# IAMINA V1-03 — Audit source OCR glycémie
2026-10-11 | Base Git `15cfe25fcc93fff00a1198d705fb683c7a2eb960` | Issue #923 | DRAFT parent #932

## Goal
Établir où une mesure provenant de l'OCR glycémique est capturée, interprétée, confirmée et persistée, et documenter les cas non prouvés. Audit de code uniquement : pas de nouveau test, déploiement ou validation clinique.

## Périmètre et preuves
- Inventaire de 170 fichiers Dart de production ciblés sous `frontend/lib` sur 230 blobs ; exclusions : l10n, pictogrammes, catalogues et exécutables d'audit UI. Aucun usage de `GlucoseOcrShield.extract` ou de `ApiClient.analyzeGlucometerImage` identifié hors des définitions. Les écrans Journal/AddLog examinés ne les appellent pas. Cela n'exclut pas une voie alternative non inventoriée.
- `frontend/lib/core/clinical/glucose_ocr_shield.dart` : refuse les nombres sans étiquette mg/dL ou mmol/L ou avec deux étiquettes. Traite néanmoins les marqueurs spéciaux HI/LO avant le contrôle d'unité, avec `confidence: 1.0` et `value: null`. La formule `needsConfirmation` peut devenir fausse sur une valeur numérique issue d'une seule correspondance sans que le code prouve un dialogue de confirmation.
- Le motif mg/dL ne reconnaît pas toute la plage décrite par son commentaire (décalage code/documentation à trancher cliniquement). Les valeurs multiples sont ramenées à la première avec une confiance réduite ; UI de correction non prouvée.
- `frontend/lib/services/api_client.dart` définit POST web OCR. `backend/ai/api/v1/ai.py` expose cette route, `backend/media/vision.py` exige une unité explicite dans le résultat structuré. La preuve optique de l'unité reste non démontrée. `backend/core/external_media_v1.py` refuse l'egress patient brut ; sur refus l'API retombe sur `value:null, fallback:true` (l'unité de remplacement n'est pas une mesure).
- Tests synthétiques `frontend/test/glucose_ocr_unit_provenance_test.dart` et `backend/media/tests/test_vision_provider_boundary.py` protègent notamment valeurs sans unité et étiquettes contradictoires. Référence engineering #932 : 16/16 GitHub Actions en succès au HEAD de base, dont https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38107828563. Aucune batterie additionnelle exécutée dans ce rapport.

## Verdict
**Vérifié** : les deux parsers exigent une unité explicite pour une valeur numérique ; aucun appel depuis les 170 fichiers ciblés. **Non prouvé** : parcours OCR patient mobile/web activé, capture réelle, provenance optique, correction, confirmation, sauvegarde, localisation FR/AR/Darija/RTL, accessibilité. **Risques à arbitrer** : HI/LO, confiance élevée sans confirmation automatique garantie, valeurs multiples et divergence de plage commentée.

## Suite / critères d'acceptation
Inventorier tous les entrypoints alternatifs et les tests d'injection, fixer par revue clinique le traitement des cas ambigus, implémenter uniquement sous feature flag désactivé par défaut un futur parcours capture→confirmation explicite→persistance, avec tests de refus/absence d'autosave et BEFORE/AFTER si UI touchée. Ne pas rouvrir l'egress média sans revue privacy/processor. Aucun usage patient, merge ou Vercel.

## Complement technique — 2026-10-11
- Test de characterization ajouté : `frontend/test/glucose_ocr_activation_boundary_test.dart`. Il protège le statut non connecté des callers OCR et vérifie que HI/LO ne deviennent pas des valeurs numériques, tandis que des nombres multiples exigent correction.
- Ce test ne prouve pas la provenance optique ni un parcours UI ; son verdict exact-head GitHub reste à établir. Aucune activation patient.

## Gate clinique pré-activation : matrice de preuve (2026-10-11)

**Statut : dossier de validation proposé, NON approuvé.** Les valeurs/chaînes ci-dessous sont des fixtures synthétiques et non des mesures de patients. Aucun comportement clinique, écran ni endpoint activé par ce document.

| Scénario synthétique | État du code relevé | Condition minimale exigée pour un futur parcours patient |
| --- | --- | --- |
| `120` ou `6.5` sans unité | Garde numérique : `hasValue=false`, `needsConfirmation=true` | Ne pas préremplir de glycémie autoritative ni inférer une unité ; édition manuelle explicite |
| `120 mg/dL` / `6.5 mmol/L` | Parser unitaire + conversion mmol/L à l'échelle ×18, score de confiance ; **`needsConfirmation=false` pour une lecture numérique unique à forte confiance** | Afficher unité d'origine, valeur et provenance, exiger **action de confirmation utilisateur distincte avant persistance** ; aucune sauvegarde sur simple score |
| `120 mg/dL 6.5 mmol/L` | Étiquettes contradictoires rejetées | Proposer correction manuelle avec origine inconnue, sans proposition numérique |
| `120 180 mg/dL` | Premier nombre retenu, score faible `0.58`, `needsConfirmation=true` | Aucune auto-validation ; faire choisir/confirmer le nombre affiché |
| `HI` / `LO` | `value=null`, drapeau booléen, `confidence=1.0`, `needsConfirmation=true`; traitement spécial avant contrôle de l'unité | **Décision clinicien requise** : présentation et triage, sans transformer un indicateur hors plage en valeur exacte, ni sauvegarder une valeur fabriquée |
| `401 mg/dL` à `600 mg/dL` | Motif `_glucosePattern` ne matche que `400` au-dessus de 399, malgré commentaire « 400–600 » ; donc absence de valeur OCR exploitable | Trancher cliniquement plage autorisée et erreur de texte/documentation ; ne pas élargir sans tests et revue |
| Lecture optique réelle avec contexte voisin (date, heure, numéro de série) | Aucune chaîne capture→UI→confirmation→DB prouvée ; contrôle lexical seul | Prouver sur fixtures d'images autorisées le choix de la bonne mesure, son unité **visible**, la correction utilisateur, le refus de sauvegarde en cas de doute et l'absence d'egress non autorisé |
| Annulation, application hors ligne, redémarrage ou refus IA local A | OCR non connecté aux écrans courants ciblés ; preuve réelle absente | Aucune sauvegarde sur annulation, interruption ou refus ; tests Android/iOS, FR/AR/RTL, 200% text scaling, observabilité sans PHI |

**Définition de succès future, non acquise** : (1) preuve source de l'entrée OCR activée derrière feature flag **OFF par défaut** ; (2) fixtures multi-images et revues clinicien qualifié ; (3) chemin exact capture→prévisualisation→correction→confirmation explicite→persistance, avec tests négatifs « annuler = rien en DB » ; (4) vérification absence de cloud média non autorisé ; (5) captures BEFORE/AFTER aux mêmes 390×844 / 768×1024 / 1280×900 si l'UI change, accessibilité et FR/AR ; (6) tests SQLite/PostgreSQL/Flutter exact-HEAD et avis indépendant privacy/sécurité/clinique avant utilisation réelle.

**Arbitrages humains non remplacés par ce plan** : signification HI/LO et action de sécurité, plage acceptée, seuils d'anomalie, niveau de preuve optique et responsabilité de confirmation. Recommandation de séquence la plus prudente : **maintenir le parcours OCR non exposé**, exiger confirmation explicite de toute lecture si une future UI est autorisée ; ce dernier choix est une proposition de gouvernance, pas un avis médical approuvé.
