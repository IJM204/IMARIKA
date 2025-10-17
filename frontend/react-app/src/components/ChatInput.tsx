import React, { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import { motion } from 'framer-motion';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled = false }) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  return (
    <motion.form
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      onSubmit={handleSubmit}
      className="flex items-end space-x-3"
    >
      <div className="flex-1 relative">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about maize, beans, cassava, sorghum, finger millet, or sweet potatoes..."
          disabled={disabled}
          rows={1}
          className="w-full px-4 py-3 pr-12 bg-gray-50 dark:bg-dark-800 border border-gray-200 dark:border-dark-700 rounded-2xl resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed max-h-32"
        />
        
        {/* Quick suggestions */}
        {!message && (
          <div className="absolute top-full left-0 right-0 mt-2 flex flex-wrap gap-2">
            {[
              'What nutrients does maize need?',
              'How to manage bean pests?',
              'Best weather for cassava?',
            ].map((suggestion, index) => (
              <button
                key={index}
                type="button"
                onClick={() => setMessage(suggestion)}
                className="px-3 py-1 text-xs bg-gray-100 dark:bg-dark-700 text-gray-600 dark:text-dark-300 rounded-full hover:bg-gray-200 dark:hover:bg-dark-600 transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}
      </div>

      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        type="submit"
        disabled={!message.trim() || disabled}
        className="p-3 bg-primary-500 text-white rounded-2xl hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <Send size={16} />
      </motion.button>
    </motion.form>
  );
};

export default ChatInput;