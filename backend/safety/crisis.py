"""
Crisis and suicidal ideation classifier — stateless, no LLM dependency.

Détecte les signaux d'idéation suicidaire et fournit les ressources de crise
adaptées par région/langue. Aucune dépendance vers engine/ ou diabetes/.

Garde-fou linguistique central (Darija), implémenté par ADJACENCE :
  "nmout 3la X" / "nmout men {jou3,d7k,3ya,...}" / "bnin ... nmout"  = HYPERBOLE  -> NONE
  "bghit nmout" / "ma b9itch baghi n3ich" SANS modificateur affectif = IDÉATION  -> CLASSE 2
  L'hyperbole est testée AVANT l'idéation.

────────────────────────────────────────────────────────────────────────────
⚠️  CE MODULE EST UN FILET DÉTERMINISTE HAUTE-PRÉCISION, PAS UN DÉTECTEUR EXHAUSTIF.
    Les messages ambigus qui n'atteignent aucune classe (return NONE) DOIVENT
    continuer vers le flux normal.

⚠️  LISTES POSITIVES DARIJA = AMORCE, PAS VÉRITÉ DE TERRAIN.
    À curer par un locuteur natif + revue clinique, idéalement sur corpus patients.
────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import re

# ════════════════════════════════════════════════════════════════════════════
# GARDE-FOU FAUX POSITIFS — idiome de mort en usage HYPERBOLIQUE
#   Testé par ADJACENCE (modificateur collé au verbe de mort), pas par simple
#   co-occurrence : évite de neutraliser une vraie idéation contenant "3la" ailleurs.
# ════════════════════════════════════════════════════════════════════════════
_DEATH_VERB = r"(?:kan\s*)?n?mou?t|ymout|tmout|نموت|يموت|تموت|الموت"
_AFFECT_NOUN = r"jjou3|jou3|ld7k|d7k|dahk|3ya|3yya|3ay|lbrd|lfar7a|chno|chi\s+7aja"

_HYPERBOLE_PATTERNS = (
    rf"(?:{_DEATH_VERB})\s+3la\s+\w+",                 # nmout 3la l7loua
    rf"(?:{_DEATH_VERB})\s+men\s+(?:{_AFFECT_NOUN})",  # nmout men jou3/d7k/3ya
    rf"(?:bnin|bnina|zwin|zwina|ldid|ldida)\W+(?:{_DEATH_VERB})",
    rf"(?:{_DEATH_VERB})\W+(?:bnin|bnina|zwin|zwina|ldid|ldida)",
    rf"(?:{_DEATH_VERB})\s+(?:من|على)\s+\S+",          # arabe: نموت من الجوع
)
_HYPERBOLE_RE = re.compile("|".join(_HYPERBOLE_PATTERNS), re.IGNORECASE)


# ════════════════════════════════════════════════════════════════════════════
# IDÉATION SUICIDAIRE — marqueurs HAUTE CONFIANCE uniquement
#   Le "nmout" bare ambigu N'est PAS ici (décision : éviter l'effet "cried wolf" ;
#   le bare nmout part vers le LLM crise-aware).
# ════════════════════════════════════════════════════════════════════════════
_IDEATION_MARKERS = (
    r"bghit\s+n?mou?t",                       # bghit nmout / bghit mout
    r"baghi(?:a)?\s+n?mou?t",
    r"bghit\s+ns?ali\s+3la\s+rasi",           # bghit nsali 3la rasi (en finir)
    r"bghit\s+nkml?l?\s+3la\s+rasi",
    r"ma\s+b9it\w*\s+(?:baghi\s+)?n3ich",     # ma b9itch (baghi) n3ich
    r"ma\s+bghit\w*\s+n3ich",
    r"ma\s+b9a\s+3andi\s+ma\s+n3ich\s+3lih",
    r"بغيت\s+ن?موت",
    r"ما\s+بقيتش?\s+(?:باغي\s+)?نعيش|ما\s+بغيتش?\s+نعيش",
    r"نسالي\s+على\s+راسي|نكمل\s+على\s+راسي",
    r"je\s+veux\s+(?:mourir|en\s+finir|plus\s+vivre)",
    r"j[' ]?en\s+peux\s+plus\s+de\s+(?:la\s+)?vie",
    r"plus\s+envie\s+de\s+vivre",
)
_IDEATION_RE = re.compile("|".join(_IDEATION_MARKERS), re.IGNORECASE)


def is_hyperbole(normalized_message: str) -> bool:
    """Returns True if the message is an affective hyperbole (not a real crisis signal)."""
    return bool(_HYPERBOLE_RE.search(normalized_message))


def is_ideation(normalized_message: str) -> bool:
    """Returns True if the message contains a high-confidence suicidal ideation marker."""
    return bool(_IDEATION_RE.search(normalized_message))


# ════════════════════════════════════════════════════════════════════════════
# RESSOURCES DE CRISE — VÉRIFIÉES le 2026-05-29 (sources publiques). À RE-VÉRIFIER.
#   ⚠️ Doit vivre en CONFIG, pas en dur : numéros/horaires changent.
#   ⚠️ FR : 3114 = national, 24/7, gratuit (confirmé).
#   ⚠️ MA : PAS de ligne nationale 24/7 vérifiée. Ressource = chat "Stop Silence"
#           (Sourire de Reda), horaires limités. NE PAS inventer de numéro marocain.
# ════════════════════════════════════════════════════════════════════════════
CRISIS_RESOURCES = {
    "FR": {
        "kind": "phone",
        "line": "3114",
        "name": "Numéro national de prévention du suicide",
        "hours": "24h/24, 7j/7, gratuit",
        "verified": "2026-05-29",
    },
    "MA": {
        "kind": "chat_plus_hospital",
        "chat_url": "https://www.stopsilence.org",
        "chat_name": "Stop Silence (Sourire de Reda)",
        "chat_hours": "Lun & Ven 16h–21h · Mar/Mer/Jeu 16h–23h · Sam 16h–18h30 (à re-vérifier)",
        "primary": "urgences de l'hôpital le plus proche",
        # ⚠️ Réutiliser la MÊME constante de secours déjà validée dans le template glycémie.
        "emergency_number": None,
        "verified": "2026-05-29",
    },
}


def crisis_support_response(region: str = "MA", lang: str = "fr") -> str:
    """Réponse de soutien en crise. Contrats de sécurité :
      - AUCUNE instruction glycémique (ni sucre, ni PLS, ni "mange").
      - Ne nomme aucun moyen.
      - Ne fait pas de promesse catégorique de confidentialité.
      - Redirige vers de l'aide HUMAINE, ne se centre pas sur le bot.

    ⚠️ Versions ar-MA (Darija) volontairement laissées en TODO : une formulation
       de crise mal calibrée en Darija peut faire plus de mal que le français.
       À écrire avec un locuteur natif + validation clinique avant prod.
    """
    res = CRISIS_RESOURCES.get(region, CRISIS_RESOURCES["MA"])

    if lang.startswith("ar"):
        if region == "FR":
            return (
                "أنا قرأت ضيق فكلامك وكناخدو بجدية. ما خصكش تعيش هاد الشي بوحدك. "
                "إلا كنتي فخطر دابا، عيّط للنجدة. تقدر تهضر مع ناس مكوّنين على "
                "الإصغاء فالرقم 3114 (مجاني، 24/24)."
            )
        return (
            "أنا قرأت ضيق فكلامك وكناخدو بجدية. ما خصكش تعيش هاد الشي بوحدك. "
            "إلا كنتي فخطر دابا، سير لمستعجلات أقرب مستشفى. تقدر تهضر مع ناس "
            "مكوّنين على الإصغاء عبر Stop Silence (stopsilence.org)."
        )

    intro = (
        "Je lis beaucoup de détresse dans ton message, et je la prends au sérieux. "
        "Tu n'as pas à traverser ça seul·e — le plus important maintenant, "
        "c'est d'en parler à quelqu'un."
    )
    if region == "FR":
        ressource = (
            f"Si tu es en danger immédiat, appelle les secours. "
            f"Tu peux aussi parler dès maintenant à des personnes formées à l'écoute "
            f"au {res['line']} ({res['name']}, {res['hours']})."
        )
    else:
        ressource = (
            f"Si tu es en danger immédiat, va aux {res['primary']} ou appelle les secours. "
            f"Tu peux aussi échanger avec des personnes formées à l'écoute via "
            f"{res['chat_name']} ({res['chat_url']})."
        )
    return f"{intro} {ressource}"
