# IAMINA — Narration Live Hardening A

Base : `main@e456ab806ce2da165a420d66bfcc5bbf66b16d69`.

## Goal

Fermer deux voies de risque connues avant toute activation live du Narration Envelope :
1. fuite d'une mesure exacte ou quasi-exacte via `provider_hint` ;
2. accès au mode provider `think()` depuis le gateway patient gouverné.

## Succès

- un `provider_hint` `coarsened_only` ne peut contenir la valeur exacte ;
- il ne peut réutiliser le même fragment numérique ;
- il ne peut contenir une autre mesure clinique chiffrée présentée comme approximation ;
- un hint sémantique réellement grossier reste autorisé ;
- `GatewayLLM.think()` échoue avant tout appel provider ;
- tests adversariaux couvrent ces invariants ;
- aucune activation de narration live ;
- aucune modification UI, DB ou Vercel.

## Pourquoi

Le shadow contract autorisait déjà seulement `LOCAL_ONLY` et `COARSENED_ONLY`, mais le contenu de `provider_hint` n'était pas encore contrôlé contre la valeur exacte.

Par ailleurs, `LLMPipeline.think()` était fail-closed, mais `GatewayLLM.think()` appelait encore directement le provider. Ce chemin devait être fermé explicitement pour respecter la doctrine :

**IAMINA décide. Le LLM formule. IAMINA vérifie.**

## Hors scope du lot A

- tokens opaques one-shot / anti-replay ;
- schéma sémantique riche pour required/forbidden claims ;
- vérification explicite des limitations obligatoires ;
- activation live d'une rule family ;
- nouvel egress patient.

Ces points forment le prochain lot de hardening après certification de ce lot.
