import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import { Message, Chat, HealthResponse } from './types';
import { useLocalStorage } from './hooks/useLocalStorage';
import { reviveChats, mapBackendMessage } from './utils/dates';
import {
  API_BASE,
  postChat,
  streamChat,
  listConversations,
  getConversation,
  getHealth,
} from './services/api';
import './index.css';

const WELCOME_ID = 'welcome-id';

const WELCOME_MESSAGE: Message = {
  id: WELCOME_ID,
  content:
    '🌾 Habari! Mimi ni Imarika, mshauri wako wa kilimo wa mazao ya Afrika Mashariki. Ninaweza kukusaidia na maswali kuhusu mahindi, maharage, mihogo, ulezi, mtama, na viazi vitamu. Uliza swali lolote!',
  sender: 'bot',
  timestamp: new Date(),
};

/** Identifiant genere cote client : il devient l'id de conversation SQLite. */
const createChatId = () =>
  `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [chats, setChats] = useLocalStorage<Chat[]>('imarika-chats', [], reviveChats);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const busyRef = useRef(false);

  // Message d'accueil quand aucun message n'est affiche
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([WELCOME_MESSAGE]);
    }
  }, [messages.length]);

  // Sante du systeme : immediatement puis toutes les 30 s (n'empeche pas l'UI)
  useEffect(() => {
    let alive = true;
    const check = async () => {
      try {
        const result = await getHealth();
        if (alive) setHealth(result);
      } catch {
        if (alive) setHealth(null);
      }
    };
    check();
    const timer = window.setInterval(check, 30000);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, []);

  // SQLite -> Sidebar via l'API history ; repli localStorage si le backend est absent
  const refreshHistory = useCallback(async () => {
    try {
      const conversations = await listConversations();
      setChats((prev) => {
        const localById = new Map(prev.map((c) => [c.id, c]));
        const apiIds = new Set(conversations.map((c) => c.id));
        const fromApi: Chat[] = conversations.map((c) => {
          const local = localById.get(c.id);
          return {
            id: c.id,
            title: c.title || (local ? local.title : 'Conversation'),
            createdAt: local ? local.createdAt : new Date(c.created_at),
            messages: local ? local.messages : [],
          };
        });
        const offlineOnly = prev.filter((c) => !apiIds.has(c.id));
        return [...fromApi, ...offlineOnly];
      });
    } catch {
      // Backend injoignable : on conserve les conversations locales
    }
  }, [setChats]);

  useEffect(() => {
    refreshHistory();
  }, [refreshHistory]);

  /** Envoi d'un message : streaming SSE avec repli sur l'API classique. */
  const sendMessage = async (content: string) => {
    if (busyRef.current || !content.trim()) return;
    busyRef.current = true;

    const chatId = currentChatId || createChatId();
    if (!currentChatId) {
      setCurrentChatId(chatId);
      const newChat: Chat = {
        id: chatId,
        title: content.slice(0, 40),
        messages: [],
        createdAt: new Date(),
      };
      setChats((prev) => [newChat, ...prev]);
    }

    // Préfixer le message avec la ville météo sélectionnée si la météo est demandée sans ville
    const storedCity = getStoredWeatherCity();
    const weatherQueryPatterns = /^\s*(météo|meteo|weather|temps)\s*$/i;
    let enhancedContent = content;
    if (weatherQueryPatterns.test(content.trim()) && storedCity) {
      enhancedContent = `${storedCity} ${content}`;
      console.log('Weather city selector: enhancing message with stored city:', storedCity, content);
    }

    const baseMessages = messages.filter((m) => m.id !== WELCOME_ID);
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      content,
      sender: 'user',
      timestamp: new Date(),
    };
    const assistantId = `bot-${Date.now()}`;
    const assistantMessage: Message = {
      id: assistantId,
      content: '',
      sender: 'bot',
      timestamp: new Date(),
    };

    setMessages([...baseMessages, userMessage, assistantMessage]);
    setIsTyping(true); // visible jusqu'au premier token
    setIsStreaming(true);

    let answer = '';
    const render = (text: string) =>
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? { ...m, content: text } : m)),
      );

    try {
      const tokens = await streamChat(
        { message: enhancedContent, conversation_id: chatId },
        {
          onStart: (id) => {
            if (id) setCurrentChatId(id);
          },
          onToken: (token) => {
            answer += token;
            setIsTyping(false); // le indicateur cede la place au message en cours
            render(answer);
          },
          onError: (message) => {
            answer = `${answer ? `${answer}\n\n` : ''}[Erreur] ${message}`;
            render(answer);
          },
          onDone: () => {
            /* la reponse complete est deja dans `answer` */
          },
        },
      );

      // Flux vide (reponse non generee) : repli sur l'API non-streaming
      if (tokens === 0 && !answer) {
        const result = await postChat({ message: enhancedContent, conversation_id: chatId });
        answer = result.response;
        if (result.conversation_id) setCurrentChatId(result.conversation_id);
        render(answer);
      }
    } catch (error) {
      if (!answer) {
        try {
          const result = await postChat({ message: enhancedContent, conversation_id: chatId });
          answer = result.response;
          if (result.conversation_id) setCurrentChatId(result.conversation_id);
        } catch (fallbackError) {
          answer =
            `⚠️ Impossible de joindre le serveur FastAPI sur ${API_BASE}.\n` +
            'Vérifiez que le backend est démarré (python -m uvicorn backend.main:app --port 8000).';
        }
      }
      render(answer);
    } finally {
      setIsTyping(false);
      setIsStreaming(false);
      busyRef.current = false;

      const finalMessages: Message[] = [
        ...baseMessages,
        userMessage,
        { ...assistantMessage, content: answer },
      ];
      setMessages(finalMessages);

      setChats((prev) => {
        const exists = prev.some((c) => c.id === chatId);
        if (!exists) {
          return [
            {
              id: chatId,
              title: content.slice(0, 40),
              createdAt: new Date(),
              messages: finalMessages,
            },
            ...prev,
          ];
        }
        return prev.map((c) =>
          c.id === chatId
            ? { ...c, title: c.title || content.slice(0, 40), messages: finalMessages }
            : c,
        );
      });

      refreshHistory();
    }
  };

  /** Selection d'une conversation : SQLite (API history) en priorite. */
  const selectChat = async (chatId: string) => {
    setCurrentChatId(chatId);
    setSidebarOpen(false);

    const local = chats.find((c) => c.id === chatId);
    setMessages(local ? local.messages : []);

    try {
      const detail = await getConversation(chatId);
      if (detail && detail.messages && detail.messages.length > 0) {
        setMessages(detail.messages.map(mapBackendMessage));
      }
    } catch {
      // Backend absent : on garde les messages locaux
    }
  };

  const startNewChat = () => {
    setCurrentChatId(null);
    setMessages([]);
    setSidebarOpen(false);
  };

  // Récupérer la ville météo sélectionnée depuis localStorage
  const getStoredWeatherCity = () => {
    try {
      const stored = localStorage.getItem('selected_weather_city');
      return stored || null;
    } catch (e) {
      return null;
    }
  };

  return (
    <div className="flex h-screen bg-white dark:bg-dark-900 text-gray-900 dark:text-white">
      {/* Sidebar */}
      <motion.div
        initial={false}
        animate={{ x: sidebarOpen ? 0 : '-100%' }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="fixed inset-y-0 left-0 z-50 w-80 bg-gray-50 dark:bg-dark-800 border-r border-gray-200 dark:border-dark-700 lg:relative lg:translate-x-0"
      >
        <Sidebar
          chats={chats}
          currentChatId={currentChatId}
          onNewChat={startNewChat}
          onSelectChat={selectChat}
          onClose={() => setSidebarOpen(false)}
        />
      </motion.div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} health={health} />
        
        <ChatArea
          messages={messages}
          isTyping={isTyping}
          isStreaming={isStreaming}
          onSendMessage={sendMessage}
        />
      </div>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
};

export default App;
