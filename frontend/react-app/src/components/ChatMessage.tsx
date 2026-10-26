import React from 'react';
import { motion } from 'framer-motion';
import { User, Sprout } from 'lucide-react';
import { Message } from '../types';
import { formatTime } from '../utils/dates';

interface ChatMessageProps {
  message: Message;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.sender === 'user';

  // Message assistant encore vide (attente du premier token du streaming)
  if (!isUser && !message.content) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser
            ? 'bg-blue-500 text-white'
            : 'bg-primary-500 text-white'
        }`}
      >
        {isUser ? <User size={16} /> : <Sprout size={16} />}
      </div>

      {/* Message Content */}
      <div className={`flex-1 max-w-xs sm:max-w-md lg:max-w-lg xl:max-w-xl ${isUser ? 'text-right' : ''}`}>
        <div
          className={`inline-block p-3 rounded-2xl ${
            isUser
              ? 'bg-blue-500 text-white rounded-br-md'
              : 'bg-gray-100 dark:bg-dark-800 text-gray-900 dark:text-white rounded-bl-md'
          }`}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>
        
        {/* Timestamp */}
        <p className={`text-xs text-gray-500 dark:text-dark-400 mt-1 ${isUser ? 'text-right' : ''}`}>
          {formatTime(message.timestamp)}
        </p>
      </div>
    </motion.div>
  );
};

export default ChatMessage;