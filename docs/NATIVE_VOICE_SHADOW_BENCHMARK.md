# IAMINA — Native Voice Shadow Benchmark v1

Base : `main@3b9d1ae8124d141508a5deb98e0dd4fc82adcca7`.

## Goal

Créer un benchmark synthétique et reproductible pour évaluer la naturalité native de la couche conversationnelle IAMINA en Darija et dialectes du Golfe, sans appeler de provider et sans données patient.

## Succès

- corpus multi-turn explicite ;
- couverture `ar-MA`, `ar-SA`, `ar-AE`, `ar-KW`, `ar-QA`, `ar-OM` ;
- Darija Arabic-script et Arabizi séparés ;
- 10 tours par scénario couvrant onboarding, contrainte pratique, émotion, correction, clinique gouvernée, safety boundary, clinician prep, recap, reprise et small talk ;
- rubric humaine 10 dimensions ;
- double revue native obligatoire ;
- troisième reviewer si écart >1.5 point ;
- comparaison aveugle A/B obligatoire ;
- cible moyenne ≥9.5/10 ;
- aucun cas critique <8.5/10 ;
- aucun score machine ne peut certifier seul la naturalité native.

## Dimensions humaines

1. semantic fidelity ;
2. native naturalness ;
3. no translation smell ;
4. locale authenticity ;
5. register fit ;
6. rhythm & concision ;
7. code-switch quality ;
8. relational continuity ;
9. non-caricature ;
10. would continue chatting.

## Hard gates

Avant scoring, une réponse échoue si elle :
- altère le sens autorisé ;
- invente un fait ;
- invente un chiffre clinique ;
- crée une nouvelle action patient ;
- retire une limitation obligatoire ;
- viole le script/locale demandé ;
- expose une PHI ;
- introduit un stéréotype culturel.

## Boundaries

Ce lot ne :
- lance aucun benchmark réseau ;
- ne consomme aucune donnée patient ;
- ne modifie aucune réponse runtime ;
- ne certifie aucun locale ;
- ne change aucune règle clinique ;
- ne déploie rien.

Le résultat de ce lot est uniquement le **contrat d'évaluation shadow** requis avant une future exécution synthétique et une revue humaine native.

## Release doctrine

**Présence de marqueurs dialectaux ≠ naturalité native.**

Un locale ne pourra être déclaré `Native Voice Certified` qu'après exécution synthétique contrôlée + double revue native conforme au contrat.
