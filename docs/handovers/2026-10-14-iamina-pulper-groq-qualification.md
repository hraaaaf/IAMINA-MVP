## 15 octobre 2026 — P1 PULPER : QUALIFICATION TECHNIQUE POST-INTÉGRATION SUR `a18139aec53ae6a11eceeeb15d898debad31f75b`

Deux défauts P1 (provenance source↔valeur/unité et confirmation avant aperçu) corrigés via [#1015](https://github.com/hraaaaf/IAMINA-MVP/pull/1015), fusionnés UNIQUEMENT vers la branche de la PR #1005. 5/5 runs success sur `a18139aec53ae6a11eceeeb15d898debad31f75b`: [Pulper #38692936390](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38692936390), [CI #38692936595](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38692936595), [Protected Shadow #38692936522](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38692936522), [Django #38692936557](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38692936557), [portabilité #38692936420](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38692936420). Artefact [#11952668344](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38692936390/artifacts/11952668344) téléchargé et JSON inspecté : `passed=true`, 18/18 critiques, 6/6 rejets fail-closed, FP=FN=0, provenance 18/18, 0 corruption, 0 fuite sentinelle, 4 appels Groq sur données fictives et OCR image simulé. Ce commit de documentation crée un **nouveau HEAD** dont la CI exacte reste à lire; ne pas recycler les succès du SHA `a18139aec53ae6a11eceeeb15d898debad31f75b`.

**Frontière** : PR #1005 reste DRAFT, aucun merge main ni déploiement Vercel, aucune utilisation sur documents patients réels. Approbations humaine clinique/sécurité/privacy/CNDP/Groq toujours en attente [#320](https://github.com/hraaaaf/IAMINA-MVP/issues/320) / [#1002](https://github.com/hraaaaf/IAMINA-MVP/issues/1002). P5 historique 50 %.

---

## 14 octobre 2026 — AUDITS PAR DISCIPLINE EXÉCUTÉS (IA, NON SIGNÉS) — SHA `e3073670`

**Précision d'indépendance :** trois pré-analyses distinctes clinique, CNDP/privacy et sécurité ont été réalisées dans le même système IA, et NE SONT PAS trois avis humains indépendants, ne signent ni ne certifient un logiciel médical ou un transfert réel de données patients. Aucun nouvel essai sur patient réel ni test d'intrusion n'a été exécuté.

- **Audit clinique [rapport PR #1005](https://github.com/hraaaaf/IAMINA-MVP/pull/1005#issuecomment-6181089756) : NO-GO patient réel.** Code `pulper.py:327-346` ne relie pas strictement valeur normalisée et extrait source : `verified=True` est possible sur une ligne contenant `raw_value` sans vérifier l'accord numérique/unité. `api/v1/documents.py:148-154,211-221` permet `confirm=true` dans le POST initial, contournant l'aperçu comme étape serveur obligatoire. Deux P1 de revue statique, tests négatifs à écrire. Besoin de formats IFCC mmol/mol, NGSP %, glycémie mmol/L / mg/dL, discordances multi-pages, posologies, OCR vrai.
- **Audit privacy/CNDP [rapport PR #1005](https://github.com/hraaaaf/IAMINA-MVP/pull/1005#issuecomment-6181091121) : NO-GO egress patient.** Groq `PENDING` et fondement juridique vide dans `backend/core/ai_processor_policy.py`. Cinq preuves contractuelles/réglementaires internes non obtenues : CNDP santé, transferts à l'étranger, DPA IAMINA/Groq, ZDR réellement actif sur compte production, notice/consentement patient. Références CNDP et Groq sur le rapport. Gate existant [#320](https://github.com/hraaaaf/IAMINA-MVP/issues/320).
- **Audit AppSec [rapport PR #1005](https://github.com/hraaaaf/IAMINA-MVP/pull/1005#issuecomment-6181092553) : GO technique synthétique conditionnel, NO-GO patient.** Vérifications de code des portes auth, policy consentement, ZIP/MIME et enveloppe JSON ; P1 intégrité/confirmation ci-dessus, preuve d'absence globale de PHI non établie, tests négatifs Groq à compléter. P2 à tester : exception `PulperShield.validate` enregistrant du texte d'exception potentiellement non nettoyé.
- **Ticket de correction P1 [#1011](https://github.com/hraaaaf/IAMINA-MVP/issues/1011)** créé, conditions de succès explicites et tests à ajouter SANS abaisser les seuils ni envoyer de vraies données patient. [Issue qualification #1002](https://github.com/hraaaaf/IAMINA-MVP/issues/1002) et [Notion Handover maître](https://app.notion.com/p/3f477c66336281b28c78eb11c22f5ee6) actualisés.
- **CI du SHA étudié : 5/5 SUCCESS**, 18/18 faits synthétiques, 6/6 rejets, mais les CI n'ont pas testé ces nouveaux scénarios P1. La présente modification n'est que documentaire : ne pas prétendre que les CI du nouveau SHA sont déjà vertes.

**Verdict commun :** NO-GO fusion clinique/productive et envoi de documents réels à Groq. **Next exact :** corriger #1011 avec tests, requalifier le nouveau code, collecter les cinq justificatifs account-specific et obtenir les trois approbations datées de professionnels indépendants avant le moindre merge main/egress patient. PR #1005 DRAFT, aucun Vercel.

---

## 14 octobre 2026 — CLOSEOUT TECHNIQUE VÉRIFIÉ sur `8be7da98` (5/5 vert)

**Goal** : préserver Groq GPT-OSS pour les textes PDF/DOCX Pulper, corriger les erreurs de format/réponse et prouver l'extraction synthétique sans assouplir provenance, seuils, protection egress ni contrôle médical.

**Succès observable / preuve exacte :** HEAD `8be7da98736ed2fd8806b811c967bf382ce30dda` sur [PR #1005](https://github.com/hraaaaf/IAMINA-MVP/pull/1005) : cinq workflows TERMINÉS SUCCESS :
- [Pulper Golden Corpus #38652269367](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38652269367)
- [CI #38652269378](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38652269378)
- [Protected Shadow #38652269402](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38652269402)
- [Django migration drift #38652269360](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38652269360)
- [Developer portability #38652269357](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38652269357)

**Artefact de qualification exact** [#11935875573](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38652269367/artifacts/11935875573) téléchargé et lu : `passed=true`, `18/18` faits critiques, zéro FP/FN, précision/rappel/provenance/couverture/timestamps/version/fail-closed 100 %, `6/6` rejets, `0` corrosion clinique, `0` fuite sentinelle, `4` appels réels à Groq **sur corpus fictif** PDF/DOCX. Images `3` fixtures synthétiques, PAS qualification OCR vision réelle. Tous les seuils inchangés.

**Fix macOS** : subprocess d'un test `evaluation` relancé depuis `backend` ; import Ruff I001 corrigé ; CI PostgreSQL, Ruff, passerelle anti-bypass, portabilité macOS/Windows toutes SUCCESS au SHA certifié.

**Décision de closeout** : le **lot de qualification logicielle synthétique Pulper/Groq est techniquement clos** sur SHA `8be7da98`. Cette insertion de documentation est un commit post-preuve, sans modification runtime, et aura **son propre verdict CI** ; ne PAS transférer automatiquement l'état 5/5 au HEAD documentaire. **PR #1005 reste DRAFT NON FUSIONNÉE vers main**, et [issue #1002](https://github.com/hraaaaf/IAMINA-MVP/issues/1002) reste ouverte pour la livraison contrôlée.

**VRAI HUMAN GATE pour la fusion / usage patient** : évaluation clinique indépendante, vérification sécurité et confidentialité de l'envoi de documents médicaux à Groq (finalité, données envoyées, résidence/traitance et politiques patient), puis autorisation explicite de mise en production. Le benchmark n'autorise pas l'egress clinique réel et n'apporte aucune précision OCR image clinique. Aucun patient réel, aucun Vercel. D7/#7/D9/#9 séparés. P5 historique 50 %, pas recalculé.

**Next exact** : vérifier CI sur le commit documentaire final ; si verte, transmettre la PR au circuit de revue clinique/privacy/sécurité, sans merge main ni déploiement avant signatures. Si rouge, diagnostiquer échec, corriger, relancer.

---

## 14 octobre 2026 — dernier état de reprise pour Pulper/Groq

**Objectif** : maintenir Groq sur PDF/DOCX avec preuves de provenance et seuils médicaux inchangés. **Preuve acquise** : SHA `e44b1a9e`, Pulper #38646278280, CI #38646278329, Protected Shadow #38646278296 et migration #38646278289 SUCCESS ; artefact Pulper #11933046605 vérifié 18/18 faits critiques, 6/6 rejets, 0 corruption, Groq texte 4 cas live fictifs, images simulées seulement.

**Portabilité macOS** : job #38646278327 rouge (autonomous `python -c` depuis racine repo, `ModuleNotFoundError: evaluation`). Correction sûre test-only sur SHA `87dc3972` : `cwd=Path(__file__).resolve().parents[1]` dans `backend/evaluation/test_clinician_prep_protected_shadow_benchmark.py`, sans modifier code patient. Le passage CI #38651962051 a révélé une erreur Ruff `I001` (ordre `datetime`/`pathlib`) ; ce dernier correctif de tri d'import est inclus dans la présente révision, et aucun succès du SHA final n'est encore revendiqué. Les runs Pulper #38651962043, Protected Shadow #38651962042 et Django drift #38651962054 avaient déjà SUCCESS sur la révision intermédiaire.

**Next exact** : contrôler CI générale, portabilité macOS et qualification Pulper sur ce nouveau SHA ; réparer seulement en cas de nouvel échec. PR [#1005](https://github.com/hraaaaf/IAMINA-MVP/pull/1005) DRAFT/unmerged `main`. **Human gate** : validation clinique/sécurité/privacy et autorisation d'egress patient réels vers Groq non acquises ; ne pas merger ni déployer Vercel. D7/#7 et D9/#9 séparés. P5 historique 50 %.

---

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
