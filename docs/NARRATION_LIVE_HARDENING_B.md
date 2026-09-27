# IAMINA — Narration Live Hardening B

Base stackée : Narration Live Hardening A.

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
`{{NVF_<128-bit random hex>}}`

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
