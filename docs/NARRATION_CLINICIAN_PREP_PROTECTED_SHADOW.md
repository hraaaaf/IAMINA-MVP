# IAMINA — CLINICIAN_PREP Protected Narration Shadow

Base de préparation : Hardening C.

## Goal

Préparer la première rule family à une narration native contrôlée sans affaiblir son corps clinique déterministe.

## Family

`CLINICIAN_PREP`.

## Contrat

Le corps clinique exact reste celui produit par `resolve_clinician_prep_from_brief()`.

Le futur provider :
- ne reçoit pas ce corps ;
- reçoit uniquement le body token opaque de Hardening C ;
- peut générer un wrapper relationnel court ;
- n'a aucune autorité clinique.

Après réinjection locale :
- le body doit être présent exactement une fois ;
- le body lui-même reste validé par le verifier CLINICIAN_PREP V1 exact-copy ;
- le wrapper est vérifié séparément.

## Wrapper autorisé

Exemples de classe autorisée :
- « D'accord, on fait simple. »
- « Bien sûr. »
- équivalent naturel local sans contenu clinique.

## Wrapper interdit

Le wrapper est rejeté s'il :
- dépasse 120 caractères ;
- contient un chiffre ;
- contient du vocabulaire clinique explicite ;
- ajoute diagnostic, traitement, dose, urgence, symptôme ou fait clinique.

En cas d'échec :
`fallback = resolution.reply` exact.

## Egress

Groq reste `PENDING` dans `core.ai_processor_policy`.

Les preuves E1–E6 de `docs/privacy/GROQ_PATIENT_EGRESS_EVIDENCE.md` restent manquantes.

Conséquence :
- aucune activation provider externe sur patient authentifié ;
- aucune tentative de contourner processor policy ;
- prochain benchmark éventuel = **synthetic-only** ;
- patient runtime reste déterministe.

## Validation avant shadow provider synthétique

- Hardening C mergé + post-merge vert ;
- tests du wrapper verifier verts ;
- provider prompt ne contient aucune donnée patient ;
- coût sous plafond benchmark autorisé ;
- output passe body-token verifier + wrapper verifier.

## Hors scope

- patient egress réel ;
- Vercel ;
- DB ;
- nouvelle autorité clinique ;
- autres rule families.
