# Image officielle Python légère
FROM python:3.12-slim-bookworm

# Répertoire de travail
WORKDIR /app

# Variables d'environnement pour Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source du projet
COPY . .

# Création du dossier data si inexistant
RUN mkdir -p /app/data

# Port de l'API FastAPI et de l'interface web
EXPOSE 8000

# Commande de lancement FastAPI (mode léger et performant)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
