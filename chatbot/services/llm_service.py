import google.generativeai as genai
from django.conf import settings
from groq import Groq
import json
import inspect

genai.configure(api_key=settings.GEMINI_API_KEY)

# Initialize Groq client safely
client = None
if getattr(settings, "GROQ_API_KEY", None):
    client = Groq(api_key=settings.GROQ_API_KEY)


def function_to_schema(func):
    # Retrieve arguments and docstring
    sig = inspect.signature(func)
    doc = func.__doc__ or ""
    
    # Simple docstring description parser
    description = doc.strip().split("\n")[0]
    
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    for name, param in sig.parameters.items():
        # Map python types to JSON schema types
        ptype = param.annotation
        type_str = str(ptype).lower()
        js_type = "string"
        if "int" in type_str:
            js_type = "integer"
        elif "bool" in type_str:
            js_type = "boolean"
        elif "float" in type_str or "number" in type_str:
            js_type = "number"
            
        parameters["properties"][name] = {
            "type": js_type,
            "description": f"The {name} parameter."
        }
        
        if param.default == inspect.Parameter.empty:
            parameters["required"].append(name)
            
    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": description,
            "parameters": parameters
        }
    }


def generate_response(prompt: str, system_instruction: str = None, history: list = None) -> str:
    if not client:
        return "Error: GROQ_API_KEY is not configured in settings/environment."

    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
        
    if history:
        for turn in history:
            role = "assistant" if turn["role"] in ["model", "assistant"] else "user"
            messages.append({"role": role, "content": turn["parts"][0]})
            
    messages.append({"role": "user", "content": prompt})
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.0,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        return f"Error executing Groq API: {str(e)}"


def generate_embeddings(text: str) -> list[float]:
    result = genai.embed_content(
        model="models/gemini-embedding-001", content=text, task_type="retrieval_document"
    )
    return result["embedding"]


def chat_with_tools(prompt: str, tools: list, system_instruction: str = None, history: list = None) -> str:
    if not client:
        return "Error: GROQ_API_KEY is not configured in settings/environment."

    # 1. Format messages list starting with system_instruction
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
        
    # 2. Append history
    if history:
        for turn in history:
            role = "assistant" if turn["role"] in ["model", "assistant"] else "user"
            messages.append({"role": role, "content": turn["parts"][0]})
            
    # 3. Append the current prompt
    messages.append({"role": "user", "content": prompt})
    
    # 4. Convert python functions to Groq tool schemas
    groq_tools = [function_to_schema(t) for t in tools]
    
    # Create mapping of function name to function reference
    tool_map = {t.__name__: t for t in tools}
    
    max_iterations = 5
    for _ in range(max_iterations):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=groq_tools,
                tool_choice="auto",
                temperature=0.0,
            )
        except Exception as e:
            return f"Error executing Groq API completion: {str(e)}"
            
        message = response.choices[0].message
        
        # Build message dictionary to append back
        msg_dict = {"role": "assistant"}
        if message.content:
            msg_dict["content"] = message.content
        if message.tool_calls:
            msg_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]
        messages.append(msg_dict)
        
        if not message.tool_calls:
            return message.content or ""
            
        # Execute each tool call
        for tc in message.tool_calls:
            func_name = tc.function.name
            func_args = json.loads(tc.function.arguments)
            func_ref = tool_map.get(func_name)
            
            if func_ref:
                try:
                    sig = inspect.signature(func_ref)
                    coerced_args = {}
                    for param_name, param_val in sig.parameters.items():
                        if param_name in func_args:
                            val = func_args[param_name]
                            if val is not None:
                                type_str = str(param_val.annotation).lower()
                                if "int" in type_str:
                                    val = int(float(val))
                                elif "float" in type_str or "number" in type_str:
                                    val = float(val)
                                elif "bool" in type_str:
                                    val = bool(val)
                            coerced_args[param_name] = val
                    
                    result = func_ref(**coerced_args)
                except Exception as e:
                    result = {"error": f"Exception executing tool: {str(e)}"}
            else:
                result = {"error": f"Tool '{func_name}' not found."}
                
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "name": func_name,
                "content": json.dumps(result)
            })
            
    return messages[-1].get("content") or "Error: Max tool call iterations reached."
