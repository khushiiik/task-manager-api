import React from 'react';
import { Plus, MessageSquare, LogOut, Sun, Moon, Sparkles, Trash2 } from 'lucide-react';

export default function Sidebar({
  sessions,
  activeSessionId,
  onSessionSelect,
  onNewChatClick,
  onDeleteSession,
  userProfile,
  onLogout,
  theme,
  toggleTheme,
}) {
  return (
    <aside className="sidebar">
      <div className="sidebar-top">
        <button className="new-chat-btn" onClick={onNewChatClick}>
          <Plus size={20} />
          <span>New Chat</span>
        </button>
        
        <div className="sidebar-title">Recent Chats</div>
      </div>

      <div className="conversations-list">
        {sessions.length === 0 ? (
          <div style={{ padding: '12px 16px', fontSize: '13px', color: 'var(--text-secondary)' }}>
            No recent conversations
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              className={`conversation-item ${activeSessionId === session.id ? 'active' : ''}`}
              onClick={() => onSessionSelect(session.id)}
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, overflow: 'hidden', flex: 1 }}>
                <MessageSquare size={16} style={{ color: 'var(--text-secondary)', flexShrink: 0 }} />
                <span className="conversation-title">
                  {session.title || 'Untitled Conversation'}
                </span>
              </div>
              <button
                className="delete-session-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteSession(session.id);
                }}
                title="Delete Chat"
                style={{
                  background: 'none',
                  border: 'none',
                  padding: 4,
                  borderRadius: 4,
                  cursor: 'pointer',
                  color: 'var(--text-secondary)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'all 0.2s ease',
                }}
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))
        )}
      </div>

      <div className="sidebar-bottom">
        <button className="sidebar-action-item" onClick={toggleTheme}>
          {theme === 'dark' ? (
            <>
              <Sun size={18} />
              <span>Light Mode</span>
            </>
          ) : (
            <>
              <Moon size={18} />
              <span>Dark Mode</span>
            </>
          )}
        </button>

        <button className="sidebar-action-item" onClick={onLogout}>
          <LogOut size={18} />
          <span>Sign Out</span>
        </button>

        {userProfile && (
          <div className="profile-card">
            <div className="profile-avatar">
              {userProfile.username ? userProfile.username[0].toUpperCase() : 'U'}
            </div>
            <div className="profile-details">
              <span className="profile-name">{userProfile.username}</span>
              <span className="profile-role">
                {userProfile.role || 'Member'} {userProfile.team ? `• ${userProfile.team.name}` : ''}
              </span>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
