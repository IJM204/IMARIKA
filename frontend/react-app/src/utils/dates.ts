import { Chat, Message, BackendMessage } from '../types';

/**
 * Convertit une date qui peut etre un Date (etat React) ou une string ISO
 * (restauration depuis localStorage / API) en objet Date valide.
 */
export const toDate = (value: Date | string | undefined | null): Date => {
  if (value instanceof Date) {
    return isNaN(value.getTime()) ? new Date() : value;
  }
  const parsed = value ? new Date(value) : new Date();
  return isNaN(parsed.getTime()) ? new Date() : parsed;
};

export const reviveMessage = (message: Message): Message => ({
  ...message,
  timestamp: toDate(message.timestamp),
});

/** Reconstitue les Dates apres un JSON.parse(localStorage). */
export const reviveChats = (chats: Chat[]): Chat[] => {
  if (!Array.isArray(chats)) return [];
  return chats.map((chat) => ({
    ...chat,
    createdAt: toDate(chat.createdAt),
    messages: Array.isArray(chat.messages) ? chat.messages.map(reviveMessage) : [],
  }));
};

/** Formate une date pour la Sidebar, qu'elle soit Date ou string ISO. */
export const formatDate = (value: Date | string): string => {
  const date = toDate(value);
  return date.toLocaleDateString(undefined, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
};

/** Formate une heure pour l'affichage d'un message. */
export const formatTime = (value: Date | string): string =>
  toDate(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

/** Transforme un message SQLite (sender: assistant) en message UI (sender: bot). */
export const mapBackendMessage = (message: BackendMessage): Message => ({
  id: message.id,
  content: message.content,
  sender: message.sender === 'user' ? 'user' : 'bot',
  timestamp: toDate(message.created_at),
});
