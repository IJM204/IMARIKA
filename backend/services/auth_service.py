"""
Authentification des utilisateurs — 100 % module standard Python.

Aucune dependance externe (pas de bcrypt/passlib) : hachage PBKDF2-HMAC-SHA256
avec 310 000 itérations (recommandation OWASP 2023) + jetons de session aleatoires.

Format du hash :  pbkdf2_sha256$<iterations>$<sel_base64>$<empreinte_base64>
"""

import base64
import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from backend.core.database import get_connection

# --- Paramètres de sécurité -------------------------------------------------
PBKDF2_ITERATIONS = 310_000
SALT_BYTES = 16
DIGEST_BYTES = 32
SESSION_TTL_DAYS = 30

# --- Contraintes -------------------------------------------------------------
USERNAME_MIN, USERNAME_MAX = 3, 30
PASSWORD_MIN, PASSWORD_MAX = 6, 128


class AuthError(Exception):
    """Erreur metier renvoyee telle quelle a l'utilisateur (400/401)."""


# --------------------------------------------------------------------------- #
#  Hachage des mots de passe                                                  #
# --------------------------------------------------------------------------- #

def hash_password(password: str) -> str:
    if not isinstance(password, str) or not (PASSWORD_MIN <= len(password) <= PASSWORD_MAX):
        raise AuthError(f"Le mot de passe doit contenir {PASSWORD_MIN} a {PASSWORD_MAX} caractères.")
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS, DIGEST_BYTES)
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, stored: str) -> bool:
    """Comparaison en temps constant (anti-timing)."""
    try:
        algo, iterations_s, salt_b64, digest_b64 = (stored or "").split("$")
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iterations_s)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
    except Exception:
        return False
    actual = hashlib.pbkdf2_hmac("sha256", (password or "").encode("utf-8"), salt, iterations, len(expected))
    return hmac.compare_digest(actual, expected)


# --------------------------------------------------------------------------- #
#  Gestion des comptes                                                        #
# --------------------------------------------------------------------------- #

def _validate_username(username: str) -> str:
    username = (username or "").strip()
    if not (USERNAME_MIN <= len(username) <= USERNAME_MAX):
        raise AuthError(f"Le nom d'utilisateur doit contenir {USERNAME_MIN} a {USERNAME_MAX} caractères.")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    if not set(username) <= allowed:
        raise AuthError("Nom d'utilisateur : lettres, chiffres, '.', '_' ou '-' uniquement.")
    return username


def create_user(
    username: str,
    password: str,
    display_name: Optional[str] = None,
    phone: Optional[str] = None,
    region: Optional[str] = None,
    crops: Optional[str] = None,
    language: Optional[str] = "fr",
) -> Dict[str, Any]:
    username = _validate_username(username)
    pwd_hash = hash_password(password)

    conn = get_connection()
    try:
        with conn:
            exists = conn.execute(
                "SELECT 1 FROM users WHERE username = ?", (username,)
            ).fetchone()
            if exists:
                raise AuthError("Ce nom d'utilisateur est déjà pris.")
            user_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """INSERT INTO users
                   (id, username, password_hash, display_name, phone, region,
                    crops, language, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    user_id, username, pwd_hash,
                    display_name or username, phone, region,
                    crops, language or "fr", now,
                ),
            )
            return {
                "id": user_id,
                "username": username,
                "display_name": display_name or username,
                "phone": phone,
                "region": region,
                "crops": crops,
                "language": language or "fr",
                "created_at": now,
            }
    finally:
        conn.close()


def authenticate(username: str, password: str) -> Dict[str, Any]:
    """Verifie les identifiants et retourne le profil sans le hash."""
    username = (username or "").strip()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        # Toujours verifier (temps constant) meme si l'utilisateur n'existe pas
        dummy = "pbkdf2_sha256$310000$AAAAAAAAAAAAAAAAAAAAAA==$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
        if not row:
            verify_password(password, dummy)
            raise AuthError("Identifiants incorrects.")
        if not verify_password(password, row["password_hash"]):
            raise AuthError("Identifiants incorrects.")
        return _public_user(row)
    finally:
        conn.close()


def _public_user(row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"],
        "phone": row["phone"],
        "region": row["region"],
        "crops": row["crops"],
        "language": row["language"],
        "created_at": row["created_at"],
    }


# --------------------------------------------------------------------------- #
#  Sessions (jetons sécurisés avec hachage SHA-256 en base)                   #
# --------------------------------------------------------------------------- #

def _hash_token(token: str) -> str:
    """Empreinte cryptographique SHA-256 du jeton pour stockage en base."""
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def create_session(user_id: str) -> Dict[str, Any]:
    """
    Crée une session sécurisée : le jeton brut est renvoyé à l'utilisateur,
    mais seule son empreinte SHA-256 est enregistrée dans SQLite.
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=SESSION_TTL_DAYS)
    conn = get_connection()
    try:
        with conn:
            # Nettoyage des sessions expirees a chaque connexion
            conn.execute("DELETE FROM sessions WHERE expires_at < ?", (now.isoformat(),))
            conn.execute(
                "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
                (token_hash, user_id, now.isoformat(), expires.isoformat()),
            )
            return {"token": raw_token, "expires_at": expires.isoformat()}
    finally:
        conn.close()


def get_user_by_token(token: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Retourne le profil lie au jeton, ou None (invalide/expire).
    Supporte les jetons hachés en SHA-256 ainsi que les anciens jetons bruts.
    """
    if not token:
        return None
    token_hash = _hash_token(token)
    now_iso = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT u.* FROM sessions s
               JOIN users u ON u.id = s.user_id
               WHERE (s.token = ? OR s.token = ?) AND s.expires_at > ?""",
            (token_hash, token, now_iso),
        ).fetchone()
        return _public_user(row) if row else None
    finally:
        conn.close()


def delete_session(token: Optional[str]) -> bool:
    if not token:
        return False
    token_hash = _hash_token(token)
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute("DELETE FROM sessions WHERE token = ? OR token = ?", (token_hash, token))
            return cur.rowcount > 0
    finally:
        conn.close()


def update_profile(user_id: str, **fields) -> Optional[Dict[str, Any]]:
    """Mise a jour partielle du profil (champs connus uniquement)."""
    allowed = {"display_name", "phone", "region", "crops", "language"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return None
    conn = get_connection()
    try:
        with conn:
            sets = ", ".join(f"{k} = ?" for k in updates)
            conn.execute(
                f"UPDATE users SET {sets} WHERE id = ?",
                (*updates.values(), user_id),
            )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _public_user(row) if row else None
    finally:
        conn.close()
