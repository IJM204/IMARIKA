import {
  ApiResponse,
  ConversationSummary,
  ConversationDetail,
  HealthResponse,
} from '../types';

/**
 * Point d'entree du backend FastAPI.
 * Surchargeable via la variable d'environnement REACT_APP_API_URL.
 */
export const API_BASE =
  process.env.REACT_APP_API_URL || 'http://localhost:8000';

const JSON_HEADERS = { 'Content-Type': 'application/json' };

export interface ChatPayload {
  message: string;
  conversation_id?: string | null;
  language?: string;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

const parsePayload = (payload: ChatPayload) => ({
  message: payload.message,
  conversation_id: payload.conversation_id || undefined,
  language: payload.language || 'fr',
});

/* ------------------------------------------------------------------ */
/*  POST /api/v1/chat — reponse complete                               */
/* ------------------------------------------------------------------ */

export async function postChat(payload: ChatPayload): Promise<ApiResponse> {
  const response = await fetch(`${API_BASE}/api/v1/chat`, {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify(parsePayload(payload)),
  });

  if (!response.ok) {
    let detail = `Erreur ${response.status}`;
    try {
      const body = await response.json();
      detail = body?.detail || body?.error || detail;
    } catch {
      /* reponse non JSON */
    }
    throw new ApiError(response.status, detail);
  }
  return response.json();
}

/* ------------------------------------------------------------------ */
/*  POST /api/v1/chat/stream — SSE (Server-Sent Events)                */
/* ------------------------------------------------------------------ */

export interface StreamHandlers {
  onStart?: (conversationId?: string) => void;
  onToken?: (token: string) => void;
  onError?: (message: string) => void;
  onDone?: (conversationId?: string) => void;
}

/**
 * Consomme le flux SSE du backend et dispatche les evenements
 * {event: start|token|error|done}. Retourne le nombre de tokens recus.
 */
export async function streamChat(
  payload: ChatPayload,
  handlers: StreamHandlers,
): Promise<number> {
  const response = await fetch(`${API_BASE}/api/v1/chat/stream`, {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify(parsePayload(payload)),
    cache: 'no-store',
  });

  if (!response.ok) {
    let detail = `Erreur ${response.status}`;
    try {
      const body = await response.json();
      detail = body?.detail || detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(response.status, detail);
  }

  const body = response.body;
  if (!body) {
    throw new ApiError(500, "Le navigateur n'a pas pu lire le flux SSE.");
  }

  const reader = body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  let tokens = 0;

  const dispatch = (rawLine: string) => {
    const trimmed = rawLine.trim();
    if (!trimmed.startsWith('data:')) return;
    const json = trimmed.slice(5).trim();
    if (!json) return;

    let event: any;
    try {
      event = JSON.parse(json);
    } catch {
      return; // ligne SSE incomplete / keep-alive
    }

    switch (event.event) {
      case 'start':
        handlers.onStart?.(event.conversation_id);
        break;
      case 'token':
        tokens += 1;
        handlers.onToken?.(event.token ?? '');
        break;
      case 'error':
        handlers.onError?.(event.message ?? 'Erreur inconnue');
        break;
      case 'done':
        handlers.onDone?.(event.conversation_id);
        break;
      default:
        break;
    }
  };

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let index: number;
      while ((index = buffer.indexOf('\n\n')) !== -1) {
        const block = buffer.slice(0, index);
        buffer = buffer.slice(index + 2);
        block.split('\n').forEach(dispatch);
      }
    }
    // s'il reste du buffer (dernier evenement sans separateur final)
    if (buffer.trim()) buffer.split('\n').forEach(dispatch);
  } finally {
    try {
      reader.releaseLock();
    } catch {
      /* ignore */
    }
  }

  return tokens;
}

/* ------------------------------------------------------------------ */
/*  Historique SQLite via FastAPI                                       */
/* ------------------------------------------------------------------ */

export async function listConversations(): Promise<ConversationSummary[]> {
  const response = await fetch(`${API_BASE}/api/v1/history`);
  if (!response.ok) throw new ApiError(response.status, 'Historique indisponible');
  return response.json();
}

export async function getConversation(id: string): Promise<ConversationDetail> {
  const response = await fetch(`${API_BASE}/api/v1/history/${encodeURIComponent(id)}`);
  if (!response.ok) throw new ApiError(response.status, 'Conversation introuvable');
  return response.json();
}

export async function deleteConversation(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/history/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new ApiError(response.status, 'Suppression impossible');
}

/* ------------------------------------------------------------------ */
/*  Sante du systeme                                                    */
/* ------------------------------------------------------------------ */

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/api/v1/health`, { cache: 'no-store' });
  if (!response.ok) throw new ApiError(response.status, 'Service de sante indisponible');
  return response.json();
}
