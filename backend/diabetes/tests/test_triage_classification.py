"""
Tests pour la classification de triage à 2 classes.

Le cœur de cette suite, ce sont les TESTS NÉGATIFS (faux positifs à ne jamais
déclencher) et la GARANTIE SÉCURITÉ : une réponse de crise ne contient JAMAIS
d'instruction glycémique. Ces deux blocs sont plus importants que les positifs —
c'est exactement la couverture qui manquait (16 tests happy-path, 0 négatif).
"""

import pytest

from diabetes.middleware.triage_classification import (
    TriageClass,
    classify,
    crisis_support_response,
    select_triage_response,
)

GLYCEMIC_TEMPLATE_STUB = (
    "Glycémie critique. Prends du sucre rapide maintenant, mets-toi en position "
    "latérale de sécurité et appelle les secours."
)


# ════════════════════════════════════════════════════════════════════════════
# 1) TESTS NÉGATIFS — idiome de mort en usage HYPERBOLIQUE. NE DOIT JAMAIS firer.
# ════════════════════════════════════════════════════════════════════════════
HYPERBOLE_NON_URGENT = [
    "kan nmout 3la dik l7loua",
    "kan nmout 3la chocolat",
    "nmout men jou3",
    "rani nmout men jou3 a sat",
    "3yyit nmout men ld7k",
    "wllah nmout men d7k",
    "bnin kan nmout",
    "had tajine bnin nmout 3lih",
    "kan nmout men 3ya",
    "نموت من الجوع",
    "كنموت على هاد لحلوة",
]


@pytest.mark.parametrize("msg", HYPERBOLE_NON_URGENT)
def test_hyperbole_ne_declenche_jamais(msg):
    assert classify(msg) is TriageClass.NONE, (
        f"FAUX POSITIF : {msg!r} est une hyperbole affective"
    )


@pytest.mark.parametrize("msg", [
    "bghit nmout men jou3",
    "bghit nmout men ld7k",
])
def test_marqueur_ideation_battu_par_modificateur_affectif(msg):
    assert classify(msg) is TriageClass.NONE, (
        f"{msg!r} : 'men jou3/d7k' rend la phrase hyperbolique"
    )


@pytest.mark.parametrize("msg", [
    "salam, kif ndir bach n9es sukkar?",
    " klit couscous lyoum",
    "",
    "labas hamdolah",
])
def test_messages_neutres_ne_declenchent_pas(msg):
    assert classify(msg) is TriageClass.NONE


# ════════════════════════════════════════════════════════════════════════════
# 2) CLASSE 2 — IDÉATION SUICIDAIRE. DOIT firer -> template SOUTIEN.
# ════════════════════════════════════════════════════════════════════════════
IDEATION_MESSAGES = [
    "bghit nmout",
    "bghit mout",
    "ma b9itch baghi n3ich",
    "ma b9it baghi n3ich",
    "ma bghitch n3ich",
    "بغيت نموت",
    "ما بقيتش باغي نعيش",
    "je veux mourir",
    "j'en peux plus de la vie",
    "j'ai plus envie de vivre",
]


@pytest.mark.parametrize("msg", IDEATION_MESSAGES)
def test_ideation_classee_classe2(msg):
    assert classify(msg) is TriageClass.SUICIDAL_IDEATION, (
        f"IDÉATION MANQUÉE (faux négatif, direction dangereuse) : {msg!r}"
    )


# ════════════════════════════════════════════════════════════════════════════
# 3) CLASSE 1 — URGENCE GLYCÉMIQUE / PHYSIQUE.
# ════════════════════════════════════════════════════════════════════════════
GLYCEMIC_MESSAGES = [
    "7assfiya b3da ghadi ntih",
    "rani ghadi ntih",
    "ydiya kayrj fou w ma kan7ml",
    "fqdt l3ql",
    "je vais m'evanouir",
    "j'ai des convulsions",
    "غادي نطيح",
    "فقدان الوعي",
    "sukkar 38 w kanrjef",
]


@pytest.mark.parametrize("msg", GLYCEMIC_MESSAGES)
def test_urgence_glycemique_classee_classe1(msg):
    assert classify(msg) is TriageClass.GLYCEMIC_EMERGENCY, (
        f"URGENCE GLYCÉMIQUE MANQUÉE : {msg!r}"
    )


# ════════════════════════════════════════════════════════════════════════════
# 4) GARANTIE SÉCURITÉ CENTRALE — la réponse de crise (C2) ne contient JAMAIS
#    d'instruction glycémique. C'est le bug d'origine.
# ════════════════════════════════════════════════════════════════════════════
_GLYCEMIC_FORBIDDEN_TOKENS = [
    "sucre", "sukkar", "sugar", "سكر",
    "position laterale", "position latérale", "pls",
    "mange", "kul", "glucose", "glycemie", "glycémie",
]


