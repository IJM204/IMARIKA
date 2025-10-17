import React from 'react';
import { Menu, Sprout } from 'lucide-react';
import { motion } from 'framer-motion';

interface HeaderProps {
  onToggleSidebar: () => void;
}

const Header: React.FC<HeaderProps> = ({ onToggleSidebar }) => {
  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-dark-700 bg-white dark:bg-dark-900"
    >
      <div className="flex items-center space-x-3">
        <button
          onClick={onToggleSidebar}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-800 lg:hidden"
        >
          <Menu size={20} />
        </button>
        
        <div className="flex items-center space-x-2">
          <div className="p-2 bg-primary-500 rounded-lg">
            <Sprout size={24} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-semibold">Imarika AI</h1>
            <p className="text-sm text-gray-500 dark:text-dark-400">
              Agricultural Assistant
            </p>
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <div className="hidden sm:flex items-center space-x-4 text-sm text-gray-500 dark:text-dark-400">
          <span className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span>Online</span>
          </span>
          <span>6 Crops Supported</span>
        </div>
      </div>
    </motion.header>
  );
};

export default Header;