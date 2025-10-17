import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import { Message, Chat } from './types';
import { useLocalStorage } from './hooks/useLocalStorage';
import './index.css';

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [chats, setChats] = useLocalStorage<Chat[]>('imarika-chats', []);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);

  // Initialize with welcome message
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([{
        id: '1',
        content: '🌾 Habari! Mimi ni Imarika, mshauri wako wa kilimo wa mazao ya Afrika Mashariki. Ninaweza kukusaidia na maswali kuhusu mahindi, maharage, mihogo, ulezi, mtama, na viazi vitamu. Uliza swali lolote!',
        sender: 'bot',
        timestamp: new Date(),
      }]);
    }
  }, [messages.length]);

  const sendMessage = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);

    try {
      // Simulate API call to your backend
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();
      
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.response || 'Samahani, sijaweza kupata jibu. Jaribu tena.',
        sender: 'bot',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      // Fallback response for demo
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Samahani, kuna tatizo la kiufundi. Jaribu tena baadaye.',
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, botMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const startNewChat = () => {
    const newChat: Chat = {
      id: Date.now().toString(),
      title: 'New Chat',
      messages: [],
      createdAt: new Date(),
    };
    
    setChats(prev => [newChat, ...prev]);
    setCurrentChatId(newChat.id);
    setMessages([]);
    setSidebarOpen(false);
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
          onSelectChat={(chatId) => {
            setCurrentChatId(chatId);
            setSidebarOpen(false);
          }}
          onClose={() => setSidebarOpen(false)}
        />
      </motion.div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />
        
        <ChatArea
          messages={messages}
          isTyping={isTyping}
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