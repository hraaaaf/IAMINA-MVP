"""
Classification de triage à 2 CLASSES pour TriageVitalMiddleware.

Casse le défaut critique actuel : _ALL_KEYWORDS fusionne tout et route TOUT vers
le template glycémie (SAMU + sucre + PLS). Conséquence : "bghit nmout" (idéation)
reçoit "mange du sucre et appelle les secours" — cliniquement faux et dangereux.

  CLASSE 1 — URGENCE GLYCÉMIQUE / PHYSIQUE   -> template glycémie (inchangé)
  CLASSE 2 — IDÉATION SUICIDAIRE / CRISE     -> template soutien (JAMAIS d'instructions glycémie)

Garde-fou linguistique délégué à safety.crisis (hyperbole + idéation) :
  "nmout 3la X" / "nmout men {jou3,d7k,3ya,...}" / "bnin ... nmout"  = HYPERBOLE  -> NONE
  "bghit nmout" / "ma b9itch baghi n3ich" SANS modificateur affectif = IDÉATION  -> CLASSE 2
  L'hyperbole est testée AVANT l'idéation : "bghit nmout men jou3" => NONE.

────────────────────────────────────────────────────────────────────────────
⚠️  CE MODULE EST UN FILET DÉTERMINISTE HAUTE-PRÉCISION, PAS UN DÉTECTEUR EXHAUSTIF.
    Les messages ambigus qui n'atteignent aucune classe (return NONE) DOIVENT
    continuer vers le flux normal. Pour un message émotionnel routé vers le LLM,
    injecter une consigne crise-aware (voir INTEGRATION NOTES en bas de fichier).
    Le filet attrape le certain ; le LLM rattrape l'ambigu. Ni l'un ni l'autre seul.

⚠️  LISTES POSITIVES DARIJA = AMORCE, PAS VÉRITÉ DE TERRAIN.
    À curer par un locuteur natif + revue clinique, idéalement sur corpus patients.
    (Auteur de l'amorce : assistant IA, non locuteur natif.)
────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import re
from enum import Enum

# Crisis-domain logic lives in safety.crisis — import for use and backward compat.
from safety.crisis import (
    CRISIS_RESOURCES,
    crisis_support_response,
    is_hyperbole,
    is_ideation,
)

__all__ = [
    "TriageClass",
    "classify",
    "crisis_support_response",
    "select_triage_response",
    "CRISIS_RESOURCES",
]


class TriageClass(str, Enum):
    NONE = "none"
    GLYCEMIC_EMERGENCY = "glycemic_emergency"
    SUICIDAL_IDEATION = "suicidal_ideation"


# ════════════════════════════════════════════════════════════════════════════
# CLASSE 1 — URGENCE GLYCÉMIQUE / PHYSIQUE
#   Fusionne tes _FR_CRITICAL / _DARIJA_CRITICAL / _ARABIC_CRITICAL *physiques*.
#   N'ajoute ici QUE des variantes orthographiques de termes physiques/glycémiques.
#   Ne JAMAIS mettre les idiomes de mort (mout/nmout) ici : ils sont gérés en Classe 2
#   via safety.crisis.
# ════════════════════════════════════════════════════════════════════════════
_GLYCEMIC_FR = frozenset({
    "perte de connaissance", "evanoui", "evanouie", "je vais m'evanouir",
    "convulsion", "convulsions", "je tremble", "tremblements", "malaise",
    "vertige", "vertiges", "confusion", "hypo severe", "coma", "inconscient",
    "inconsciente", "je vois flou", "sueurs froides",
})
_GLYCEMIC_DARIJA = frozenset({
    "ghadi ntih", "ghadi ntah", "kantih",
    "fqad l3ql", "fqdt l3ql", "tahwid", "kayrjraj", "kanrjef", "rj fou",
    "rajef", "ma kan7ml", "ma kan7mlch", "dwakht", "dayakht",
    "ma kanchoufch", "ma kanchouf walou",
})
_GLYCEMIC_ARABIC = frozenset({
    "فقدان الوعي", "غيبوبة", "إغماء", "اغماء", "تشنج", "تشنجات", "رعشة",
    "دوخة", "فقدت الوعي", "ما كنشوفش", "غادي نطيح",
})

# Proximité chiffre glycémique CRITIQUE <-> mot glycémie.
# Cible: valeurs hors-norme uniquement (≤49 mg/dL = hypo sévère, ≥300 mg/dL = hyper sévère).
# Un patient qui rapporte "ma glycémie est à 140" NE doit PAS déclencher l'urgence —
# c'est dans la cible. Ce regex est volontairement étroit : on attrape la valeur,
# pas la conversation autour de la valeur.
_NUMERIC_GLUCOSE = re.compile(
    # 10-49 (hypo sévère) ou 300-599 (hyper sévère) près d'un mot glycémique
    r"\b([1-4]\d|3\d{2}|4\d{2}|5\d{2})\b[^\d]{0,20}\b(sukkar|sucre|glyc\w*|sugar|سكر)\b"
    r"|\b(sukkar|sucre|glyc\w*|sugar|سكر)\b[^\d]{0,20}\b([1-4]\d|3\d{2}|4\d{2}|5\d{2})\b",
    re.IGNORECASE,
)


def _normalize(message: str) -> str:
    """Minuscule + collapse des espaces. Volontairement SIMPLE."""
    return re.sub(r"\s+", " ", message.strip().lower())


def classify(message: str) -> TriageClass:
    """Classe déterministe. L'ORDRE est la garantie de sécurité.

    1) hyperbole affective  -> NONE      (protège les faux positifs ; AVANT idéation)
    2) idéation suicidaire  -> CLASSE 2  (template soutien, jamais glycémie)
    3) urgence glycémique   -> CLASSE 1  (template glycémie existant)
    4) sinon                -> NONE      (poursuite du flux normal -> LLM crise-aware)

    Crisis detection delegated to safety.crisis (is_hyperbole, is_ideation).
    """
    if not message:
        return TriageClass.NONE

    norm = _normalize(message)

    if is_hyperbole(norm):
        return TriageClass.NONE

    if is_ideation(norm):
        return TriageClass.SUICIDAL_IDEATION

    if _NUMERIC_GLUCOSE.search(norm):
        return TriageClass.GLYCEMIC_EMERGENCY
    if any(kw in norm for kw in _GLYCEMIC_FR):
        return TriageClass.GLYCEMIC_EMERGENCY
    if any(kw in norm for kw in _GLYCEMIC_DARIJA):
        return TriageClass.GLYCEMIC_EMERGENCY
    if any(kw in message for kw in _GLYCEMIC_ARABIC):
        return TriageClass.GLYCEMIC_EMERGENCY

    return TriageClass.NONE


def select_triage_response(
    triage_class: TriageClass,
    *,
    glycemic_template: str,
    region: str = "MA",
    lang: str = "fr",
) -> str | None:
    """Aiguille vers le bon template. `glycemic_template` = template existant
    (passé en argument pour ne pas le réécrire ni le dupliquer)."""
    if triage_class is TriageClass.SUICIDAL_IDEATION:
        return crisis_support_response(region=region, lang=lang)
    if triage_class is TriageClass.GLYCEMIC_EMERGENCY:
        return glycemic_template
    return None


# ════════════════════════════════════════════════════════════════════════════
# INTEGRATION NOTES (pour le câblage dans triage_vital.py)
# ════════════════════════════════════════════════════════════════════════════
#
# 1) ORDRE DANS LE MIDDLEWARE — la classification DOIT tourner AVANT le routage
#    émotionnel/LLM. Le triage reste le 1er rempart.
#
#        cls = classify(user_message)
#        fixed = select_triage_response(
#            cls, glycemic_template=EXISTING_GLYCEMIC_TEMPLATE, region=patient.region,
#            lang=detected_lang,
#        )
#        if fixed is not None:
#            return fixed            # ZÉRO LLM, réponse pré-validée
#        # sinon : flux normal
#
# 2) DEUXIÈME COUCHE (filet pour l'ambigu) — pour un message "emotional" routé
#    vers le LLM, ajouter au system prompt :
#    "Si le patient exprime une détresse psychologique grave ou des idées noires,
#     ne donne AUCUN conseil glycémique ; oriente avec douceur vers de l'aide humaine."
#
# 3) RESSOURCES EN CONFIG — déplacer CRISIS_RESOURCES vers settings/DB.
#    Re-vérifier les ressources périodiquement (champ `verified`).
