"""
Service d'orchestration du chat pour Imarika.
Coordonne: Question -> Memoire conversation -> Base de connaissances -> Ollama -> Reponse
Le chat est multi-tours : les derniers echanges sont reinjectes comme memoire
courte (`recent_messages`), le contexte CSV part dans un bloc systeme dedie.
"""

import sys
from pathlib import Path
from typing import AsyncIterator, Optional, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.services.ollama_service import ollama_service
from backend.services.knowledge_service import knowledge_service
from backend.services.history_service import history_service
from backend.services import greeting_service
from backend.core.config import settings
from ai.prompts.system_prompts import IMARIKA_SYSTEM_PROMPT

# Nombre max de messages (user + assistant) reinjectes en memoire courte.
MEMORY_TURNS = 6


class ChatService:
    """Orchestre la chaine complete: question -> contexte -> LLM -> reponse."""

    @staticmethod
    def _finish_sentence(text: str) -> str:
        """
        Evite d'afficher une phrase coupee par le budget de tokens :
        on tronque a la derniere fin de phrase (ou a la derniere ligne complete).
        """
        stripped = (text or "").rstrip()
        if not stripped or stripped[-1] in ".!?»)…":
            return stripped
        for sep in (". ", "! ", "? ", "\n"):
            idx = stripped.rfind(sep)
            if idx > 60:
                return stripped[: idx if sep == "\n" else idx + 1].rstrip()
        return stripped

    @staticmethod
    def _slim_chunk(chunk: str, limit: int = 380) -> str:
        """
        Retient l'essentiel d'un extrait CSV (culture/activite + pratiques).
        Les lignes conditionnelles (humidite/hydrique) sont retirees : elles
        sont generiques et doublent le cout du prompt sur CPU.
        """
        lines = (chunk or "").splitlines()
        if not lines:
            return ""
        kept = [lines[0]]
        for line in lines[1:]:
            if line.strip().startswith("- Pratiques"):
                kept.append(line)
                break
        text = "\n".join(kept)
        return text if len(text) <= limit else text[:limit].rstrip() + " …"

    @staticmethod
    def _context_block(context_chunks: List[str], regional_info: str) -> str:
        """Bloc systeme dedie au contexte agronomique ('' si aucun)."""
        parts = [
            ChatService._slim_chunk(c)
            for c in (context_chunks or [])[:2]
        ]
        parts = [p for p in parts if p]
        if regional_info:
            parts.append("--- CONTEXTE REGIONAL BURUNDI ---\n" + regional_info[:350])
        if not parts:
            return ""
        return (
            "\n\n--- DONNEES TECHNIQUES ET AGRONOMIQUES DISPONIBLES ---\n"
            + "\n\n".join(parts)
            + "\n--- FIN DES DONNEES. Utilise-les si pertinentes ; "
              "reponds normalement si la question est hors agriculture. ---"
        )

    @staticmethod
    def _retrieve(message: str):
        """
        Contexte agricole a injecter dans le prompt.
        Question generale (hors agriculture) : aucun contexte CSV -> prompt
        deux fois plus court, donc generation deux fois plus rapide sur CPU.
        """
        if greeting_service.is_general_question(message):
            return [], ""
        kb_result = knowledge_service.retrieve_context(message)
        return (
            kb_result.get("context_chunks", []),
            kb_result.get("regional_info", ""),
        )

    async def process_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> dict:
        """
        Traitement non-streaming (retourne la reponse complete), multi-tours.
        Retourne un dict avec response, conversation_id et context_used.
        """

        # 0. Salutations / politesses : reponse immediate, sans Ollama.
        fast_reply = greeting_service.detect(message)
        if fast_reply:
            conv_id = history_service.get_or_create_conversation(
                conversation_id=conversation_id,
                first_message=message,
                user_id=user_id,
            )
            history_service.add_message(conv_id, "user", message)
            history_service.add_message(conv_id, "assistant", fast_reply)
            return {
                "response": fast_reply,
                "conversation_id": conv_id,
                "context_used": [],
            }

        # 1. Recuperer/creer la conversation SQLite
        conv_id = history_service.get_or_create_conversation(
            conversation_id=conversation_id,
            first_message=message,
            user_id=user_id,
        )

        # 2. Sauvegarder le message utilisateur
        history_service.add_message(conv_id, "user", message)

        # 3. Memoire courte : derniers echanges SAUVEGARDES de cette
        #    conversation (le message courant est le dernier element).
        history = history_service.recent_messages(conv_id, limit=MEMORY_TURNS)

        # 4. Contexte agricole -> bloc systeme dedie
        context_chunks, regional_info = self._retrieve(message)

        # 5. Appeler Ollama en multi-tours
        try:
            response_text = await ollama_service.chat(
                history=history,
                system=IMARIKA_SYSTEM_PROMPT
                + self._context_block(context_chunks, regional_info),
                temperature=0.3,
                num_predict=settings.CHAT_MAX_TOKENS,
            )
        except RuntimeError as e:
            response_text = (
                f"Désolé, je rencontre une difficulté technique : {str(e)}\n"
                "Veuillez réessayer dans quelques instants."
            )

        # 6. Ne jamais afficher une phrase coupee par le budget de tokens
        response_text = self._finish_sentence(response_text)

        # 7. Sauvegarder la reponse
        history_service.add_message(conv_id, "assistant", response_text)

        return {
            "response": response_text,
            "conversation_id": conv_id,
            "context_used": context_chunks[:2] if context_chunks else [],
        }

    async def stream_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Traitement streaming: yielde les tokens au fur et a mesure, multi-tours.
        Sauvegarde la reponse complete en SQLite a la fin.
        """
        # 0. Salutations / politesses : reponse immediate, sans Ollama.
        fast_reply = greeting_service.detect(message)
        if fast_reply:
            conv_id = history_service.get_or_create_conversation(
                conversation_id=conversation_id,
                first_message=message,
                user_id=user_id,
            )
            history_service.add_message(conv_id, "user", message)
            yield f'data: {{"event":"start","conversation_id":"{conv_id}"}}\n\n'
            safe = fast_reply.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
            yield f'data: {{"event":"token","token":"{safe}"}}\n\n'
            history_service.add_message(conv_id, "assistant", fast_reply)
            yield f'data: {{"event":"done","conversation_id":"{conv_id}"}}\n\n'
            return

        # 1. Conversation + message utilisateur
        conv_id = history_service.get_or_create_conversation(
            conversation_id=conversation_id,
            first_message=message,
            user_id=user_id,
        )
        history_service.add_message(conv_id, "user", message)

        # 2. Memoire courte + contexte agricole
        history = history_service.recent_messages(conv_id, limit=MEMORY_TURNS)
        context_chunks, regional_info = self._retrieve(message)

        # 3. Yield metadata event
        yield f'data: {{"event":"start","conversation_id":"{conv_id}"}}\n\n'

        # 4. Stream depuis Ollama en multi-tours
        full_response = ""
        try:
            async for token in ollama_service.stream_chat(
                history=history,
                system=IMARIKA_SYSTEM_PROMPT
                + self._context_block(context_chunks, regional_info),
                temperature=0.3,
                num_predict=settings.CHAT_MAX_TOKENS,
            ):
                full_response += token
                # Echapper les guillemets et sauts de ligne pour JSON
                safe_token = token.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
                yield f'data: {{"event":"token","token":"{safe_token}"}}\n\n'
        except Exception as e:
            err = str(e).replace('"', "'")
            yield f'data: {{"event":"error","message":"{err}"}}\n\n'
            full_response = f"Erreur technique: {str(e)}"

        # 5. Sauvegarder la reponse complete
        if full_response:
            history_service.add_message(conv_id, "assistant", full_response)

        yield f'data: {{"event":"done","conversation_id":"{conv_id}"}}\n\n'


chat_service = ChatService()
