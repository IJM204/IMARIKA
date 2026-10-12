import sqlite3
import os
from pathlib import Path
from backend.core.config import settings

def get_db_path() -> Path:
    db_path = Path(settings.DATABASE_PATH)
    if not db_path.is_absolute():
        db_path = Path(settings.PROJECT_ROOT) / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path

def get_connection() -> sqlite3.Connection:
    """Provides a SQLite connection with foreign keys enabled and row factory."""
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)


def init_db():
    """Initializes the database schema if tables do not exist.

    Gere aussi la MIGRATION d'une base existante : la colonne
    conversations.user_id et la table users sont ajoutees si absentes.
    """
    conn = get_connection()
    try:
        with conn:
            # ---------------------------------------------------------- #
            #  Conversations (avec user_id optionnel pour la migration)   #
            # ---------------------------------------------------------- #
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            if not _column_exists(conn, "conversations", "user_id"):
                # Base creee avant l'ajout des comptes utilisateurs
                conn.execute(
                    "ALTER TABLE conversations ADD COLUMN user_id TEXT"
                )

            # ---------------------------------------------------------- #
            #  Messages                                                   #
            # ---------------------------------------------------------- #
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    sender TEXT NOT NULL CHECK (sender IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
                ON messages(conversation_id)
            """)

            # ---------------------------------------------------------- #
            #  Comptes utilisateurs (login + mot de passe)                 #
            # ---------------------------------------------------------- #
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    display_name TEXT,
                    phone TEXT,
                    region TEXT,
                    crops TEXT,
                    language TEXT NOT NULL DEFAULT 'fr',
                    created_at TEXT NOT NULL
                )
            """)

            # ---------------------------------------------------------- #
            #  Sessions (jeton d'acces)                                    #
            # ---------------------------------------------------------- #
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # ---------------------------------------------------------- #
            #  Index                                                      #
            # ---------------------------------------------------------- #
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_conversations_user_id "
                "ON conversations(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_user_id "
                "ON sessions(user_id)"
            )
    finally:
        conn.close()
