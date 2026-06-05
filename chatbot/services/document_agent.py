import json
import numpy as np
import faiss
from pypdf import PdfReader
from docx import Document
from chatbot.models.attachment import Attachment
from .llm_service import generate_embeddings, generate_response


def extract_pdf_text(file_path: str) -> str:
    reader = PdfReader(file_path)
    raw_text_list = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            raw_text_list.append(text)
    return "\n".join(raw_text_list)


def extract_docx_text(file_path: str) -> str:
    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs]
    return "\n".join(paragraphs)


def extract_plain_text(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def process_attachment(attachment_id: int) -> dict:
    """Parses an uploaded attachment (PDF, DOCX, TXT, MD), extracts text, chunks it,
    generates embeddings using Gemini, and saves them in the database.
    """
    try:
        attachment = Attachment.objects.get(id=attachment_id)
    except Attachment.DoesNotExist:
        return {"error": f"Attachment with id={attachment_id} not found."}

    file_path = attachment.file.path
    file_type = attachment.file_type.lower()

    # 1. Text extraction based on file type
    try:
        if file_type == "pdf":
            full_text = extract_pdf_text(file_path)
        elif file_type == "docx":
            full_text = extract_docx_text(file_path)
        elif file_type in ["txt", "md"]:
            full_text = extract_plain_text(file_path)
        else:
            return {"error": f"Unsupported file type: {file_type}"}
    except Exception as e:
        return {"error": f"Failed to parse document: {str(e)}"}

    if not full_text.strip():
        return {"error": "Document contains no extractable text."}

    # 2. Chunking (chunks of 500 characters, 100 char overlap)
    chunk_size = 500
    overlap = 100
    chunks = []

    start = 0
    while start < len(full_text):
        end = start + chunk_size
        chunk = full_text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap

    if not chunks:
        return {"error": "No text chunks generated from document."}

    # 3. Generate embeddings
    embedded_data = []
    for idx, chunk in enumerate(chunks):
        try:
            embedding = generate_embeddings(chunk)
            embedded_data.append(
                {"id": idx, "text": chunk, "embedding": embedding}
            )
        except Exception:
            # Skip failed chunks and continue
            continue

    if not embedded_data:
        return {"error": "Failed to generate embeddings for any document chunks."}

    # 4. Save JSON serialized data back to database
    attachment.parsed_text = json.dumps(embedded_data)
    attachment.save()

    return {"success": True, "num_chunks": len(embedded_data)}


def run_document_agent(prompt: str, session_id: str) -> str:
    """Executes a RAG query over all parsed text attachments associated with a ChatSession,
    using an in-memory FAISS flat index.
    """
    # Fetch all attachments for this session
    attachments = Attachment.objects.filter(session_id=session_id).exclude(
        parsed_text=""
    )
    if not attachments.exists():
        return "Error: No indexed documents found for this session."

    all_chunks = []
    for att in attachments:
        try:
            chunks = json.loads(att.parsed_text)
            all_chunks.extend(chunks)
        except Exception:
            continue

    if not all_chunks:
        return "Error: Could not retrieve indexed document context."

    # 1. Build FAISS index in memory
    try:
        embeddings = np.array(
            [item["embedding"] for item in all_chunks], dtype=np.float32
        )
        dimension = embeddings.shape[1]

        index = faiss.IndexFlatIP(dimension)  # Inner Product flat index for Cosine Similarity
        faiss.normalize_L2(embeddings)
        index.add(embeddings)
    except Exception as e:
        return f"Error building vector index: {str(e)}"

    # 2. Get Query Embedding
    try:
        query_vector = np.array([generate_embeddings(prompt)], dtype=np.float32)
        faiss.normalize_L2(query_vector)
    except Exception as e:
        return f"Error generating query embedding: {str(e)}"

    # 3. Search FAISS index
    k = min(5, len(all_chunks))
    D, I = index.search(query_vector, k)

    # 4. Format context
    context_chunks = []
    for idx in I[0]:
        if idx != -1 and idx < len(all_chunks):
            context_chunks.append(all_chunks[idx]["text"])

    context = "\n---\n".join(context_chunks)

    # 5. Call LLM with RAG Prompt
    rag_prompt = (
        "You are an assistant answering questions based ONLY on the provided document contexts. "
        "If the answer cannot be found in the context, politely state that you do not know. "
        "Do not make up facts outside the provided documents.\n\n"
        f"DOCUMENT CONTEXT:\n{context}\n\n"
        f"USER QUESTION: {prompt}\n\n"
        "ANSWER:"
    )

    return generate_response(rag_prompt)
