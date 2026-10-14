# IAMINA — Pulper Groq — qualification synthétique et gates
_Date : 14 octobre 2026. Statut : correctif technique en PR #1005, non fusionné à main._

## Goal / succès / preuve
**Goal** : garder **Groq GPT-OSS 120B** pour l'analyse textuelle PDF/DOCX de Pulper, sans remplacer par un parseur déterministe, et restaurer la qualification synthétique sans assouplir les règles cliniques de provenance et de fail-closed.

**Succès observable dans le lot synthétique** : 99 % minimum de précision et rappel critiques, 100 % provenance, couverture du corpus, fail-closed des formats interdits, capture des versions, zéro corruption critique et zéro fuite de sentinelle.

**Preuve déjà acquise sur la révision testée** : PR [#1005](https://github.com/hraaaaf/IAMINA-MVP/pull/1005), SHA `7c7fc08e7df6cd141a4f8ba6c7d816edf7fef40d` ; [run Pulper #38645651119](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38645651119) **SUCCESS**, rapport joint [artifact #11931892795](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38645651119/artifacts/11931892795) téléchargé et inspecté : `passed=true`, 18/18 champs critiques exacts, précision=1.0, rappel=1.0, provenance=1.0, couverture=1.0, version=1.0, fail-closed=6/6, zéro corruption, sentinelle=0 et 4 appels Groq live PDF/DOCX. Les 3 cas image du corpus restent des transcriptions/analyses **synthétiques déterministes** ; **aucune précision OCR vision réelle qualifiée** par ce run.

## Cause / correction
Le paramètre `reasoning_format=hidden` était incompatible avec GPT-OSS sur Groq d'après les [docs officielles Groq](https://console.groq.com/docs/reasoning) ; on passe `include_reasoning=false` sans abaisser le plafond de tokens. Le format strict Groq exige `{"reply":"JSON extraction sérialisé"}`, tandis que Pulper attendait directement le JSON d'extraction. Le nouveau prompt `pulper-parse-v5-groq-envelope` permet un décodage exact des deux couches, avec refus des enveloppes falsifiées ou mal typées. Le SDK `google-genai` est repinné à `2.30.1` pour que les CI Python puissent installer ses dépendances ; cet SDK n'est pas utilisé par la voie Pulper Groq.

Contrats inchangés : `PHIPseudonymizer`, `assert_ai_egress_allowed(TEXT)`, `get_llm().complete` gouverné, vérification de l'extrait sur sa ligne source, `PulperShield`, erreur fermée sans extraction inventée. Pas de données patient, secrets ou réponse brute en artefacts.

## Vérification des autres CI / human gate
Au run sur SHA `7c7fc08e`, le contrôle **Protected Shadow internal live probe** a échoué avant réseau : une assertion test `test_provider_registry.py` attendait l'ancien nom de paramètre, alors que le code et les tests ciblés Pulper sont corrects. Ce commit documentaire + assertion actualise ce contrat ; **les nouveaux workflows sur nouveau SHA nécessitent lecture exacte avant certification générale**.

**Non prouvé** : application médicale approuvée pour données de patients réels, autorisation de transfert de données médicales à Groq, validation clinique et confidentialité indépendantes, précision OCR vision réel. **Aucune fusion vers main, aucun déploiement Vercel.** Les décisions D7/#7 et D9/#9 restent un chantier séparé.

## Reprise exacte
1. Vérifier les workflows GitHub sur le SHA de clôture de la PR #1005 et corriger toute régression liée au changement.
2. Examiner le nouvel artefact Pulper sans fuite et confirmer les seuils inchangés.
3. Documenter le bilan vérifié dans issue #1002 / Notion ; ne pas fusionner vers main avant validation sécurité/confidentialité clinique indépendante.
