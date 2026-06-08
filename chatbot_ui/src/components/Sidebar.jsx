import React from 'react';
import { Plus, MessageSquare, LogOut, Sun, Moon, Sparkles } from 'lucide-react';

export default function Sidebar({
  sessions,
  activeSessionId,
  onSessionSelect,
  onNewChatClick,
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
            >
              <MessageSquare size={16} style={{ color: 'var(--text-secondary)', flexShrink: 0 }} />
              <span className="conversation-title">
                {session.title || 'Untitled Conversation'}
              </span>
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
