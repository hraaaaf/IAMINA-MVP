# IAMINA — Narration Envelope / Shadow Mode

Base : `main@455a1ca1904a41874c62af169793b70d070b7d7a`.

## Goal

Créer la frontière structurée entre le cerveau clinique déterministe IAMINA et le futur narrateur natif, sans modifier les réponses patient, sans nouvel egress et sans donner au LLM une autorité clinique.

## Succès

- contrat versionné `narration-envelope.v1` ;
- `AdviceDecision` reste l'autorité source ;
- speech act, locale, claims, limitations et actions sont transportés explicitement ;
- les valeurs de faits exactes restent locales ;
- les faits `local_only` n'exposent aucune valeur au provider view ;
- un futur hint provider ne peut être que `coarsened_only` et distinct de la valeur exacte ;
- les placeholders requis doivent survivre à la formulation ;
- token inconnu ou manquant → fail-closed ;
- chiffre clinique untokenized inventé → fail-closed ;
- réinjection de la valeur exacte seulement localement après vérification ;
- intégration runtime en shadow mode sur les réponses gouvernées ;
- shadow failure n'altère pas la réponse patient actuelle ;
- aucun appel LLM ajouté ;
- aucun changement UI, DB ou Vercel.

## Architecture

`AdviceResolution`
→ `NarrationEnvelope`
→ provider view sans valeur exacte
→ futur narrateur linguistique
→ structural verifier
→ family semantic verifier
→ réinjection locale
→ output/safety guards.

Dans ce lot, la partie « futur narrateur » n'est pas activée. Le runtime construit seulement l'envelope en shadow mode puis continue à retourner la réponse déterministe existante.

## Privacy invariant

`NarrationFact.rendered_value` n'est jamais exposé par `provider_view()`.

Deux politiques seulement :
- `local_only` : aucun hint provider ;
- `coarsened_only` : seul un `provider_hint` distinct peut être exposé.

Le chemin externe existant pseudonymisation → anonymisation → DLP → processor policy reste inchangé et n'est pas utilisé par ce shadow lot.

## Verification structurelle

Le verifier shadow refuse :
- token inconnu ;
- token requis absent ;
- valeur locale exacte déjà présente dans la réponse candidate ;
- nouvelle valeur clinique chiffrée avec unité hors token ;
- token non résolu après réinjection.

Il ne prétend pas vérifier à lui seul l'équivalence sémantique clinique. Les verifiers par famille restent l'autorité pour le sens.

## Doctrine

**IAMINA décide. Le LLM formule. IAMINA vérifie.**

Le LLM n'est ni un moteur analytique ni une autorité clinique.

## Hors scope

- appel réel au LLM depuis les routes `AdviceResolution` ;
- changement de réponse patient ;
- changement des règles cliniques ;
- activation de nouvelles données patient externes ;
- suppression d'un privacy gate ;
- certification linguistique native ;
- déploiement Vercel.
