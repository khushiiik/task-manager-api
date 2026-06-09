import React, { useState, useEffect } from 'react';
import Login from './components/Login';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';

export default function App() {
  const [accessToken, setAccessToken] = useState(localStorage.getItem('accessToken'));
  const [userProfile, setUserProfile] = useState(null);
  const [loadingProfile, setLoadingProfile] = useState(!!accessToken);
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [activeSession, setActiveSession] = useState(null);
  const [isSending, setIsSending] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  
  // Theme state: defaults to dark-theme for modern premium feel
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark');

  // Load user profile on login or mount
  const fetchUserProfile = async (token) => {
    try {
      const response = await fetch('/api/users/profile/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        // Access token might be expired, attempt refresh
        const refreshedToken = await handleTokenRefresh();
        if (refreshedToken) {
          return fetchUserProfile(refreshedToken);
        } else {
          throw new Error('Unauthorized');
        }
      }

      if (!response.ok) {
        throw new Error('Failed to retrieve profile');
      }

      const data = await response.json();
      setUserProfile(data);
      setAccessToken(token);
      return data;
    } catch (err) {
      handleLogout();
    } finally {
      setLoadingProfile(false);
    }
  };

  // JWT Token refresh helper
  const handleTokenRefresh = async () => {
    const refresh = localStorage.getItem('refreshToken');
    if (!refresh) return null;

    try {
      const response = await fetch('/api/users/token/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh }),
      });

      if (!response.ok) throw new Error('Refresh token invalid');

      const data = await response.json();
      localStorage.setItem('accessToken', data.access);
      setAccessToken(data.access);
      return data.access;
    } catch (err) {
      handleLogout();
      return null;
    }
  };

  // Custom authenticated fetch wrapper that handles token refreshing automatically
  const authFetch = async (url, options = {}) => {
    let token = localStorage.getItem('accessToken');
    if (!token) return null;

    if (!options.headers) options.headers = {};
    options.headers['Authorization'] = `Bearer ${token}`;

    let response = await fetch(url, options);

    if (response.status === 401) {
      const newToken = await handleTokenRefresh();
      if (newToken) {
        options.headers['Authorization'] = `Bearer ${newToken}`;
        response = await fetch(url, options);
      }
    }
    return response;
  };

  // Fetch all sessions
  const fetchSessions = async () => {
    try {
      const res = await authFetch('/api/chatbot/sessions/');
      if (res && res.ok) {
        const data = await res.json();
        // Since get_queryset orders by -created_at, sessions will be correctly ordered
        setSessions(data.results || data);
      }
    } catch (err) {
      console.error('Error fetching sessions:', err);
    }
  };

  // Fetch active session messages
  const fetchSessionDetails = async (sessionId) => {
    if (!sessionId) return;
    try {
      const res = await authFetch(`/api/chatbot/sessions/${sessionId}/`);
      if (res && res.ok) {
        const data = await res.json();
        setActiveSession(data);
      }
    } catch (err) {
      console.error('Error fetching session details:', err);
    }
  };

  useEffect(() => {
    if (accessToken) {
      fetchUserProfile(accessToken).then((profile) => {
        if (profile) {
          fetchSessions();
        }
      });
    }
  }, [accessToken]);

  // Load details when active session changes
  useEffect(() => {
    if (activeSessionId) {
      fetchSessionDetails(activeSessionId);
    } else {
      setActiveSession(null);
    }
  }, [activeSessionId]);

  const handleLoginSuccess = async (token) => {
    setLoadingProfile(true);
    await fetchUserProfile(token);
  };

  const handleLogout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    setAccessToken(null);
    setUserProfile(null);
    setSessions([]);
    setActiveSessionId(null);
    setActiveSession(null);
  };

  // Theme Toggler
  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    localStorage.setItem('theme', nextTheme);
  };

  // Send message API trigger
  const handleSendMessage = async (text) => {
    if (!activeSessionId) return;
    setIsSending(true);

    // Optimistically update message screen
    const tempUserMessage = { role: 'user', content: text };
    setActiveSession((prev) => ({
      ...prev,
      messages: [...(prev.messages || []), tempUserMessage],
    }));

    try {
      const res = await authFetch(`/api/chatbot/sessions/${activeSessionId}/message/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content: text }),
      });

      if (res && res.ok) {
        const updatedSession = await res.json();
        setActiveSession(updatedSession);
        
        // Refresh sidebar title list
        fetchSessions();
      } else {
        throw new Error('Failed to send message');
      }
    } catch (err) {
      alert(err.message);
    } finally {
      setIsSending(false);
    }
  };

  // Delete session trigger
  const handleDeleteSession = async (sessionId) => {
    if (!window.confirm("Are you sure you want to delete this chat session?")) return;

    try {
      const res = await authFetch(`/api/chatbot/sessions/${sessionId}/`, {
        method: 'DELETE',
      });

      if (res && res.ok) {
        // Remove from local list state
        setSessions((prev) => prev.filter((s) => s.id !== sessionId));
        if (activeSessionId === sessionId) {
          setActiveSessionId(null);
          setActiveSession(null);
        }
      } else {
        throw new Error('Failed to delete chat session.');
      }
    } catch (err) {
      alert(err.message);
    }
  };

  // Upload attachment file trigger
  const handleUploadFile = async (file, sessionId = activeSessionId) => {
    if (!sessionId) return;
    setIsUploading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await authFetch(`/api/chatbot/sessions/${sessionId}/attachments/`, {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (res && res.ok) {
        // Document uploaded, fetch updated message history
        fetchSessionDetails(sessionId);
        alert(data.message || 'File uploaded and indexed successfully.');
      } else {
        throw new Error(data.error || 'Failed to process document.');
      }
    } catch (err) {
      alert(err.message);
    } finally {
      setIsUploading(false);
    }
  };

  // Lazy creation flow: Creates session and then sends first message or document
  const handleFirstMessage = async (text, file = null) => {
    setIsSending(true);

    try {
      const res = await authFetch('/api/chatbot/sessions/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        // Request uses standard body (if any serialization is needed, standard POST works)
        body: JSON.stringify({}),
      });

      if (!res || !res.ok) {
        throw new Error('Failed to initialize chat session.');
      }

      const newSession = await res.json();
      setActiveSessionId(newSession.id);
      
      // Update sidebar session list immediately
      setSessions((prev) => [newSession, ...prev]);

      if (file) {
        await handleUploadFile(file, newSession.id);
      } else if (text) {
        // Once the session is created, trigger standard message posting
        // Use timeout or custom function to trigger standard message on the new session
        const messageRes = await authFetch(`/api/chatbot/sessions/${newSession.id}/message/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ content: text }),
        });

        if (messageRes && messageRes.ok) {
          const updatedSession = await messageRes.json();
          setActiveSession(updatedSession);
          fetchSessions();
        } else {
          throw new Error('Failed to deliver message.');
        }
      }
    } catch (err) {
      alert(err.message);
    } finally {
      setIsSending(false);
    }
  };

  if (loadingProfile) {
    return (
      <div className={`login-container ${theme}-theme`} style={{ background: 'var(--bg-primary)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
          <div className="progress-bar-container" style={{ width: 200, height: 8 }}>
            <div className="progress-bar" />
          </div>
          <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>Authenticating session...</span>
        </div>
      </div>
    );
  }

  if (!userProfile) {
    return <Login onLoginSuccess={handleLoginSuccess} theme={theme} />;
  }

  return (
    <div className={`app-container ${theme}-theme`}>
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSessionSelect={setActiveSessionId}
        onNewChatClick={() => setActiveSessionId(null)}
        onDeleteSession={handleDeleteSession}
        userProfile={userProfile}
        onLogout={handleLogout}
        theme={theme}
        toggleTheme={toggleTheme}
      />
      <ChatArea
        activeSession={activeSession}
        onSendMessage={handleSendMessage}
        onUploadFile={handleUploadFile}
        userProfile={userProfile}
        isSending={isSending}
        isUploading={isUploading}
        onFirstMessage={handleFirstMessage}
      />
    </div>
  );
}
