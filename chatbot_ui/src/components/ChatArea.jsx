import React, { useState, useEffect, useRef } from 'react';
import { Send, Paperclip, Bot, User, FileText, X } from 'lucide-react';
import Markdown from './Markdown';

export default function ChatArea({
  activeSession,
  onSendMessage,
  onUploadFile,
  userProfile,
  isSending,
  isUploading,
  uploadProgress,
  onFirstMessage,
}) {
  const [inputText, setInputText] = useState('');
  const [streamedText, setStreamedText] = useState('');
  const lastStreamedIndexRef = useRef(-1);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const suggestions = [
    { text: 'Assign task "XYZ_123_ABC" to "dev_alpha_1"', label: 'Task Assignment' },
    { text: 'Show all tasks in my project', label: 'View Tasks' },
    { text: 'Check if there are any overdue tasks', label: 'Database Inspection' },
    { text: 'Upload a file and ask a question about it', label: 'Document Query' },
  ];

  const messages = activeSession ? activeSession.messages || [] : [];

  // Scroll to bottom whenever messages list changes or typing streams
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamedText]);

  // Handle simulated streaming/typewriter effect for the latest assistant message
  useEffect(() => {
    if (messages.length > 0) {
      const lastIdx = messages.length - 1;
      const lastMessage = messages[lastIdx];
      if (lastMessage.role === 'assistant') {
        // If this is a newly received message (index different from last streamed), trigger typing
        if (lastStreamedIndexRef.current !== lastIdx) {
          lastStreamedIndexRef.current = lastIdx;
          setStreamedText('');
          
          const fullContent = lastMessage.content || '';
          let currentLength = 0;
          
          // Stream character-slice by character-slice (3 chars at a time) for smooth, error-free typing animation
          const timer = setInterval(() => {
            if (currentLength < fullContent.length) {
              currentLength += 3;
              setStreamedText(fullContent.substring(0, currentLength));
            } else {
              setStreamedText(fullContent);
              clearInterval(timer);
            }
          }, 15);

          return () => clearInterval(timer);
        }
      }
    } else {
      lastStreamedIndexRef.current = -1;
      setStreamedText('');
    }
  }, [messages.length, messages.length > 0 ? messages[messages.length - 1].content : '']);

  const handleSend = () => {
    if (!inputText.trim() || isSending || isUploading) return;
    
    const textToSend = inputText;
    setInputText('');

    if (!activeSession) {
      // Lazy session creation flow
      onFirstMessage(textToSend);
    } else {
      onSendMessage(textToSend);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Standard backend supported types
    const validExtensions = ['.pdf', '.docx', '.txt', '.md'];
    const fileName = file.name.toLowerCase();
    const isValid = validExtensions.some(ext => fileName.endsWith(ext));

    if (!isValid) {
      alert('Only PDF, Word (.docx), Plain Text (.txt), and Markdown (.md) documents are supported.');
      e.target.value = null;
      return;
    }

    if (!activeSession) {
      // Lazy session creation with file first
      onFirstMessage(null, file);
    } else {
      onUploadFile(file);
    }
    // Reset file input value
    e.target.value = null;
  };

  const handleSuggestionClick = (text) => {
    setInputText(text);
  };

  return (
    <div className="chat-area">
      <header className="chat-header">
        <span className="header-title">
          {activeSession ? activeSession.title || 'Conversation' : 'New Chat'}
        </span>
      </header>

      {/* Message List or Welcome View */}
      {messages.length === 0 ? (
        <div className="welcome-container">
          <h1 className="welcome-title">Hello, {userProfile?.username || 'User'}</h1>
          <p className="welcome-subtitle">How can I help you manage tasks today?</p>
          
          <div className="suggestions-grid">
            {suggestions.map((s, idx) => (
              <div
                key={idx}
                className="suggestion-card"
                onClick={() => handleSuggestionClick(s.text)}
              >
                <span className="suggestion-card-text">{s.text}</span>
                <span className="suggestion-card-icon">
                  <Bot size={16} />
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="messages-container">
          {messages.map((msg, index) => {
            const isUser = msg.role === 'user';
            const isLatestAssistant = !isUser && index === messages.length - 1;
            const contentToDisplay = isLatestAssistant ? streamedText : msg.content;

            return (
              <div key={msg.id || index} className={`message-wrapper ${isUser ? 'user' : 'assistant'}`}>
                <div className={`message-avatar ${isUser ? 'user' : 'assistant'}`}>
                  {isUser ? <User size={18} /> : <Bot size={18} />}
                </div>
                <div className="message-bubble">
                  {isUser ? (
                    <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
                  ) : (
                    <Markdown content={contentToDisplay} />
                  )}
                </div>
              </div>
            );
          })}

          {/* Sending/Loader status */}
          {isSending && streamedText === '' && (
            <div className="message-wrapper assistant">
              <div className="message-avatar assistant">
                <Bot size={18} />
              </div>
              <div className="message-bubble">
                <div className="typing-indicator">
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      )}

      {/* Input container */}
      <div className="chat-input-container">
        {/* Upload status banner */}
        {isUploading && (
          <div className="upload-indicator">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <FileText size={16} style={{ color: 'var(--accent-color)' }} />
              <span>Uploading & indexing document chunks...</span>
            </div>
            <div className="progress-bar-container">
              <div className="progress-bar" />
            </div>
          </div>
        )}

        <div className="chat-input-bar">
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            accept=".pdf,.docx,.txt,.md"
            onChange={handleFileChange}
            disabled={isSending || isUploading}
          />
          <button
            className="input-icon-btn"
            onClick={() => fileInputRef.current?.click()}
            title="Upload Document (PDF, DOCX, TXT, MD)"
            disabled={isSending || isUploading}
          >
            <Paperclip size={20} />
          </button>

          <textarea
            className="chat-textarea"
            placeholder="Type a message or request task assignment..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isSending || isUploading}
            rows={1}
          />

          <button
            className="input-icon-btn send-btn"
            onClick={handleSend}
            disabled={!inputText.trim() || isSending || isUploading}
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
