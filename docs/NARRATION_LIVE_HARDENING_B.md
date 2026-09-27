# IAMINA — Narration Live Hardening B

Base certifiée : `main@96f6c853383600b99119d5edcc1fc6de1df9f8a0` après merge de Hardening A / PR #818.

## Goal

Remplacer les placeholders sémantiques prédictibles de type `{{FACT_GLUCOSE}}` par des tokens opaques, uniques et limités à une seule instance de `NarrationEnvelope`.

## Succès

- aucun semantic key n'est exposé dans le token provider ;
- chaque fait reçoit un token opaque cryptographiquement aléatoire ;
- deux enveloppes construites avec le même fait reçoivent des tokens différents ;
- un token provenant d'une autre enveloppe est rejeté fail-closed ;
- plusieurs faits d'une même enveloppe ont des tokens distincts ;
- la réinjection exacte reste locale après vérification ;
- aucun changement de décision clinique ;
- aucune activation live ;
- aucun changement UI, DB ou Vercel.

## Contrat

Format provider :
`{{NVF:<8hex>:<8hex>:<8hex>:<8hex>}}`

Le mapping `semantic fact key → opaque token` reste uniquement dans l'instance locale de `NarrationEnvelope`.

Le provider ne reçoit ni le semantic key interne ni la valeur exacte locale.

## Anti-replay

Le verifier n'accepte que les tokens émis par l'enveloppe courante.

Un token valide provenant d'une enveloppe précédente est traité comme inconnu et provoque un rejet.

## Hors scope

- rendu local déterministe des limitations obligatoires ;
- claim schema sémantique enrichi ;
- activation live d'une rule family ;
- nouvel egress patient.


## Dépendance A

Hardening A est mergé sur `main` :
- PR #818 ;
- merge exact `96f6c853383600b99119d5edcc1fc6de1df9f8a0` ;
- pré-merge : CI #5081 SUCCESS, migration #4108 SUCCESS, Companion E2E #279 SUCCESS.

Cette PR B est désormais évaluée directement contre `main`.


## Privacy egress compatibility

Le format segmenté par `:` évite qu'un token opaque soit classé comme identifiant stable par les contrôles privacy.
Les tokens générés sont testés pour traverser sans mutation :
- External Anonymization Gateway ;
- DLP text payload.

La segmentation ne réduit pas l'entropie : 128 bits aléatoires restent générés par enveloppe.
