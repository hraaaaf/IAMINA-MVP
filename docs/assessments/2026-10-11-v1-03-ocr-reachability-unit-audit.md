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
