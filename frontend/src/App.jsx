import { useState, useEffect } from 'react';
import { Settings } from 'lucide-react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import { SettingsPanel } from './components/layout/SettingsPanel';
import { useChat } from './contexts/ChatContext';
import { useTheme } from './contexts/ThemeContext';

export default function App() {
  const [showSettings, setShowSettings] = useState(false);
  const {
    conversations,
    activeId,
    messages,
    isLoading,
    error,
    sendMessage,
    startNewChat,
    openConversation,
    deleteConversation,
  } = useChat();
  const { isDark } = useTheme();

  // Global keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl+N or Cmd+N: New conversation
      if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        startNewChat();
      }
      
      // Ctrl+, or Cmd+,: Open settings
      if ((e.ctrlKey || e.metaKey) && e.key === ',') {
        e.preventDefault();
        setShowSettings(true);
      }
      
      // Escape: Close settings
      if (e.key === 'Escape' && showSettings) {
        setShowSettings(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showSettings, startNewChat]);

  return (
    <div className="app-layout relative">
      {/* Screen reader announcements for new messages */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {messages.length > 0 && messages[messages.length - 1]?.role === 'assistant' && (
          `New message from assistant`
        )}
      </div>

      {/* Sidebar */}
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onNewChat={startNewChat}
        onOpen={openConversation}
        onDelete={deleteConversation}
      />

      {/* Main Chat Area */}
      <main className="chat-area" role="main">
        {/* Top Bar */}
        <header className="chat-topbar">
          {/* Mobile: Add padding to account for hamburger button */}
          <div className="lg:hidden w-12" aria-hidden="true" />
          
          <div className="topbar-favicon" aria-hidden="true">🩺</div>
          <h1 className="topbar-title">Medical Triage Assistant</h1>
          <div className="flex items-center gap-2">
            <div className="topbar-pill" role="status">
              <span className="topbar-pill-dot" aria-hidden="true" />
              AI-Powered
            </div>
            <button
              onClick={() => setShowSettings(true)}
              className="p-2.5 rounded-xl hover:bg-white/10 dark:hover:bg-white/5 transition-all duration-300 hover:scale-105 active:scale-95"
              title="Settings (Ctrl+,)"
              aria-label="Open settings"
              style={{
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255, 255, 255, 0.1)'
              }}
            >
              <Settings className="w-5 h-5" style={{ color: 'var(--text-secondary)' }} />
            </button>
          </div>
        </header>

        {/* Messages */}
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          error={error}
          onSuggestion={sendMessage}
        />

        {/* Input */}
        <ChatInput onSend={sendMessage} disabled={isLoading} />
      </main>

      {/* Settings Panel */}
      <SettingsPanel isOpen={showSettings} onClose={() => setShowSettings(false)} />
    </div>
  );
}
