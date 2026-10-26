export interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

export interface Chat {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
}

export interface ApiResponse {
  response: string;
  conversation_id?: string;
  context_used?: string[];
  status?: string;
  error?: string;
}

/** Conversation renvoyee par GET /api/v1/history */
export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

/** Message brut renvoye par GET /api/v1/history/{id} */
export interface BackendMessage {
  id: string;
  sender: string; // "user" | "assistant"
  content: string;
  created_at: string;
}

export interface ConversationDetail {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: BackendMessage[];
}

/** Reponse de GET /api/v1/health */
export interface HealthResponse {
  status: string;
  backend_online: boolean;
  ollama_online: boolean;
  model_available: boolean;
  model_name: string;
  error?: string | null;
  timestamp?: string;
}
