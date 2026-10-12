"""Endpoints pour l'historique des conversations SQLite (isole par utilisateur)."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.api.v1.deps import get_current_user
from backend.schemas.history import ConversationSummary, ConversationDetail
from backend.services.history_service import history_service

router = APIRouter()


def _user_id(user: Optional[dict]) -> Optional[str]:
    return user["id"] if isinstance(user, dict) else None


@router.get("/history", response_model=List[ConversationSummary], tags=["History"])
async def list_conversations(user: Optional[dict] = Depends(get_current_user)):
    """Liste des conversations visibles par l'utilisateur connecte."""
    try:
        return history_service.list_conversations(user_id=_user_id(user))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recuperation de l historique: {str(e)}")


@router.get("/history/{conversation_id}", response_model=ConversationDetail, tags=["History"])
async def get_conversation(
    conversation_id: str,
    user: Optional[dict] = Depends(get_current_user),
):
    """Retourne les messages d une conversation (404 si elle n appartient pas a l utilisateur)."""
    conv = history_service.get_conversation_messages(
        conversation_id, user_id=_user_id(user)
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation introuvable.")
    return conv


@router.delete("/history/{conversation_id}", tags=["History"])
async def delete_conversation(
    conversation_id: str,
    user: Optional[dict] = Depends(get_current_user),
):
    """Supprime une conversation et ses messages associes."""
    success = history_service.delete_conversation(
        conversation_id, user_id=_user_id(user)
    )
    if not success:
        raise HTTPException(status_code=404, detail="Conversation introuvable ou deja supprimee.")
    return {"status": "success", "message": "Conversation supprimee avec succes."}
