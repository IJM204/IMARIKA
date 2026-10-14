"""
Service « Mes cultures » : gestion des parcelles isolees par utilisateur.

user_id est TOUJOURS requis ici (une parcelle est un donnee personnelle) :
les appels viennent des endpoints /api/v1/plots qui utilisent require_user().
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from backend.core.database import get_connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PlotsError(Exception):
    """Erreur metier (validation) -> 400 cote API."""


class PlotsService:
    @staticmethod
    def _validate(payload: Dict[str, Any]) -> Dict[str, Any]:
        crop = (payload.get("crop") or "").strip()
        if not crop:
            raise PlotsError("La culture est obligatoire.")
        if len(crop) > 80:
            raise PlotsError("Nom de culture trop long (80 caracteres max).")

        region = (payload.get("region") or None)
        if region:
            region = region.strip()[:80]

        notes = (payload.get("notes") or None)
        if notes:
            notes = notes.strip()[:500]

        area = payload.get("area_ha")
        if area in ("", None):
            area = None
        try:
            area = float(area) if area is not None else None
        except (TypeError, ValueError):
            raise PlotsError("Superficie invalide : donnez un nombre (en hectares).")
        if area is not None and (area < 0 or area > 100000):
            raise PlotsError("Superficie invalide (0 - 100 000 ha).")

        planted = (payload.get("planted_at") or None)
        if planted:
            planted = str(planted).strip()[:10]  # format YYYY-MM-DD

        return {
            "crop": crop[:80],
            "region": region,
            "area_ha": area,
            "planted_at": planted,
            "notes": notes,
        }

    # ------------------------------------------------------------------ #
    #  CRUD                                                               #
    # ------------------------------------------------------------------ #
    def list_plots(self, user_id: str) -> List[dict]:
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM plots WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_plot(self, plot_id: str, user_id: str) -> Optional[dict]:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM plots WHERE id = ? AND user_id = ?",
                (plot_id, user_id),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def create_plot(self, payload: Dict[str, Any], user_id: str) -> dict:
        clean = self._validate(payload)
        now = _now()
        plot = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "created_at": now,
            "updated_at": now,
            **clean,
        }
        conn = get_connection()
        try:
            with conn:
                conn.execute(
                    """INSERT INTO plots
                       (id, user_id, crop, region, area_ha, planted_at, notes,
                        created_at, updated_at)
                       VALUES (:id, :user_id, :crop, :region, :area_ha,
                               :planted_at, :notes, :created_at, :updated_at)""",
                    plot,
                )
        finally:
            conn.close()
        return plot

    def update_plot(self, plot_id: str, payload: Dict[str, Any], user_id: str) -> Optional[dict]:
        clean = self._validate(payload)
        conn = get_connection()
        try:
            with conn:
                cur = conn.execute(
                    """UPDATE plots SET crop = :crop, region = :region,
                       area_ha = :area_ha, planted_at = :planted_at,
                       notes = :notes, updated_at = :updated_at
                       WHERE id = :id AND user_id = :uid""",
                    {
                        "id": plot_id,
                        "uid": user_id,
                        "updated_at": _now(),
                        **clean,
                    },
                )
                if cur.rowcount == 0:
                    return None
            return self.get_plot(plot_id, user_id)
        finally:
            conn.close()

    def delete_plot(self, plot_id: str, user_id: str) -> bool:
        conn = get_connection()
        try:
            with conn:
                cur = conn.execute(
                    "DELETE FROM plots WHERE id = ? AND user_id = ?",
                    (plot_id, user_id),
                )
                return cur.rowcount > 0
        finally:
            conn.close()

    # ------------------------------------------------------------------ #
    #  Injection dans le chat                                             #
    # ------------------------------------------------------------------ #
    def profile_block(self, user_id: str) -> str:
        """
        Resume lisible des parcelles pour le prompt systeme du chatbot :
        culture, province, superficie, anciennete de la plantation.
        Chaine vide si l'utilisateur n'a aucune parcelle.
        """
        plots = self.list_plots(user_id)
        if not plots:
            return ""
        lines = []
        for p in plots[:6]:  # budget CPU : au plus 6 parcelles
            days = ""
            if p.get("planted_at"):
                try:
                    from datetime import date
                    planted = date.fromisoformat(str(p["planted_at"])[:10])
                    n = (date.today() - planted).days
                    if n >= 0:
                        days = f", plantee il y a {n} jours"
                except ValueError:
                    days = ""
            area = f", {p['area_ha']:g} ha" if p.get("area_ha") else ""
            region = f", province de {p['region']}" if p.get("region") else ""
            lines.append(f"- {p['crop']}{area}{region}{days}.")
        return (
            "--- PARCELLES DE CET UTILISATEUR (contexte personnel, "
            "utilisez-le automatiquement sans redemander ces informations) ---\\n"
            + "\\n".join(lines)
        )


plots_service = PlotsService()
