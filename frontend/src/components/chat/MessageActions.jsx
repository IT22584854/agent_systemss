import { useState } from 'react';
import { Copy, Edit2, RefreshCw, Check } from 'lucide-react';
import { useChat } from '../../contexts/ChatContext';
import { useToast } from '../shared/Toast';

/**
 * Message action buttons component (copy, edit, regenerate)
 */
export function MessageActions({ message, isLastAssistantMessage }) {
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(message.content);
  const { copyMessage, editMessage, regenerateResponse, isLoading } = useChat();
  const { success, error: showError } = useToast();

  const handleCopy = async () => {
    const result = await copyMessage(message.id);
    if (result) {
      setCopied(true);
      success('Copied to clipboard');
      setTimeout(() => setCopied(false), 2000);
    } else {
      showError('Failed to copy message');
    }
  };

  const handleEdit = () => {
    setIsEditing(true);
    setEditContent(message.content);
  };

  const handleSaveEdit = async () => {
    if (editContent.trim() && editContent !== message.content) {
      await editMessage(message.id, editContent);
      setIsEditing(false);
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditContent(message.content);
  };

  const handleRegenerate = async () => {
    await regenerateResponse();
  };

  if (isEditing) {
    return (
      <div className="mt-2 space-y-2">
        <textarea
          value={editContent}
          onChange={(e) => setEditContent(e.target.value)}
          className="w-full min-h-[100px] px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
          autoFocus
          onKeyDown={(e) => {
            if (e.key === 'Escape') handleCancelEdit();
            if (e.key === 'Enter' && e.ctrlKey) handleSaveEdit();
          }}
        />
        <div className="flex items-center gap-2">
          <button
            onClick={handleSaveEdit}
            disabled={!editContent.trim() || editContent === message.content}
            className="px-3 py-1.5 text-xs font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Save (Ctrl+Enter)
          </button>
          <button
            onClick={handleCancelEdit}
            className="px-3 py-1.5 text-xs font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600"
          >
            Cancel (Esc)
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
      {/* Copy button */}
      <button
        onClick={handleCopy}
        className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        title="Copy message"
        aria-label="Copy message to clipboard"
      >
        {copied ? (
          <Check className="w-4 h-4 text-medical-600 dark:text-medical-400" />
        ) : (
          <Copy className="w-4 h-4 text-gray-500 dark:text-gray-400" />
        )}
      </button>

      {/* Edit button (only for user messages) */}
      {message.role === 'user' && (
        <button
          onClick={handleEdit}
          disabled={isLoading}
          className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Edit message"
          aria-label="Edit and resend message"
        >
          <Edit2 className="w-4 h-4 text-gray-500 dark:text-gray-400" />
        </button>
      )}

      {/* Regenerate button (only for last assistant message) */}
      {message.role === 'assistant' && isLastAssistantMessage && (
        <button
          onClick={handleRegenerate}
          disabled={isLoading}
          className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Regenerate response"
          aria-label="Regenerate assistant response"
        >
          <RefreshCw className={`w-4 h-4 text-gray-500 dark:text-gray-400 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      )}

      {/* Edited indicator */}
      {message.edited && (
        <span className="ml-2 text-xs text-gray-400 dark:text-gray-500 italic">
          (edited)
        </span>
      )}

      {/* Regenerated indicator */}
      {message.regenerated && (
        <span className="ml-2 text-xs text-gray-400 dark:text-gray-500 italic">
          (regenerated)
        </span>
      )}
    </div>
  );
}
