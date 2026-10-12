"""
Reponses rapides hors-LLM pour Imarika.

Certaines questions ("bonjour", "merci", "qui es-tu"...) n'ont pas besoin du
modele : elles sont reconnues ici et repondues INSTANTANEMENT, sans appel a
Ollama (0 Go de RAM, 0 seconde d'attente). L'utilisateur evite donc d'attendre
90 s de generation pour un "bonjour".

Toute question non reconnue ici part normalement vers le modele + la base de
connaissances agronomiques.
"""

import re
import unicodedata
from typing import Dict, List, Optional, Tuple


def _normalize(text: str) -> str:
    """Minuscules + suppression des accents : "Bonjour" == "bonjour" == "bonjour"."""
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text


# ------------------------------------------------------------------ #
#  Regles : (motifs reconnus, reponse)                                #
#  Un motif est une expression reguliere testee sur le texte normalise#
# ------------------------------------------------------------------ #

_RULES: List[Tuple[List[str], str]] = [
    # --- Salutations -------------------------------------------------- #
    (
        [r"^(bonjour|bonsoir|salut|coucou|hey|hello|hi|yo|bonne journée|bonne journee)\b"],
        "Bonjour ! Je suis Imarika, votre assistant agricole.\n"
        "Exemples de questions :\n"
        "- Quand semer le maïs en Saison A ?\n"
        "- Comment fertiliser le haricot ?\n"
        "- Quels ravageurs attaquent le manioc ?",
    ),
    (
        [r"^(muraho|murakaza|wote|maramuke|mwaramutse)\b"],
        "Muraho ! Ndi Imarika, umufasha mu bw'ubuntu.\n"
        "Ushobora kubuza: \"Reka nseme ibigori mu Karindime?\" "
        "cyangwa \"Nigute nongere umwanya?\"",
    ),
    (
        [r"^(habari|habari yako|habari za asubuhi|shikamoo|jambo)\b"],
        "Habari! Mimi ni Imarika, msaidizi wako wa kilimo.\n"
        "Unaweza kuuliza: \"Nipatie ratiba ya kupanda mahindi\" "
        "au \"Jinsi ya kumwagilia maharagwe\".",
    ),
    # --- Remerciements ------------------------------------------------ #
    (
        [r"\b(merci|merci beaucoup|thanks|thank you|asante|murakoze|cyose murakoze)\b"],
        "Avec plaisir ! Revenez quand vous voulez, je suis là 24h/24. 🌾",
    ),
    # --- Présentation ------------------------------------------------- #
    (
        [r"(qui es[- ]tu|tu es qui|c.est quoi tu|presente[- ]toi|who are you|wewe nani|ni nani wewe|wowe ani|ndowe urengeranya)"],
        "Je suis Imarika, un assistant agricole burundais.\n"
        "Je donne des conseils sur : haricot, maïs, manioc, sorgho, "
        "éleusine (ulezi) et patate douce — semis, fertilisation, "
        "maladies, récolte — et je réponds aussi aux questions générales.",
    ),
    # --- État / fonctionnement ---------------------------------------- #
    (
        [r"(comment (ca|ça) va|comment allez[- ]tu|how are you|habari yako|uri gute|mwiri wanje)"],
        "Je vais bien, merci ! Et vous ?\n"
        "Comment puis-je vous aider aujourd'hui (agriculture ou autre) ?",
    ),
    # --- Capacités / aide --------------------------------------------- #
    (
        [r"^(aide|help|que peux[- ]tu faire|tes fonctions|comment ca marche|vous aidez|m'aider|m aider)\b"],
        "Je peux vous aider sur :\n"
        "- Agriculture : calendrier des semis, fertilisation, maladies, "
        "ravageurs, récolte, conservation (Burundi, 6 cultures).\n"
        "- Questions générales : santé, éducation, vie courante (réponses courtes).\n"
        "- Météo : demandez « météo Bujumbura ».\n"
        "Posez votre question en français, kirundi ou kiswahili.",
    ),
    # --- Au revoir ----------------------------------------------------- #
    (
        [r"^(au revoir|bye|goodbye|a bientot|à bientot|kwa heri|tungaaye|urongoye)\b"],
        "Au revoir et bonnes récoltes ! 🌾 Revenez quand vous voulez.",
    ),
]

# Reponse de repli si aucun motif specifique n'a matche mais que le message
# ressemble a une simple politesse (ex: "salut toi", "bonjour a tous").
_FALLBACK_POLITE = (
    "Bonjour ! Je suis Imarika, votre assistant agricole. "
    "Posez-moi une question sur vos cultures ou une question générale."
)


def detect(message: str) -> Optional[str]:
    """
    Retourne une reponse immediate si le message est une salutation /
    politesse / question de presentation, sinon None (-> LLM).
    """
    if not message or not message.strip():
        return None

    text = _normalize(message)

    # Messages trop courts pour etre une vraie question agronomique
    # (evite d'envoyer "ok", ":", "???" au modele).
    if len(text) <= 3 and not re.search(r"[a-z]{2}", text):
        return "Bonjour ! Comment puis-je vous aider ? 🌾"

    for patterns, reply in _RULES:
        for pattern in patterns:
            if re.search(pattern, text):
                return reply

    # Politesses au milieu d'une phrase : "bonjour, comment semer le mais ?"
    # -> on laisse le modele gerer (la question agronomique prime).
    return None


def is_general_question(message: str) -> bool:
    """
    Indique si une question est HORS agriculture (le prompt utilisateur
    n'ajoutera alors aucun contexte CSV : reponse libre du modele).
    Utilise par chat_service pour alléger le prompt.
    """
    if not message:
        return False
    text = _normalize(message)
    agri_markers = [
        "mais", "maïs", "haricot", "manioc", "sorgho", "patate", "millet",
        "eleusine", "ulezi", "culture", "semis", "semence", "fertilis",
        "engrais", "maladie", "ravageur", "rec", "rendement", "sol",
        "irrigation", "saison", "parcelle", "champ", "agric", "maraicher",
        "cassava", "beans", "maize", "sorghum", "harvest", "sow", "pest",
        "mahindi", "ibiharage", "imyumbati", "amasaka", "ibijumbu",
    ]
    return not any(m in text for m in agri_markers)
