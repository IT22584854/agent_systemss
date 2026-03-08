import { Keyboard } from 'lucide-react';

/**
 * Keyboard shortcuts reference component
 */
export function KeyboardShortcuts() {
  const shortcuts = [
    {
      category: 'General',
      items: [
        { keys: ['Ctrl', 'N'], description: 'Start new conversation' },
        { keys: ['Ctrl', ','], description: 'Open settings' },
        { keys: ['Esc'], description: 'Close modal/dialog' },
      ],
    },
    {
      category: 'Chat',
      items: [
        { keys: ['Enter'], description: 'Send message' },
        { keys: ['Shift', 'Enter'], description: 'New line in message' },
        { keys: ['Ctrl', 'C'], description: 'Copy selected message' },
      ],
    },
    {
      category: 'Editing',
      items: [
        { keys: ['Ctrl', 'Enter'], description: 'Save edited message' },
        { keys: ['Esc'], description: 'Cancel editing' },
      ],
    },
    {
      category: 'Navigation',
      items: [
        { keys: ['Tab'], description: 'Move focus forward' },
        { keys: ['Shift', 'Tab'], description: 'Move focus backward' },
      ],
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-gray-900 dark:text-gray-100">
        <Keyboard className="w-5 h-5" />
        <h3 className="text-lg font-semibold">Keyboard Shortcuts</h3>
      </div>

      {shortcuts.map((section) => (
        <div key={section.category}>
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
            {section.category}
          </h4>
          <div className="space-y-2">
            {section.items.map((shortcut, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between py-2 px-3 rounded-lg bg-gray-50 dark:bg-gray-800/50"
              >
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {shortcut.description}
                </span>
                <div className="flex items-center gap-1">
                  {shortcut.keys.map((key, keyIdx) => (
                    <span key={keyIdx} className="inline-flex">
                      <kbd className="px-2 py-1 text-xs font-semibold text-gray-800 dark:text-gray-200 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded shadow-sm">
                        {key}
                      </kbd>
                      {keyIdx < shortcut.keys.length - 1 && (
                        <span className="mx-1 text-gray-400">+</span>
                      )}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      <div className="text-xs text-gray-500 dark:text-gray-500 pt-4 border-t border-gray-200 dark:border-gray-700">
        <p>💡 Tip: Some shortcuts may vary by browser or operating system.</p>
      </div>
    </div>
  );
}
