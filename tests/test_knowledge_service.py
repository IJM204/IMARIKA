"""
Tests unitaires du Knowledge Service — mapping Français -> CSV anglais.

Objectif : une question formulee en francais doit produire un contexte agronomique
NON VIDE issu des CSV (data/<culture>.csv), contenant de vraies informations.

Ces tests echouent si le mapping FR -> concepts anglais est absent ou casse.

Execution :
    python -m pytest tests/test_knowledge_service.py -v
    python tests/test_knowledge_service.py        (mode script)
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.knowledge_service import knowledge_service

pytestmark = pytest.mark.fast

# question -> culture attendue (None = aucune culture imposee) + termes anglais
# qui DOIVENT apparaitre dans le contexte retourne (vocabulaire reel des CSV).
CASES = [
    {
        "question": "Comment fertiliser le maïs ?",
        "crop": "maize",
        "crop_label": "Maize",
        "expected_terms": ["fertiliz", "nutrient", "manure", "npk", "dap", "nitrogen", "compost"],
        "min_hits": 2,
    },
    {
        "question": "Comment semer le haricot ?",
        "crop": "beans",
        "crop_label": "Beans",
        "expected_terms": ["sow", "plant", "seed", "spacing", "germination"],
        "min_hits": 2,
    },
    {
        "question": "Quels sont les ravageurs ?",
        "crop": None,
        "crop_label": None,
        "expected_terms": ["pest", "insect", "weevil", "control", "disease", "pathogen"],
        "min_hits": 2,
    },
    {
        "question": "Comment améliorer le rendement du maïs ?",
        "crop": "maize",
        "crop_label": "Maize",
        "expected_terms": ["yield", "growth", "production", "optimal", "crop"],
        "min_hits": 2,
    },
]


def _context_text(result: dict) -> str:
    return "\n".join(result.get("context_chunks", [])).lower()


def _run(case: dict) -> dict:
    return knowledge_service.retrieve_context(case["question"])


def test_contexte_non_vide():
    """Les 4 questions francaises doivent retourner un contexte non vide."""
    empty = [c["question"] for c in CASES if not _run(c).get("context_chunks")]
    assert not empty, f"Contexte VIDE pour : {empty}"


def test_contexte_contient_une_ligne_csv_reelle():
    """Le contexte doit provenir d'une vraie ligne de CSV (Culture / Activite)."""
    for case in CASES:
        result = _run(case)
        chunks = result.get("context_chunks", [])
        assert chunks, f"Contexte vide pour : {case['question']}"
        joined = "\n".join(chunks)
        assert "Culture :" in joined and "Activité" in joined, (
            f"Le contexte de '{case['question']}' ne provient pas des CSV : {joined[:200]}"
        )


def test_contexte_pertinent_par_question():
    """Chaque question doit retrouver des concepts anglais reels des CSV."""
    for case in CASES:
        result = _run(case)
        text = _context_text(result)
        assert text.strip(), f"Contexte vide pour : {case['question']}"
        hits = [t for t in case["expected_terms"] if t in text]
        assert len(hits) >= case["min_hits"], (
            f"'{case['question']}' : termes pertinents introuvables "
            f"(attendu parmi {case['expected_terms']}, trouve {hits}) dans :\n{text[:400]}"
        )


def test_culture_identifiee():
    """La culture citee en francais doit etre detectee (maïs -> maize, haricot -> beans)."""
    for case in CASES:
        if not case["crop"]:
            continue
        result = _run(case)
        assert case["crop"] in result.get("crops", []), (
            f"Culture non detectee pour '{case['question']}' : {result.get('crops')}"
        )
        text = _context_text(result)
        assert case["crop_label"].lower() in text, (
            f"Le contexte de '{case['question']}' ne mentionne pas {case['crop_label']}"
        )


def test_fertilisation_declenche_contexte_regional_burundi():
    """Une question sur la fertilisation doit ajouter les pratiques burundaises (FOMI...)."""
    result = knowledge_service.retrieve_context("Comment fertiliser le maïs ?")
    regional = result.get("regional_info", "")
    assert "fomi" in regional.lower(), (
        f"Contexte regional burundais absent pour une question de fertilisation : '{regional[:200]}'"
    )


def test_requete_inconnue_ne_provoque_pas_d_exception():
    """Une question hors domaine (hors agriculture) ne doit rien faire planter."""
    result = knowledge_service.retrieve_context("Recette de cuisine au chocolat ?")
    assert isinstance(result, dict)
    # Contexte vide accepte : l'important est l'absence d'exception et de crash.
    assert isinstance(result.get("context_chunks", []), list)
    assert not result.get("context_chunks"), (
        "Une requete hors domaine ne doit pas retourner de faux contexte agricole"
    )


if __name__ == "__main__":
    failures = 0
    for fn in [
        test_contexte_non_vide,
        test_contexte_contient_une_ligne_csv_reelle,
        test_contexte_pertinent_par_question,
        test_culture_identifiee,
        test_fertilisation_declenche_contexte_regional_burundi,
        test_requete_inconnue_ne_provoque_pas_d_exception,
    ]:
        try:
            fn()
            print(f"[PASS] {fn.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"[FAIL] {fn.__name__}\n       {exc}")
    print(f"\n{failures} echec(s)")
    sys.exit(1 if failures else 0)
