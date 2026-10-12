"""
AGRIBurundi-AI / Imarika — Backend Principal FastAPI.
Point d'entree modulaire et asynchrone pour l'assistant agricole burundais.
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Assurer l'importabilite des modules internes
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Interface web legere (HTML/CSS/JS natif, aucune dependance)
STATIC_DIR = Path(__file__).resolve().parent / "static"

from backend.core.config import settings
from backend.core.database import init_db
from backend.api.v1.router import api_v1_router
from backend.api.v1.deps import get_current_user
from backend.api.v1.endpoints.health import health_check
from backend.api.v1.endpoints.chat import chat_endpoint, chat_stream_post_endpoint, chat_stream_endpoint
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.schemas.health import HealthResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialisation au demarrage et nettoyage a l arret."""
    print("[START] Demarrage de AGRIBurundi-AI / Imarika API...")
    # Initialisation de la base SQLite
    init_db()
    print("[OK] SQLite initialise avec succes.")
    yield
    print("[STOP] Arret de AGRIBurundi-AI / Imarika API.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuration CORS pour autoriser le frontend React (ports 3000, 5173, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montage du routeur v1 sous le prefixe /api/v1
app.include_router(api_v1_router, prefix="/api/v1")

# Interface web statique (une seule page : login + chat)
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", tags=["System"])
    async def index():
        """Page d'accueil : interface de chat avec connexion."""
        return FileResponse(str(STATIC_DIR / "index.html"))

# Route de sante a la racine /health (pour les monitoring tools et frontend)
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def root_health_check():
    """Verification de sante du systeme a la racine /health."""
    return await health_check()

# Compatibilite directe pour /api/chat (en plus de /api/v1/chat)
@app.post("/api/chat", response_model=ChatResponse, tags=["Chat (Compat)"])
async def legacy_chat_endpoint(request: ChatRequest, http_request: Request):
    """Route de compatibilite directe /api/chat."""
    return await chat_endpoint(request, user=get_current_user(http_request))

@app.post("/api/chat/stream", tags=["Chat (Compat)"])
async def legacy_chat_stream_post(request: ChatRequest, http_request: Request):
    """Route de compatibilite streaming POST /api/chat/stream."""
    return await chat_stream_post_endpoint(request, user=get_current_user(http_request))

@app.get("/api/chat/stream", tags=["Chat (Compat)"])
async def legacy_chat_stream_get(message: str, conversation_id: str = None, http_request: Request = None):
    """Route de compatibilite streaming GET /api/chat/stream."""
    return await chat_stream_endpoint(
        message=message,
        conversation_id=conversation_id,
        user=get_current_user(http_request) if http_request else None,
    )

@app.get("/api", tags=["System"])
async def root():
    """Accueil de l API (JSON)."""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "model": settings.OLLAMA_MODEL,
        "docs": "/docs",
        "interface": "/",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=False)
