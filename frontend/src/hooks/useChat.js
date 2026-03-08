import { useState, useCallback, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { sendChatMessage } from '../utils/api';

const STORAGE_KEY = 'mta_conversations';

function loadConversations() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); }
    catch { return []; }
}

function saveConversations(convs) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(convs));
}

export function useChat() {
    const [conversations, setConversations] = useState(loadConversations);
    const [activeId, setActiveId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const sessionIdRef = useRef(null);

    // ── helpers ──────────────────────────────────────────────────────────────
    const persistConversations = useCallback((updated) => {
        setConversations(updated);
        saveConversations(updated);
    }, []);

    // ── start a new chat ─────────────────────────────────────────────────────
    const startNewChat = useCallback(() => {
        const id = uuidv4();
        const sessionId = uuidv4();
        sessionIdRef.current = sessionId;

        const newConv = { id, sessionId, title: 'New Conversation', createdAt: Date.now(), messages: [] };
        persistConversations([newConv, ...loadConversations()]);
        setActiveId(id);
        setMessages([]);
        setError(null);
    }, [persistConversations]);

    // ── switch to existing chat ───────────────────────────────────────────────
    const openConversation = useCallback((conv) => {
        setActiveId(conv.id);
        sessionIdRef.current = conv.sessionId;
        setMessages(conv.messages || []);
        setError(null);
    }, []);

    // ── delete a conversation ─────────────────────────────────────────────────
    const deleteConversation = useCallback((id) => {
        const updated = loadConversations().filter(c => c.id !== id);
        persistConversations(updated);
        if (id === activeId) {
            setActiveId(null);
            setMessages([]);
            sessionIdRef.current = null;
        }
    }, [activeId, persistConversations]);

    // ── send a message ────────────────────────────────────────────────────────
    const sendMessage = useCallback(async (text) => {
        if (!text.trim() || isLoading) return;

        // Ensure there's an active conversation
        let convId = activeId;
        let sessionId = sessionIdRef.current;
        const existingConvs = loadConversations();

        if (!convId) {
            convId = uuidv4();
            sessionId = uuidv4();
            sessionIdRef.current = sessionId;
            const newConv = { id: convId, sessionId, title: text.slice(0, 45), createdAt: Date.now(), messages: [] };
            persistConversations([newConv, ...existingConvs]);
            setActiveId(convId);
        }

        const userMsg = { id: uuidv4(), role: 'user', content: text, timestamp: Date.now() };
        const nextMessages = [...messages, userMsg];
        setMessages(nextMessages);
        setIsLoading(true);
        setError(null);

        // Persist user message immediately
        const updatedConvs1 = loadConversations().map(c =>
            c.id === convId ? { ...c, messages: nextMessages, title: c.title === 'New Conversation' ? text.slice(0, 45) : c.title } : c
        );
        persistConversations(updatedConvs1);

        try {
            const data = await sendChatMessage(text, sessionId);
            const aiMsg = {
                id: uuidv4(),
                role: 'assistant',
                content: data.response,
                sources: data.sources || [],
                timestamp: Date.now(),
            };
            const finalMessages = [...nextMessages, aiMsg];
            setMessages(finalMessages);

            const updatedConvs2 = loadConversations().map(c =>
                c.id === convId ? { ...c, messages: finalMessages } : c
            );
            persistConversations(updatedConvs2);
        } catch (err) {
            setError(err.message || 'Something went wrong. Please try again.');
        } finally {
            setIsLoading(false);
        }
    }, [activeId, isLoading, messages, persistConversations]);

    return {
        conversations,
        activeId,
        messages,
        isLoading,
        error,
        sendMessage,
        startNewChat,
        openConversation,
        deleteConversation,
    };
}
