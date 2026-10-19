# W01 — Groq strict JSON HTTP 400, correction candidate (19 October 2026)

**Goal:** Réduire les erreurs Groq GPT-OSS HTTP 400 sur le décodage JSON strict, sans relâcher les règles médicales de provenance, de précision ni de refus sûr. **Statut : candidate PR #1128 Draft, W01 NO-GO.**

**Avant :** CI `39274053015`, Ruff I001 unique dans `backend/diabetes/tests/test_pulper_groq_reply_envelope.py` ; Pulper CI `39274052750`, artefact JSON `12196826717` : 17 vrais positifs, 0 faux positif, 1 faux négatif (`docx-fasting`), HTTP 400 `provider_internal_failure`; précision 100 %, rappel 94,44 %, provenance 94,44 %, formats 100 %, fail-closed 100 %. La variante strict-preface du transport probe renvoie aussi 400, base-preface 200. Aucune information médicale fabriquée.

**Correction :** pour la combinaison Groq + GPT-OSS exclusivement, un HTTP 400 à la complétion JSON stricte autorise **une seule nouvelle tentative**, avec requête et schéma strict identiques. 2e erreur → refus normalisé fail-closed. Aucun retry des quotas, 401/403, timeouts, erreurs serveur, ni des autres modèles. Journalisation fixe uniquement, compteur agrégé `parser_route_counts.groq_strict_json_retries` dans le rapport de qualification. Correction de l'ordre des imports Ruff. Les seuils/valeurs attendues du corpus ne changent pas.

**Preuve locale sur l'exact parent `940d127d7e36155b5059ee29af54ec38afecba6a` :** Vercel Sandbox isolé `ruff check .` PASS ; `pytest` 61 PASS / 1 SKIP et 3 subtests PASS, couvrant fournisseurs, Pulper, enveloppe, sécurité et provenance ; `git diff --check` PASS. Aucun secret de Production utilisé.

**GO requis :** 100 % des workflows GitHub sur le SHA exact, benchmark **live** Groq une fois sur le candidat en conservant TOUS les seuils, revue sécurité indépendante, et W01 BFF / session patient hébergée. Si benchmark rouge, relever les codes et formes de réponse autorisés sans journaux bruts ni données patients, puis diagnostiquer avant tout nouveau run. Aucun déploiement Vercel Production / Neon Production / merge.
