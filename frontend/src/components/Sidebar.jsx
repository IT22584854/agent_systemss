import { useState, useMemo } from 'react';
import PropTypes from 'prop-types';
import { PlusCircle, MessageSquare, Trash2, Search, Pin, Archive, MoreVertical, Clock } from 'lucide-react';

export default function Sidebar({ conversations, activeId, onNewChat, onOpen, onDelete }) {
    const [searchQuery, setSearchQuery] = useState('');
    const [pinnedConvs, setPinnedConvs] = useState(new Set());
    const [archivedConvs, setArchivedConvs] = useState(new Set());
    const [menuOpen, setMenuOpen] = useState(null);

    // Filter conversations by search query and archived status
    const filteredConversations = conversations.filter(conv =>
        conv.title?.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !archivedConvs.has(conv.id)
    );

    // Group conversations by date
    const groupedConversations = useMemo(() => {
        const groups = {
            pinned: [],
            today: [],
            yesterday: [],
            last7Days: [],
            last30Days: [],
            older: []
        };

        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        const last7Days = new Date(today);
        last7Days.setDate(last7Days.getDate() - 7);
        const last30Days = new Date(today);
        last30Days.setDate(last30Days.getDate() - 30);

        filteredConversations.forEach(conv => {
            const convDate = conv.timestamp ? new Date(conv.timestamp) : new Date();

            if (pinnedConvs.has(conv.id)) {
                groups.pinned.push(conv);
            } else if (convDate >= today) {
                groups.today.push(conv);
            } else if (convDate >= yesterday) {
                groups.yesterday.push(conv);
            } else if (convDate >= last7Days) {
                groups.last7Days.push(conv);
            } else if (convDate >= last30Days) {
                groups.last30Days.push(conv);
            } else {
                groups.older.push(conv);
            }
        });

        return groups;
    }, [filteredConversations, pinnedConvs]);

    const togglePin = (convId, e) => {
        e?.stopPropagation();
        setPinnedConvs(prev => {
            const newSet = new Set(prev);
            if (newSet.has(convId)) {
                newSet.delete(convId);
            } else {
                newSet.add(convId);
            }
            return newSet;
        });
        setMenuOpen(null);
    };

    const toggleArchive = (convId, e) => {
        e?.stopPropagation();
        setArchivedConvs(prev => {
            const newSet = new Set(prev);
            if (newSet.has(convId)) {
                newSet.delete(convId);
            } else {
                newSet.add(convId);
            }
            return newSet;
        });
        setMenuOpen(null);
    };

    const formatTimestamp = (timestamp) => {
        if (!timestamp) return '';
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        
        if (minutes < 1) return 'just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };

    const handleConversationClick = (conv) => {
        onOpen(conv);
    };

    const handleNewChat = () => {
        onNewChat();
    };

    return (
        <aside className="sidebar">
            {/* Logo */}
            <div className="sidebar-logo">
                <div className="sidebar-logo-icon">🩺</div>
                <div>
                    <div className="sidebar-logo-text">MedTriage AI</div>
                </div>
            </div>

                {/* New Chat */}
                <button 
                    className="new-chat-btn" 
                    onClick={handleNewChat}
                >
                    <PlusCircle size={16} />
                    New Conversation
                </button>

                <div className="sidebar-divider" />

                {/* Search Bar */}
                {conversations.length > 0 && (
                    <div className="px-3 mb-2">
                        <div className="relative">
                            <input
                                type="text"
                                placeholder="Search conversations..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="sidebar-search-input"
                                aria-label="Search conversations"
                            />
                        </div>
                    </div>
                )}

                        {/* History with Date Groups */}
                        <div className="chat-history-list">
                            {Object.entries(groupedConversations).map(([groupKey, convs]) => {
                                if (convs.length === 0) return null;
                                
                                const groupLabels = {
                                    pinned: 'Pinned',
                                    today: 'Today',
                                    yesterday: 'Yesterday',
                                    last7Days: 'Last 7 Days',
                                    last30Days: 'Last 30 Days',
                                    older: 'Older'
                                };

                                return (
                                    <div key={groupKey} className="conversation-group">
                                        <div className="sidebar-section-label">
                                            {groupLabels[groupKey]}
                                        </div>
                                        {convs.map(conv => (
                                            <ConversationItem
                                                key={conv.id}
                                                conv={conv}
                                                isActive={conv.id === activeId}
                                                isPinned={pinnedConvs.has(conv.id)}
                                                formatTimestamp={formatTimestamp}
                                                menuOpen={menuOpen === conv.id}
                                                onOpen={() => handleConversationClick(conv)}
                                                onToggleMenu={(e) => {
                                                    e.stopPropagation();
                                                    setMenuOpen(menuOpen === conv.id ? null : conv.id);
                                                }}
                                                onPin={(e) => togglePin(conv.id, e)}
                                                onArchive={(e) => toggleArchive(conv.id, e)}
                                                onDelete={(e) => {
                                                    e.stopPropagation();
                                                    onDelete(conv.id);
                                                    setMenuOpen(null);
                                                }}
                                            />
                                        ))}
                                    </div>
                                );
                            })}

                            {filteredConversations.length === 0 && conversations.length > 0 && (
                                <div className="sidebar-empty-state">
                                    No conversations match "{searchQuery}"
                                </div>
                            )}

                            {conversations.length === 0 && (
                                <div className="sidebar-empty-state">
                                    No conversations yet.<br />Start by asking a question!
                                </div>
                            )}
                        </div>

                        <div className="sidebar-footer">
                            ⚕️ For informational purposes only.<br />
                            Always consult a qualified healthcare professional.
                        </div>
            </aside>
    );
}

// Conversation Item Component with Quick Actions
function ConversationItem({ conv, isActive, isPinned, formatTimestamp, menuOpen, onOpen, onToggleMenu, onPin, onArchive, onDelete }) {
    return (
        <div className={`history-item ${isActive ? 'active' : ''} ${isPinned ? 'pinned' : ''}`}>
            <div className="history-item-main" onClick={onOpen}>
                <div className="history-item-icon">
                    {isPinned ? (
                        <Pin size={14} style={{ flexShrink: 0 }} className="pin-icon" />
                    ) : (
                        <MessageSquare size={14} style={{ flexShrink: 0, opacity: 0.6 }} />
                    )}
                </div>
                <div className="history-item-content">
                    <span className="history-title">{conv.title || 'Untitled'}</span>
                    {conv.timestamp && (
                        <span className="history-timestamp">
                            <Clock size={10} />
                            {formatTimestamp(conv.timestamp)}
                        </span>
                    )}
                </div>
            </div>
            
            <div className="history-item-actions">
                <button
                    className="history-menu-btn"
                    onClick={onToggleMenu}
                    title="More actions"
                    aria-label="More actions"
                >
                    <MoreVertical size={14} />
                </button>

                {menuOpen && (
                    <div className="history-quick-menu">
                        <button onClick={onPin} className="menu-item">
                            <Pin size={14} />
                            {isPinned ? 'Unpin' : 'Pin'}
                        </button>
                        <button onClick={onArchive} className="menu-item">
                            <Archive size={14} />
                            Archive
                        </button>
                        <div className="menu-divider" />
                        <button onClick={onDelete} className="menu-item danger">
                            <Trash2 size={14} />
                            Delete
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

ConversationItem.propTypes = {
    conv: PropTypes.shape({
        id: PropTypes.string.isRequired,
        title: PropTypes.string,
        timestamp: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    }).isRequired,
    isActive: PropTypes.bool.isRequired,
    isPinned: PropTypes.bool.isRequired,
    formatTimestamp: PropTypes.func.isRequired,
    menuOpen: PropTypes.bool.isRequired,
    onOpen: PropTypes.func.isRequired,
    onToggleMenu: PropTypes.func.isRequired,
    onPin: PropTypes.func.isRequired,
    onArchive: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
};

Sidebar.propTypes = {
    conversations: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.string.isRequired,
        title: PropTypes.string,
    })).isRequired,
    activeId: PropTypes.string,
    onNewChat: PropTypes.func.isRequired,
    onOpen: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
};
