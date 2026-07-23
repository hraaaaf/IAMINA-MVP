# ADR 0003 — PHI Pseudonymizer extrait en service

- **Statut :** accepté (rétroactif)
- **Date :** 2026-04-17
- **Décideurs :** Software Architect, Security Architect

## Contexte

Le POC hébergeait la classe `PHIPseudonymizer` directement dans `logs/views.py`, mélangée à la logique HTTP. `TEAM.md` (Software Architect, Security Architect, Data/AI) impose :

- Pas d'appel LLM ni de primitive sécurité dans une view — tout passe par `services/`.
- Pseudonymisation PHI avant tout envoi à un fournisseur externe, appliquée uniformément aux appels résumé + chat + analyse clinique.
- Interface stable consommable par les futurs adaptateurs LLM (Claude, Gemini, autre).

## Décision

Extraire la pseudonymisation dans `backend/llm/pseudonymizer.py` (promu en package top-level lors du refactoring chassis) :

- Tokenise les données patient en UUID jetables avant tout envoi API.
- Détokenise la réponse reçue pour ré-hydrater les données réelles côté serveur.
- Expose une API stable : `tokenize(payload) -> (pseudo_payload, map)` et `untokenize(response, map)`.
- Aucun import direct depuis les views ; seuls les services LLM (`engine/`, `diabetes/services/clinical/engine.py`) l'utilisent.

## Conséquences

**Positives**

- Point unique pour la politique PHI : toute nouvelle intégration LLM hérite automatiquement de la pseudonymisation.
- Testable sans Django (fonctions pures hors HTTP).
- Audit sécurité simplifié : la frontière tokenisation/détokenisation est visible dans un fichier.

**Négatives**

- Légère indirection — un ingénieur doit connaître le fichier pour comprendre le flux LLM end-to-end. Compensé par les docstrings et la proximité dans `services/llm/`.

## Alternatives rejetées

- **Décorateur appliqué aux views** : couple la pseudonymisation au transport HTTP, rend les appels asynchrones plus difficiles, viole la directive "aucun appel LLM dans une view".
- **Middleware Django** : même problème (HTTP-only, rate tout appel batch ou management-command).

## Suivi

- TD-003 dans `techdebt.md` : ajouter timeout / retry / circuit breaker autour des appels LLM (couche `services/llm/base.py` à créer lorsque le provider cible sera arrêté, cf. TD-001).
