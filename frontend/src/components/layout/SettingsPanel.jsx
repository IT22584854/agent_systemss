import { Sun, Moon, Monitor, Download, Trash2, Keyboard } from 'lucide-react';
import { useState } from 'react';
import { useTheme, THEME_MODES } from '../../contexts/ThemeContext';
import { useChat } from '../../contexts/ChatContext';
import { useToast } from '../shared/Toast';
import { Button } from '../shared/Button';
import { Modal } from '../shared/Modal';
import { KeyboardShortcuts } from '../shared/KeyboardShortcuts';

/**
 * Settings panel component
 */
export function SettingsPanel({ isOpen, onClose }) {
  const { themeMode, setTheme, actualTheme } = useTheme();
  const { activeConversation, exportConversationJSON, exportConversationMarkdown, deleteConversation } = useChat();
  const { success, error: showError } = useToast();
  const [showShortcuts, setShowShortcuts] = useState(false);

  const themeOptions = [
    { value: THEME_MODES.LIGHT, label: 'Light', icon: Sun },
    { value: THEME_MODES.DARK, label: 'Dark', icon: Moon },
    { value: THEME_MODES.SYSTEM, label: 'System', icon: Monitor },
  ];

  const handleExportJSON = () => {
    const data = exportConversationJSON();
    if (!data) {
      showError('No active conversation to export');
      return;
    }

    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-${activeConversation.id}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    success('Conversation exported as JSON');
  };

  const handleExportMarkdown = () => {
    const data = exportConversationMarkdown();
    if (!data) {
      showError('No active conversation to export');
      return;
    }

    const blob = new Blob([data], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-${activeConversation.id}-${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
    success('Conversation exported as Markdown');
  };

  const handleClearHistory = () => {
    if (window.confirm('Are you sure you want to clear all conversation history? This cannot be undone.')) {
      // Get all conversation IDs
      const allConversations = JSON.parse(localStorage.getItem('mta_conversations') || '[]');
      allConversations.forEach(conv => {
        deleteConversation(conv.id);
      });
      success('All conversations cleared');
      onClose();
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Settings"
      size="md"
    >
      <div className="space-y-6">
        {/* Theme Settings */}
        <div>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
            Appearance
          </h3>
          <div className="grid grid-cols-3 gap-2">
            {themeOptions.map(({ value, label, icon: Icon }) => (
              <button
                key={value}
                onClick={() => setTheme(value)}
                className={`
                  flex flex-col items-center gap-2 p-3 rounded-lg border-2 transition-all
                  ${themeMode === value
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }
                `}
                aria-label={`Set theme to ${label}`}
              >
                <Icon className={`w-5 h-5 ${themeMode === value ? 'text-primary-600 dark:text-primary-400' : 'text-gray-600 dark:text-gray-400'}`} />
                <span className={`text-xs font-medium ${themeMode === value ? 'text-primary-700 dark:text-primary-300' : 'text-gray-700 dark:text-gray-300'}`}>
                  {label}
                </span>
              </button>
            ))}
          </div>
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            Current: {actualTheme === THEME_MODES.DARK ? 'Dark' : 'Light'}
            {themeMode === THEME_MODES.SYSTEM && ' (auto)'}
          </p>
        </div>

        {/* Export Options */}
        <div>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
            Export Current Conversation
          </h3>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              icon={Download}
              onClick={handleExportJSON}
              disabled={!activeConversation}
              className="flex-1"
            >
              JSON
            </Button>
            <Button
              variant="secondary"
              size="sm"
              icon={Download}
              onClick={handleExportMarkdown}
              disabled={!activeConversation}
              className="flex-1"
            >
              Markdown
            </Button>
          </div>
          {!activeConversation && (
            <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              Start a conversation to enable export
            </p>
          )}
        </div>

        {/* Data Management */}
        <div>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">
            Data Management
          </h3>
          <Button
            variant="danger"
            size="sm"
            icon={Trash2}
            onClick={handleClearHistory}
            className="w-full"
          >
            Clear All Conversations
          </Button>
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            This will permanently delete all your conversation history
          </p>
        </div>

        {/* App Info */}
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              About
            </h3>
            <button
              onClick={() => setShowShortcuts(true)}
              className="text-xs text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 flex items-center gap-1"
            >
              <Keyboard className="w-3 h-3" />
              Shortcuts
            </button>
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
            <p className="font-semibold text-gray-700 dark:text-gray-300">Medical Triage Assistant</p>
            <p>Version 2.0.0</p>
            <p>Built with React + Vite</p>
          </div>
        </div>
      </div>

      {/* Keyboard Shortcuts Modal */}
      <Modal
        isOpen={showShortcuts}
        onClose={() => setShowShortcuts(false)}
        title="Keyboard Shortcuts"
        size="md"
      >
        <KeyboardShortcuts />
      </Modal>
    </Modal>
  );
}