@pytest.mark.parametrize("region", ["MA", "FR"])
@pytest.mark.parametrize("lang", ["fr", "ar-MA"])
def test_reponse_crise_zero_instruction_glycemique(region, lang):
    txt = crisis_support_response(region=region, lang=lang).lower()
    for tok in _GLYCEMIC_FORBIDDEN_TOKENS:
        assert tok not in txt, (
            f"FUITE GLYCÉMIQUE dans la réponse de crise ({region}/{lang}): {tok!r}"
        )


def test_routage_ideation_renvoie_template_crise_pas_glycemie():
    out = select_triage_response(
        TriageClass.SUICIDAL_IDEATION,
        glycemic_template=GLYCEMIC_TEMPLATE_STUB,
        region="MA",
        lang="fr",
    )
    assert out != GLYCEMIC_TEMPLATE_STUB
    assert "sucre" not in out.lower()


def test_routage_glycemie_renvoie_template_existant_inchange():
    out = select_triage_response(
        TriageClass.GLYCEMIC_EMERGENCY,
        glycemic_template=GLYCEMIC_TEMPLATE_STUB,
        region="MA",
    )
    assert out == GLYCEMIC_TEMPLATE_STUB


def test_routage_none_ne_renvoie_aucun_template():
    out = select_triage_response(
        TriageClass.NONE, glycemic_template=GLYCEMIC_TEMPLATE_STUB, region="MA",
    )
    assert out is None


# ════════════════════════════════════════════════════════════════════════════
# 5) RESSOURCES DE CRISE — exactitude par région.
# ════════════════════════════════════════════════════════════════════════════
def test_crise_FR_contient_3114():
    assert "3114" in crisis_support_response(region="FR", lang="fr")


def test_crise_MA_ne_contient_pas_3114_ni_numero_invente():
    txt = crisis_support_response(region="MA", lang="fr")
    assert "3114" not in txt
    assert "stopsilence.org" in txt
    assert "hôpital" in txt.lower() or "hopital" in txt.lower()


def test_crise_MA_oriente_vers_humain_pas_vers_le_bot():
    txt = crisis_support_response(region="MA", lang="fr").lower()
    assert "personnes formées" in txt or "ecoute" in txt or "écoute" in txt


# ════════════════════════════════════════════════════════════════════════════
# 6) INTÉGRATION MIDDLEWARE — l'idéation est attrapée par le gate AVANT le LLM.
# ════════════════════════════════════════════════════════════════════════════
import json  # noqa: E402 — grouped under the integration-test section divider

from django.contrib.auth.models import User  # noqa: E402
from django.test import RequestFactory, TestCase  # noqa: E402


class TriageMiddlewareWiringTest(TestCase):
    """Confirme que le middleware route bien la Classe 2 vers la réponse crise,
    pas vers le template glycémie — c'est le bug d'origine qu'on ferme."""

    def setUp(self):
        from core.middleware.triage_vital import TriageVitalMiddleware
        self.user = User.objects.create_user(username="patient_test", password="x")
        self.sentinel = object()
        self.middleware = TriageVitalMiddleware(lambda req: self.sentinel)
        self.factory = RequestFactory()

    def _post(self, message: str):
        req = self.factory.post(
            "/api/v1/ai/chat",
            data=json.dumps({"message": message}),
            content_type="application/json",
        )
        req.user = self.user
        return self.middleware(req)

    def test_ideation_attrapee_par_gate_avant_llm(self):
        """'bghit nmout' → réponse crise renvoyée, get_response (LLM) jamais appelé."""
        resp = self._post("bghit nmout")
        self.assertIsNot(resp, self.sentinel, "Le LLM a été appelé — gate raté")
        body = json.loads(resp.content)
        self.assertEqual(body["conversation_id"], "TRIAGE_CRISIS")
        self.assertTrue(body["is_emergency"])

    def test_ideation_ne_contient_pas_instruction_glycemique(self):
        """Le bug d'origine : 'bghit nmout' → 'mange du sucre'. Plus jamais."""
        resp = self._post("bghit nmout")
        body = json.loads(resp.content)
        reply = body["reply"].lower()
        for forbidden in ["sucre", "sukkar", "position latérale", "pls", "mange"]:
            self.assertNotIn(forbidden, reply, f"Fuite glycémique: {forbidden!r}")

    def test_hyperbole_passe_au_flux_normal(self):
        """'kan nmout 3la l7loua' → pas un gate, le LLM doit recevoir le message."""
        resp = self._post("kan nmout 3la l7loua")
        self.assertIs(resp, self.sentinel, "Hyperbole bloquée à tort par le gate")


# ════════════════════════════════════════════════════════════════════════════
# 7) DETTE DE COUVERTURE CONNUE — variantes orthographiques à curer.
# ════════════════════════════════════════════════════════════════════════════
@pytest.mark.xfail(reason="variantes orthographiques d'idéation non couvertes — "
                          "à curer avec corpus natif avant pilote patients réel")
@pytest.mark.parametrize("msg", [
    "bghit nmoot",
    "bghit nmut",
    "bgit nmout",
])
def test_variantes_orthographiques_ideation_a_couvrir(msg):
    assert classify(msg) is TriageClass.SUICIDAL_IDEATION
