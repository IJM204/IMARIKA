import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute paths
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATA_DIR = ROOT_DIR / "data"

class Settings(BaseSettings):
    PROJECT_NAME: str = "AGRIBurundi-AI / Imarika"
    VERSION: str = "2.0.0"
    DESCRIPTION: str = "Assistant conversationnel agricole spécialisé pour le Burundi"
    
    # Project paths
    PROJECT_ROOT: Path = ROOT_DIR
    DATA_DIR: Path = DEFAULT_DATA_DIR
    
    # Ollama Local Configuration
    # --- Choix du modele (machine : Pentium 4405U 2C/4T, 7,9 Go RAM) --------
    # qwen3:1.7b  -> 1,4 Go disque, ~2 Go RAM, multilingue (fr/sw/en) : OK
    # qwen3:4b    -> ~3,5 Go RAM : DECONSEILLE ici (4 Go libres max)
    # llama3:8b   -> 4,7 Go RAM : provoque le plantage de la machine
    # Pour changer de modele, modifier cette seule variable.
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:1.7b"
    OLLAMA_TIMEOUT: int = 300

    # --- Garde-fous memoire (evite le plantage) -----------------------------
    # Duree de sejour du modele en RAM apres la derniere requete.
    # "2m" = libere ~2 Go rapidement ; "0" = dechargement immediate (premiere
    # reponse plus lente au debut).
    OLLAMA_KEEP_ALIVE: str = "2m"
    # Fenetre de contexte. 2048 tokens suffisent pour des reponses courtes et
    # divise nettement la consommation RAM (defaut Ollama: 4096 ou 8192).
    OLLAMA_NUM_CTX: int = 2048
    # Nombre de threads CPU = 4 threads logiques disponibles.
    OLLAMA_NUM_THREAD: int = 4

    # Budget de tokens pour une reponse de chat (CPU: ~1,6 token/s).
    # 140 tokens ≈ 90 s en chaud — la concision est garantie par le prompt,
    # et chat_service._finish_sentence() coupe proprement a la phrase complete.
    CHAT_MAX_TOKENS: int = 140
    
    # Database
    DATABASE_PATH: str = str(DEFAULT_DATA_DIR / "imarika.db")
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
    
    # Default language
    DEFAULT_LANGUAGE: str = "fr"
    APP_ENV: str = "development"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        arbitrary_types_allowed=True,
    )

settings = Settings()
