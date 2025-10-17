import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import TypingIndicator from './TypingIndicator';
import { Message } from '../types';

interface ChatAreaProps {
  messages: Message[];
  isTyping: boolean;
  onSendMessage: (message: string) => void;
}

const ChatArea: React.FC<ChatAreaProps> = ({ messages, isTyping, onSendMessage }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-12"
          >
            <div className="text-6xl mb-4">🌾</div>
            <h2 className="text-2xl font-semibold mb-2">Welcome to Imarika AI</h2>
            <p className="text-gray-500 dark:text-dark-400 mb-6">
              Your AI Agricultural Assistant for East African Crops
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-2xl mx-auto">
              {[
                { icon: '🌽', title: 'Maize Nutrition', desc: 'Learn about nutrients for healthy growth' },
                { icon: '🐛', title: 'Pest Management', desc: 'Get advice on managing crop pests' },
                { icon: '🌤️', title: 'Weather Impact', desc: 'Understand weather effects on farming' },
              ].map((item, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="p-4 bg-gray-50 dark:bg-dark-800 rounded-lg text-center"
                >
                  <div className="text-2xl mb-2">{item.icon}</div>
                  <h3 className="font-medium mb-1">{item.title}</h3>
                  <p className="text-sm text-gray-500 dark:text-dark-400">{item.desc}</p>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}

        {isTyping && <TypingIndicator />}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 dark:border-dark-700 p-4">
        <ChatInput onSendMessage={onSendMessage} disabled={isTyping} />
      </div>
    </div>
  );
};

export default ChatArea;