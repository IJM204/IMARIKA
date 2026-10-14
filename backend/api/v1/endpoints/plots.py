"""
Endpoints « Mes cultures » : CRUD des parcelles de l'utilisateur connecte.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from backend.api.v1.deps import require_user
from backend.services.plots_service import plots_service, PlotsError

router = APIRouter(prefix="/plots", tags=["Plots"])


class PlotCreate(BaseModel):
    crop: str = Field(..., min_length=1, max_length=80)
    region: Optional[str] = Field(None, max_length=80)
    area_ha: Optional[float] = Field(None, ge=0, le=100000)
    planted_at: Optional[str] = Field(None, max_length=10)
    notes: Optional[str] = Field(None, max_length=500)


class PlotUpdate(BaseModel):
    crop: str = Field(..., min_length=1, max_length=80)
    region: Optional[str] = Field(None, max_length=80)
    area_ha: Optional[float] = Field(None, ge=0, le=100000)
    planted_at: Optional[str] = Field(None, max_length=10)
    notes: Optional[str] = Field(None, max_length=500)


@router.get("", summary="Lister mes parcelles")
async def list_plots(user: dict = Depends(require_user)):
    return plots_service.list_plots(user["id"])


@router.post("", summary="Creer une parcelle")
async def create_plot(payload: PlotCreate, user: dict = Depends(require_user)):
    try:
        return plots_service.create_plot(payload.dict(), user["id"])
    except PlotsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{plot_id}", summary="Modifier une parcelle")
async def update_plot(
    plot_id: str, payload: PlotUpdate, user: dict = Depends(require_user)
):
    try:
        updated = plots_service.update_plot(plot_id, payload.dict(), user["id"])
    except PlotsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not updated:
        raise HTTPException(status_code=404, detail="Parcelle introuvable.")
    return updated


@router.delete("/{plot_id}", summary="Supprimer une parcelle")
async def delete_plot(plot_id: str, user: dict = Depends(require_user)):
    if not plots_service.delete_plot(plot_id, user["id"]):
        raise HTTPException(status_code=404, detail="Parcelle introuvable.")
    return {"status": "success", "message": "Parcelle supprimee avec succes."}
