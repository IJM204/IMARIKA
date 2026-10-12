# 🚀 Guide de démarrage rapide — Imarika / AGRIBurundi-AI

> Assistant agricole burundais — **Ollama** (moteur local) + **FastAPI** + interface web intégrée.

## Prérequis

- [ ] Python 3.10+
- [ ] Ollama installé **et lancé**
- [ ] Modèle léger téléchargé : `qwen3:1.7b` (1,4 Go — adapté aux machines 8 Go de RAM)

## Installation (1 minute)

```bash
# 1. Dépendances Python
pip install -r requirements.txt

# 2. Vérifier / lancer Ollama
ollama serve          # (dans un terminal séparé, si pas déjà lancé)
ollama pull qwen3:1.7b

# 3. Démarrer Imarika
python run.py
```

Puis ouvrez : **http://localhost:8000**

## Ce que vous obtenez

| URL | Rôle |
|---|---|
| http://localhost:8000 | **Interface web** (connexion + chat) |
| http://localhost:8000/docs | Documentation interactive de l'API |
| http://localhost:8000/health | État du backend et d'Ollama |

1. **Créez un compte** (nom d'utilisateur + mot de passe) au premier lancement.
2. Posez vos questions — en français, kirundi ou kiswahili.
3. L'historique est **privé** : chaque utilisateur ne voit que ses conversations.

### Exemples de questions

- 🌱 « Quand semer le maïs en Saison A ? »
- 🧪 « Comment fertiliser le haricot ? »
- 🐛 « Quels ravageurs attaquent le manioc ? »
- 👋 « Bonjour », « merci », « aide » → réponses **instantanées** (sans modèle)

## Commandes

```bash
python run.py           # API + interface web (mode léger, DÉFAUT)
python run.py legacy    # ancienne interface Streamlit (LOURD — déconseillé)
python run.py test      # suite de tests pytest
python run.py build-kg  # reconstruire le graphe de connaissances
python run.py help      # aide
```

## Optimisation mémoire (important sur 8 Go de RAM)

Réglages dans `backend/core/config.py` :

| Variable | Défaut | Effet |
|---|---|---|
| `OLLAMA_MODEL` | `qwen3:1.7b` | Changer de modèle ici (un seul endroit) |
| `OLLAMA_KEEP_ALIVE` | `"2m"` | Durée du modèle en RAM après réponse |
| `OLLAMA_NUM_CTX` | `2048` | Fenêtre de contexte (↓ = ↓ RAM) |
| `OLLAMA_NUM_THREAD` | `4` | Threads CPU |

⚠️ **Ne pas utiliser `llama3` (4,7 Go)** sur une machine 8 Go : c'est la cause
historique du plantage. `qwen3:4b` (~3,5 Go) est également déconseillé ici.

## Tests

```bash
pip install pytest
python -m pytest -m fast     # tests rapides (aucun appel à Ollama, ~30 s)
python -m pytest             # tous les tests (les tests Ollama prennent plusieurs minutes)
```

## Dépannage

**« Ollama est indisponible »** dans l'interface (badge 🟠) :
```bash
ollama serve        # démarrer le service
ollama list         # vérifier que qwen3:1.7b est présent
```

**Port 8000 déjà utilisé** :
```bash
# Changer de port dans backend/core/config.py  ->  PORT: int = 8001
```

**Première réponse lente** : normal sur CPU (~60-90 s). Les salutations
(« bonjour ») sont répondues instantanément et ne chargent pas le modèle.

**Météo** (optionnel) : clé API OpenWeatherMap dans `.env`
(voir `.env.example`).
