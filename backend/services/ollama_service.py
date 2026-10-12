"""
Service Ollama HTTP natif pour AGRIBurundi-AI / Imarika.
Utilise l'API REST d'Ollama directement via httpx asynchrone.
Plus de subprocess.run(["ollama", "run", ...])
"""

import httpx
import json
import asyncio
from typing import AsyncIterator, Optional, Dict, Any, List
from pathlib import Path
import sys

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from backend.core.config import settings


class OllamaService:
    """
    Client HTTP asynchrone pour interagir avec Ollama local.
    Supporte la génération standard et le streaming SSE.
    """

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        # Sejour du modele en RAM apres la derniere requete (voir config.py).
        # 15m maintenait ~2 Go bloques inutilement sur une machine 8 Go.
        self.keep_alive = settings.OLLAMA_KEEP_ALIVE
        self.num_ctx = settings.OLLAMA_NUM_CTX
        self.num_thread = settings.OLLAMA_NUM_THREAD

    def _options(self, temperature: float, num_predict: int) -> Dict[str, Any]:
        """Options Ollama communes, limitees en memoire."""
        return {
            "temperature": temperature,
            "num_predict": num_predict,
            "top_k": 20,
            "top_p": 0.85,
            "repeat_penalty": 1.1,
            "num_ctx": self.num_ctx,
            "num_thread": self.num_thread,
        }

    # ------------------------------------------------------------------ #
    #  Verification systeme                                                #
    # ------------------------------------------------------------------ #

    async def is_ollama_available(self) -> bool:
        """Verifie que le daemon Ollama repond."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    async def is_model_available(self, model: Optional[str] = None) -> bool:
        """Verifie que le modele cible est present dans Ollama."""
        target = model or self.model
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                if r.status_code != 200:
                    return False
                data = r.json()
                model_names = [m.get("name", "") for m in data.get("models", [])]
                # Accepter "llama3" et "llama3:latest" comme equivalents
                return any(
                    target == n or target.split(":")[0] == n.split(":")[0]
                    for n in model_names
                )
        except Exception:
            return False

    async def get_health_status(self) -> Dict[str, Any]:
        """Retourne un bilan complet de la disponibilite Ollama + modele."""
        ollama_ok = await self.is_ollama_available()
        model_ok = await self.is_model_available() if ollama_ok else False
        return {
            "ollama_online": ollama_ok,
            "model_available": model_ok,
            "model_name": self.model,
        }

    # ------------------------------------------------------------------ #
    #  Generation standard (reponse complete)                              #
    # ------------------------------------------------------------------ #

    # ------------------------------------------------------------------ #
    #  Generation standard (reponse complete)                              #
    # ------------------------------------------------------------------ #

    async def chat(
        self,
        history: List[dict],
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        num_predict: int = 256,
    ) -> str:
        """Envoie une conversation multi-tours (messages role/content) a
        Ollama /api/chat et retourne la reponse complete.
        `history` contient deja la question utilisateur courante en dernier."""
        target_model = model or self.model
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.extend(history)

        payload = {
            "model": target_model,
            "messages": messages,
            "stream": False,
            "think": False,
            "keep_alive": self.keep_alive,
            "options": self._options(temperature, num_predict),
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                content = data.get("message", {}).get("content", "")
                return content.strip()
        except Exception as e:
            raise RuntimeError(f"Erreur de communication avec Ollama: {str(e)}")

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        num_predict: int = 256,
    ) -> str:
        """
        Envoie un prompt a Ollama via /api/chat et retourne la reponse complete.
        Utilise think=False pour eviter les blocs de reflexion prolonges (ex: Qwen3).
        """
        target_model = model or self.model
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": target_model,
            "messages": messages,
            "stream": False,
            "think": False,
            "keep_alive": self.keep_alive,
            "options": self._options(temperature, num_predict),
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                content = data.get("message", {}).get("content", "")
                if not content:
                    content = data.get("response", "")
                return content.strip()
        except httpx.TimeoutException:
            raise RuntimeError(
                f"Le modele {target_model} n'a pas repondu dans le delai imparti "
                f"({self.timeout}s). Ollama est lent sur CPU — c'est normal au premier appel."
            )
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Erreur HTTP Ollama: {e.response.status_code} — {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Erreur de communication avec Ollama: {str(e)}")

    # ------------------------------------------------------------------ #
    #  Streaming (Server-Sent Events)                                      #
    # ------------------------------------------------------------------ #

    async def stream_chat(
        self,
        history: List[dict],
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        num_predict: int = 256,
    ) -> AsyncIterator[str]:
        """Version streaming multi-tours de `chat` : yielde les tokens au fur
        et a mesure. `history` contient la question courante en dernier."""
        target_model = model or self.model
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.extend(history)

        payload = {
            "model": target_model,
            "messages": messages,
            "stream": True,
            "think": False,
            "keep_alive": self.keep_alive,
            "options": self._options(temperature, num_predict),
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            token = chunk.get("message", {}).get("content", "")
                            if token:
                                yield token
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.TimeoutException:
            yield "\n\n[Délai dépassé — le modèle charge lentement sur CPU. Réessayez dans quelques secondes.]"
        except Exception as e:
            yield f"\n\n[Erreur Ollama: {str(e)}]"

    async def stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        num_predict: int = 256,
    ) -> AsyncIterator[str]:
        """
        Generateur asynchrone qui yielde chaque token au fur et a mesure.
        Utilise POST /api/chat avec stream=True et think=False.
        """
        target_model = model or self.model
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": target_model,
            "messages": messages,
            "stream": True,
            "think": False,
            "keep_alive": self.keep_alive,
            "options": self._options(temperature, num_predict),
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            token = chunk.get("message", {}).get("content", "")
                            if not token:
                                token = chunk.get("response", "")
                            if token:
                                yield token
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.TimeoutException:
            yield "\n\n[Délai dépassé — le modèle charge lentement sur CPU. Réessayez dans quelques secondes.]"
        except Exception as e:
            yield f"\n\n[Erreur Ollama: {str(e)}]"


# Singleton global
ollama_service = OllamaService()
