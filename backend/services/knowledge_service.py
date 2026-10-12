"""
Knowledge Service — pont Question (FR) -> donnees CSV (EN).

Principe :
    Question francaise
      -> detection des concepts agricoles (synonymes FR)
      -> traduction de chaque concept vers le vocabulaire EN reels des CSV
      -> scoring des lignes de data/<culture>.csv
      -> contexte agronomique injecte dans le prompt de Qwen3

Le vocabulaire anglais de CONCEPTS n'est pas invente : il est extrait des CSV
(Growth Stages / Farming Activities / conditions), d'ou l'association :
    fertilisation -> fertilizer, nutrient management, manure, npk, dap...
    semis         -> sowing, planting, seed, spacing, germination...
    ravageurs     -> pest, insects, weevil, control, pathogen...
    maladies      -> disease, pathogen, infestation...
    rendement     -> yield, production, growth, optimal...
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

import pandas as pd

from backend.core.config import settings
from ai.knowledge.burundi_agri_context import (
    BURUNDI_SEASONS,
    BURUNDI_REGIONS,
    BURUNDI_FERTILIZATION_PRACTICES,
)

# --- Colonnes CSV (certains fichiers ont des coquilles, ex: "Groth Stages") ---
STAGE_COLUMN = "Growth Stages"
ACTIVITY_COLUMN = "Farming Activities"
IDEAL_COLUMN = "Normal Conditions (ideal condition)"
WET_COLUMN = "Wetter than Normal (Higher than ideal)"
DRY_COLUMN = "Drier than Normal (Lower than Ideal)"
COLUMN_ALIASES = {
    "Groth Stages": STAGE_COLUMN,
    "Grow Stages": STAGE_COLUMN,
    "Growth Stage": STAGE_COLUMN,
}

# --- Dictionnaire FR -> EN ancre sur le vocabulaire reel des CSV -------------
# "fr" : termes recherches dans la question de l'utilisateur (declencheurs)
# "en" : termes recherches dans les lignes de CSV (produisent le score)
CONCEPTS: Dict[str, Dict[str, List[str]]] = {
    "fertilisation": {
        "fr": [
            "fertilis", "engrais", "fumier", "compost", "amend", "nutriment",
            "nutrition", "npk", "dap", "urée", "uree", "mbolea", "fomi",
            "chaux", "dolomie", "fertilizer",
        ],
        "en": [
            "fertiliz", "fertilizer", "nutrient", "manure", "compost",
            "nitrogen", "phosphorous", "potassium", "npk", "dap", "urea",
            "potash", "soil test", "soil test", "ph",
        ],
    },
    "semis": {
        "fr": [
            "semis", "semer", "semai", "semenc", "plantation", "planter",
            "planté", "germin", "espacement", "eclaire", "éclaire", "trou",
        ],
        "en": [
            "sow", "sowing", "planting", "plant", "seed", "germination",
            "spacing", "depth", "emergence", "onset of rain", "rainfall",
        ],
    },
    "ravageurs": {
        "fr": [
            "ravageur", "parasite", "insecte", "chenille", "charançon",
            "charancon", "termite", "sujetion", "punaise",
        ],
        "en": [
            "pest", "insect", "weevil", "aflatoxin", "infestation",
            "control", "attack", "pathogen",
        ],
    },
    "maladies": {
        "fr": [
            "maladie", "fongique", "cryptogamique", "pourriture", "rouille",
            "anthracnose", "mildiou", "bacteri", "virus", "moisiss",
        ],
        "en": [
            "disease", "pathogen", "infection", "infestation", "mold",
            "fung", "bacteria",
        ],
    },
    "rendement": {
        "fr": ["rendement", "productivite", "productivité", "production", "performance"],
        "en": ["yield", "production", "growth", "optimal", "maturity"],
    },
    "recolte": {
        "fr": ["récolte", "recolte", "moisson", "stockage", "conservation", "sechage", "séchage"],
        "en": ["harvest", "maturity", "storage", "store", "dry", "drying", "shelling", "winnow"],
    },
    "sol_eau": {
        "fr": ["sol", "sols", "eau", "pluie", "irrigation", "secheresse", "sécheresse", "drainage", "humidite", "humidité", "arrosage"],
        "en": ["soil", "water", "rain", "rainfall", "irrigation", "drainage", "drought", "moisture", "tillage"],
    },
}


def _term_matches(term: str, text: str) -> bool:
    """
    Recherche un terme dans un texte.
    - termes courts (<=4) : debut de mot, pour matcher les derivés
      ("sow" -> "sowing", "pest" -> "pests", "npk" -> "npk")
    - termes longs : sous-chaîne (matche les pluriels et flexions)
    """
    if not term or not text:
        return False
    if len(term) <= 4:
        return re.search(r"\b" + re.escape(term), text) is not None
    return term in text


# Mots outils FR/EN : jamais recherches dans les CSV.
# Sans cette liste, "est" matche "estim-ating" et une question generale
# (capitale, meteo...) recolte un faux contexte agricole.
QUERY_STOPWORDS = {
    # francais
    "est", "sont", "etait", "quel", "quelle", "quels", "quelles", "comment",
    "combien", "pour", "dans", "avec", "sans", "que", "qui", "quoi", "dont",
    "une", "des", "les", "aux", "cette", "ces", "comme", "selon", "entre",
    "vers", "chez", "donc", "mais", "encore", "deja", "aussi", "tous", "tout",
    "toute", "meme", "leur", "leurs", "plus", "tres", "bien", "peut", "peux",
    "faire", "fait", "doit", "dois", "quand", "pourquoi", "vous", "nous",
    # anglais
    "the", "and", "for", "with", "how", "what", "when", "where", "why", "are",
    "was", "were", "this", "that", "from", "into", "about", "should", "would",
    "could", "can", "does", "doing", "your", "their", "from", "than", "then",
}


class KnowledgeService:
    def __init__(self):
        self.data_dir = Path(settings.DATA_DIR)
        self.crop_mappings = {
            "maize": ["maïs", "mais", "maize", "corn", "ibigori", "kigori", "mahindi"],
            "beans": ["haricot", "haricots", "bean", "beans", "ibiharage", "igiharage", "maharage"],
            "cassava": ["manioc", "cassava", "imyumbati", "umwumbati", "mihogo"],
            "sorghum": ["sorgho", "sorghum", "amasaka", "isaka", "mtama"],
            "finger_millet": ["éleusine", "eleusine", "finger millet", "millet", "uburimbwe", "ulezi"],
            "sweet_potatoes": ["patate douce", "patates douces", "sweet potato", "sweet potatoes", "ibijumbu", "viazi vitamu"],
        }
        self.concepts = CONCEPTS
        self.crop_dfs = {}
        self._load_datasets()

    # ------------------------------------------------------------------ #
    #  Chargement des donnees                                              #
    # ------------------------------------------------------------------ #

    def _load_datasets(self) -> None:
        """Charge chaque CSV de culture en normalisant les noms de colonnes."""
        for crop_key in self.crop_mappings.keys():
            csv_path = self.data_dir / f"{crop_key}.csv"
            if not csv_path.exists():
                continue
            try:
                df = pd.read_csv(csv_path)
                df.columns = [COLUMN_ALIASES.get(str(c).strip(), str(c).strip()) for c in df.columns]
                self.crop_dfs[crop_key] = df
            except Exception as e:
                print(f"Warning: Could not load {csv_path}: {e}")

    # ------------------------------------------------------------------ #
    #  Detection dans la question                                          #
    # ------------------------------------------------------------------ #

    def identify_crops(self, query: str) -> List[str]:
        """Identifies target crops from query keywords across languages."""
        query_lower = query.lower()
        matched_crops = []
        for crop_key, keywords in self.crop_mappings.items():
            if any(kw in query_lower for kw in keywords):
                matched_crops.append(crop_key)
        return matched_crops

    def identify_burundi_regions(self, query: str) -> List[str]:
        """Identifies mentioned Burundi regions or provinces."""
        query_lower = query.lower()
        matched = []
        for region_name, data in BURUNDI_REGIONS.items():
            if region_name.lower() in query_lower:
                matched.append(region_name)
                continue
            for prov in data.get("provinces", []):
                clean_prov = prov.split("(")[0].strip().lower()
                if clean_prov and clean_prov in query_lower:
                    matched.append(region_name)
                    break
        return list(set(matched))

    def identify_seasons(self, query: str) -> List[str]:
        """Identifies mentioned cultural seasons."""
        query_lower = query.lower()
        matched = []
        for season_name in BURUNDI_SEASONS.keys():
            if "saison a" in query_lower or "impeshi" in query_lower or "agasasi" in query_lower:
                if "Saison A" in season_name:
                    matched.append(season_name)
            if "saison b" in query_lower or "urugaryi" in query_lower:
                if "Saison B" in season_name:
                    matched.append(season_name)
            if "saison c" in query_lower or "marais" in query_lower or re.search(
                r"\bici\b", query_lower
            ):
                if "Saison C" in season_name:
                    matched.append(season_name)
        return list(set(matched))

    def detect_concepts(self, query: str) -> List[str]:
        """
        Retourne les concepts agricoles presents dans la question.
        Ex: "Comment fertiliser le maïs ?" -> ["fertilisation"]
        """
        query_lower = query.lower()
        detected = []
        for concept, definition in self.concepts.items():
            for trigger in definition["fr"]:
                trigger_lower = trigger.lower()
                if len(trigger_lower) <= 4:
                    # termes courts : mot entier pour eviter "sol" dans "solution"
                    if re.search(r"\b" + re.escape(trigger_lower), query_lower):
                        detected.append(concept)
                        break
                elif trigger_lower in query_lower:
                    detected.append(concept)
                    break
        return detected

    def _expand_query_terms(self, query: str, concepts: List[str]) -> List[str]:
        """
        Construit la liste des termes recherches dans les CSV :
        mots de la question (hors mots outils) + termes anglais des concepts
        detectes + synonymes FR des concepts (utiles pour les colonnes Swahili).
        """
        terms = {
            w.strip("'?«».,!()()")
            for w in query.lower().split()
            if len(w.strip("'?«».,!()()")) > 2
            and w.strip("'?«».,!()()") not in QUERY_STOPWORDS
        }
        for concept in concepts:
            terms.update(t.lower() for t in self.concepts[concept]["en"])
            terms.update(t.lower() for t in self.concepts[concept]["fr"] if len(t) > 2)
        return sorted(terms)

    # ------------------------------------------------------------------ #
    #  Scoring des lignes CSV                                              #
    # ------------------------------------------------------------------ #

    def _score_row(self, row_text: str, activity: str, stage: str, terms: List[str]) -> Tuple[int, List[str]]:
        """
        Score d'une ligne : +3 sur l'activite (Farming Activities),
        +2 sur le stade (Growth Stages), +1 sur le reste des colonnes.
        """
        activity_l = (activity or "").lower()
        stage_l = (stage or "").lower()
        score = 0
        matched: List[str] = []
        for term in terms:
            if _term_matches(term, activity_l):
                score += 3
                matched.append(term)
            elif _term_matches(term, stage_l):
                score += 2
                matched.append(term)
            elif _term_matches(term, row_text):
                score += 1
                matched.append(term)
        return score, matched

    @staticmethod
    def _build_chunk(crop_name: str, activity: str, stage: str, ideal: str, wet: str, dry: str) -> str:
        chunk = f"Culture : {crop_name} | Activité : {activity.strip()} (Stade : {stage.strip()})"
        ideal = "" if ideal is None else str(ideal)
        wet = "" if wet is None else str(wet)
        dry = "" if dry is None else str(dry)
        if ideal and ideal.lower() != "nan" and len(ideal.strip()) > 5:
            chunk += f"\n- Pratiques recommandées : {ideal.strip()[:400]}"
        if wet.lower() != "nan" and len(wet.strip()) > 10:
            chunk += f"\n- Si excès d'humidité : {wet.strip()[:200]}"
        if dry.lower() != "nan" and len(dry.strip()) > 10:
            chunk += f"\n- Si déficit hydrique : {dry.strip()[:200]}"
        return chunk

    # ------------------------------------------------------------------ #
    #  API principale                                                      #
    # ------------------------------------------------------------------ #

    def retrieve_context(self, query: str) -> Dict[str, Any]:
        """Retrieves structured agronomic context relevant to the user query."""
        detected_crops = self.identify_crops(query)
        detected_regions = self.identify_burundi_regions(query)
        detected_seasons = self.identify_seasons(query)
        detected_concepts = self.detect_concepts(query)
        expanded_terms = self._expand_query_terms(query, detected_concepts)

        # Culture(s) a interroger : celles citees, sinon toutes les cultures
        # (permet de repondre aux questions generales : "ravageurs", "maladies"...)
        crops_to_search = [c for c in detected_crops if c in self.crop_dfs]
        if not crops_to_search:
            crops_to_search = list(self.crop_dfs.keys())

        # Question sans aucun signal agronomique (ni culture, ni concept, ni
        # region, ni saison) : c'est une question GENERALE. On ne renvoie ni
        # contexte CSV ni contexte regional — le modele repond alors de lui-meme.
        if not (detected_crops or detected_concepts or detected_regions or detected_seasons):
            return {
                "crops": [],
                "regions": [],
                "seasons": [],
                "concepts": [],
                "context_chunks": [],
                "regional_info": "",
            }

        candidates: List[Dict[str, Any]] = []
        for crop in crops_to_search:
            df = self.crop_dfs[crop]
            crop_name = crop.replace("_", " ").title()
            for _, row in df.iterrows():
                activity = str(row.get(ACTIVITY_COLUMN, "") or "")
                stage = str(row.get(STAGE_COLUMN, "") or "")
                row_text = " ".join(str(row.get(c, "")) for c in df.columns).lower()
                score, matched = self._score_row(row_text, activity, stage, expanded_terms)
                if score <= 0:
                    continue
                candidates.append(
                    {
                        "crop": crop,
                        "crop_name": crop_name,
                        "score": score,
                        "matched": matched,
                        "activity": activity,
                        "stage": stage,
                        "ideal": row.get(IDEAL_COLUMN, ""),
                        "wet": row.get(WET_COLUMN, ""),
                        "dry": row.get(DRY_COLUMN, ""),
                    }
                )

        # Tri : score decroissant, puis les lignes d'activite les plus ciblees
        candidates.sort(key=lambda c: c["score"], reverse=True)

        # Si la culture est connue mais qu'aucun terme ne matche, on renvoie
        # quand meme les deux etapes structurantes de la culture (contexte par
        # defaut) plutot que rien : la question porte sur cette culture.
        if not candidates and detected_crops:
            default_activities = ["Nutrient Management", "Sowing"]
            for crop in crops_to_search:
                df = self.crop_dfs[crop]
                crop_name = crop.replace("_", " ").title()
                for _, row in df.iterrows():
                    if str(row.get(ACTIVITY_COLUMN, "")).strip() not in default_activities:
                        continue
                    candidates.append(
                        {
                            "crop": crop,
                            "crop_name": crop_name,
                            "score": 0,
                            "matched": [],
                            "activity": str(row.get(ACTIVITY_COLUMN, "")),
                            "stage": str(row.get(STAGE_COLUMN, "")),
                            "ideal": row.get(IDEAL_COLUMN, ""),
                            "wet": row.get(WET_COLUMN, ""),
                            "dry": row.get(DRY_COLUMN, ""),
                        }
                    )

        # Selection : 3 lignes par culture si culture citee, sinon 4 lignes
        # globales (question generale portant sur plusieurs cultures).
        selected: List[Dict[str, Any]] = []
        if detected_crops:
            per_crop: Dict[str, int] = {}
            for cand in candidates:
                count = per_crop.get(cand["crop"], 0)
                if count >= 3:
                    continue
                per_crop[cand["crop"]] = count + 1
                selected.append(cand)
                if len(selected) >= 6:
                    break
        else:
            # Question generale : on evite que les 4 lignes soient toutes la
            # meme activite (ex: Post Harvest) en limitant a 2 lignes par activite.
            per_activity: Dict[str, int] = {}
            for cand in candidates:
                key = str(cand["activity"]).strip()
                if per_activity.get(key, 0) >= 2:
                    continue
                per_activity[key] = per_activity.get(key, 0) + 1
                selected.append(cand)
                if len(selected) >= 4:
                    break

        context_chunks = [
            self._build_chunk(
                cand["crop_name"], cand["activity"], cand["stage"],
                cand["ideal"], cand["wet"], cand["dry"],
            )
            for cand in selected
        ]

        # Contexte regional / saisonnier / fertilisation burundaise
        regional_info: List[str] = []
        for reg in detected_regions:
            reg_data = BURUNDI_REGIONS.get(reg, {})
            regional_info.append(
                f"Région {reg} (Alt: {reg_data.get('altitude')}) : Climat {reg_data.get('climat')}. "
                f"Cultures dominantes : {', '.join(reg_data.get('cultures', []))}."
            )

        for s in detected_seasons:
            s_data = BURUNDI_SEASONS.get(s, {})
            regional_info.append(
                f"{s} ({s_data.get('periode')}) : {s_data.get('recommandations')}"
            )

        if "fertilisation" in detected_concepts:
            regional_info.append(BURUNDI_FERTILIZATION_PRACTICES.strip())

        return {
            "crops": detected_crops,
            "regions": detected_regions,
            "seasons": detected_seasons,
            "concepts": detected_concepts,
            "context_chunks": context_chunks,
            "regional_info": "\n".join(regional_info),
        }


knowledge_service = KnowledgeService()
