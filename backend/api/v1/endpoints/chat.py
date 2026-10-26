"""Endpoints POST /api/v1/chat et GET /api/v1/chat/stream."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from backend.api.v1.deps import get_current_user
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services import greeting_service
from backend.services.chat_service import chat_service
from backend.services.ollama_service import ollama_service

import asyncio

router = APIRouter()

# Protection matérielle CPU : maximum 2 générations simultanées pour éviter le gel machine
_LLM_SEMAPHORE = asyncio.Semaphore(2)


def _user_id(user: Optional[dict]) -> Optional[str]:
    return user["id"] if isinstance(user, dict) else None


async def _ensure_llm(message: str) -> None:
    """Lève 503 si Ollama est down — sauf pour les salutations et la météo en direct,
    répondues localement sans modèle (la conversation reste utilisable)."""
    if greeting_service.detect(message) or chat_service._detect_weather_query(message):
        return
    if not await ollama_service.is_ollama_available():
        raise HTTPException(
            status_code=503,
            detail="Le service Ollama est indisponible. Vérifiez qu'il est lancé sur http://localhost:11434",
        )


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_endpoint(
    request: ChatRequest,
    user: Optional[dict] = Depends(get_current_user),
):
    """
    Endpoint principal de chat (reponse complete).
    Accepte un message, interroge la base de connaissances et Ollama.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Le message ne peut pas etre vide.")

    # Verifier Ollama avant de lancer la generation (sauf météo/salutations)
    await _ensure_llm(request.message)

    # Si c'est une requête météo ou salutation, exécution directe sans sémaphore
    if greeting_service.detect(request.message) or chat_service._detect_weather_query(request.message):
        result = await chat_service.process_message(
            message=request.message,
            conversation_id=request.conversation_id,
            user_id=_user_id(user),
        )
        return ChatResponse(
            response=result["response"],
            conversation_id=result["conversation_id"],
            context_used=result.get("context_used", []),
        )

    # Protection CPU via sémaphore pour les inférences LLM
    try:
        async with _LLM_SEMAPHORE:
            result = await chat_service.process_message(
                message=request.message,
                conversation_id=request.conversation_id,
                user_id=_user_id(user),
            )
            return ChatResponse(
                response=result["response"],
                conversation_id=result["conversation_id"],
                context_used=result.get("context_used", []),
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@router.post("/chat/stream", tags=["Chat"])
async def chat_stream_post_endpoint(
    request: ChatRequest,
    user: Optional[dict] = Depends(get_current_user),
):
    """
    Endpoint streaming SSE (Server-Sent Events) via POST JSON.
    Retourne les tokens un par un pour un affichage progressif.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Le message ne peut pas etre vide.")

    await _ensure_llm(request.message)

    return StreamingResponse(
        chat_service.stream_message(
            message=request.message,
            conversation_id=request.conversation_id,
            user_id=_user_id(user),
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/chat/stream", tags=["Chat"])
async def chat_stream_endpoint(
    message: str,
    conversation_id: Optional[str] = None,
    user: Optional[dict] = Depends(get_current_user),
):
    """
    Endpoint streaming SSE (Server-Sent Events) via GET query parameters.
    Retourne les tokens un par un pour un affichage progressif.
    """
    if not message.strip():
        raise HTTPException(status_code=400, detail="Le message ne peut pas etre vide.")

    await _ensure_llm(message)

    return StreamingResponse(
        chat_service.stream_message(
            message=message,
            conversation_id=conversation_id,
            user_id=_user_id(user),
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
