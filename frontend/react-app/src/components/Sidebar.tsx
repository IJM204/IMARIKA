import React from 'react';
import { Plus, MessageSquare, Settings, X } from 'lucide-react';
import { motion } from 'framer-motion';
import { Chat } from '../types';
import { formatDate } from '../utils/dates';

interface SidebarProps {
  chats: Chat[];
  currentChatId: string | null;
  onNewChat: () => void;
  onSelectChat: (chatId: string) => void;
  onClose: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  chats,
  currentChatId,
  onNewChat,
  onSelectChat,
  onClose,
}) => {
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-dark-700">
        <h2 className="font-semibold">Chats</h2>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-gray-200 dark:hover:bg-dark-700 lg:hidden"
        >
          <X size={16} />
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-4">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onNewChat}
          className="w-full flex items-center space-x-2 p-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
        >
          <Plus size={16} />
          <span>New Chat</span>
        </motion.button>
      </div>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto px-4">
        <div className="space-y-2">
          {chats.map((chat) => (
            <motion.button
              key={chat.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              whileHover={{ x: 4 }}
              onClick={() => onSelectChat(chat.id)}
              className={`w-full flex items-center space-x-3 p-3 rounded-lg text-left transition-colors ${
                currentChatId === chat.id
                  ? 'bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800'
                  : 'hover:bg-gray-100 dark:hover:bg-dark-700'
              }`}
            >
              <MessageSquare size={16} className="text-gray-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{chat.title}</p>
                <p className="text-xs text-gray-500 dark:text-dark-400">
                  {formatDate(chat.createdAt)}
                </p>
              </div>
            </motion.button>
          ))}
        </div>

        {chats.length === 0 && (
          <div className="text-center py-8 text-gray-500 dark:text-dark-400">
            <MessageSquare size={32} className="mx-auto mb-2 opacity-50" />
            <p className="text-sm">No chats yet</p>
            <p className="text-xs">Start a new conversation</p>
          </div>
        )}
      </div>

      {/* Settings */}
      <div className="p-4 border-t border-gray-200 dark:border-dark-700">
        <button className="w-full flex items-center space-x-2 p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-700 transition-colors">
          <Settings size={16} />
          <span>Settings</span>
        </button>
      </div>
    </div>
  );
};

export default Sidebar;