import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from backend.core.database import get_connection


class HistoryService:
    """Historique des conversations, isole par utilisateur.

    user_id = None  -> mode anonyme (tests, ancien frontend React)
    user_id = "..." -> l'utilisateur ne voit que SES conversations.
    """

    # ------------------------------------------------------------------ #
    #  Regle d'isolation                                                   #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _visible(user_id: Optional[str]):
        """Clause SQL de visibilite selon le connecte."""
        if user_id:
            return "AND user_id = ?", (user_id,)
        # Anonyme : uniquement les conversations anonymes
        return "AND user_id IS NULL", ()

    @staticmethod
    def _conversation_visible(conn, conversation_id: str, user_id: Optional[str]):
        clause, params = HistoryService._visible(user_id)
        cur = conn.execute(
            f"SELECT id, user_id FROM conversations WHERE id = ? {clause}",
            (conversation_id, *params),
        )
        return cur.fetchone()

    # ------------------------------------------------------------------ #
    #  Conversations                                                      #
    # ------------------------------------------------------------------ #
    @staticmethod
    def get_or_create_conversation(
        conversation_id: Optional[str] = None,
        first_message: str = "",
        user_id: Optional[str] = None,
    ) -> str:
        conn = get_connection()
        try:
            with conn:
                if conversation_id:
                    row = HistoryService._conversation_visible(
                        conn, conversation_id, user_id
                    )
                    if row:
                        return row["id"]
                    # Conversation inexistante OU appartenant a un autre
                    # utilisateur : on en cree une nouvelle proprement.

                new_id = str(uuid.uuid4())
                now = datetime.now(timezone.utc).isoformat()
                title = first_message.strip()[:40] if first_message else "Nouvelle conversation"
                if len(first_message.strip()) > 40:
                    title += "..."

                conn.execute(
                    """INSERT INTO conversations
                       (id, title, created_at, updated_at, user_id)
                       VALUES (?, ?, ?, ?, ?)""",
                    (new_id, title, now, now, user_id),
                )
                return new_id
        finally:
            conn.close()

    @staticmethod
    def add_message(conversation_id: str, sender: str, content: str) -> Dict[str, Any]:
        conn = get_connection()
        try:
            with conn:
                msg_id = str(uuid.uuid4())
                now = datetime.now(timezone.utc).isoformat()
                conn.execute(
                    "INSERT INTO messages (id, conversation_id, sender, content, created_at) VALUES (?, ?, ?, ?, ?)",
                    (msg_id, conversation_id, sender, content, now)
                )
                conn.execute(
                    "UPDATE conversations SET updated_at = ? WHERE id = ?",
                    (now, conversation_id)
                )
                return {
                    "id": msg_id,
                    "conversation_id": conversation_id,
                    "sender": sender,
                    "content": content,
                    "created_at": now
                }
        finally:
            conn.close()

    @staticmethod
    def list_conversations(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            clause, params = HistoryService._visible(user_id)
            cur = conn.execute(f"""
                SELECT c.id, c.title, c.created_at, c.updated_at,
                       COUNT(m.id) as message_count
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE 1=1 {clause}
                GROUP BY c.id
                ORDER BY c.updated_at DESC
            """, params)
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def get_conversation_messages(
        conversation_id: str, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        try:
            conv = HistoryService._conversation_visible(conn, conversation_id, user_id)
            if not conv:
                return None

            cur = conn.execute("SELECT id, title, created_at, updated_at FROM conversations WHERE id = ?", (conversation_id,))
            conv_data = cur.fetchone()
            if not conv_data:
                return None

            cur_msg = conn.execute(
                "SELECT id, sender, content, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
                (conversation_id,)
            )
            messages = [dict(m) for m in cur_msg.fetchall()]

            result = dict(conv_data)
            result["messages"] = messages
            return result
        finally:
            conn.close()

    @staticmethod
    def delete_conversation(
        conversation_id: str, user_id: Optional[str] = None
    ) -> bool:
        conn = get_connection()
        try:
            with conn:
                row = HistoryService._conversation_visible(conn, conversation_id, user_id)
                if not row:
                    return False
                cur = conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
                return cur.rowcount > 0
        finally:
            conn.close()


history_service = HistoryService()
