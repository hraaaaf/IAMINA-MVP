# IAMINA — D19 → D22 Web/PWA : fiche d'arbitrage d'autorité clinique (NON APPROUVÉE)

**Établi le 29/10/2026.** Sources relues : `main@278159a2988c860861e24301c6db37588f1b4eb8` et branche D19 [PR #920](https://github.com/hraaaaf/IAMINA-MVP/pull/920) à `81bf4d6ac4e182f3058ca6ff52b504ce8404beb9`. D22 [issue #1165](https://github.com/hraaaaf/IAMINA-MVP/issues/1165), préflight [#1173](https://github.com/hraaaaf/IAMINA-MVP/pull/1173) et closeout [#1174](https://github.com/hraaaaf/IAMINA-MVP/pull/1174) fusionnés. **D19 reste OPEN/DRAFT/non fusionnable, sans revue GitHub enregistrée au relevé.** D22 produit : **OPEN / FUE_NO_GO**.

## Goal / succès / preuve — sous-lot documentaire uniquement

- **Goal :** transformer le blocage D19 en décisions explicites et en critères de tests D22 Web, sans fixer de cible médicale, convertir les dossiers historiques, modifier des algorithmes ou permettre une livraison patient.
- **Succès observables :** table des choix, recommandation technique identifiable, autorité/signature attendues, matrice producer→consumer et oracles négatifs, décisions non approuvées conservées comme `PENDING`, CI et SHA de la PR documentaire.
- **Preuve actuelle :** audit statique des chemins sur les deux SHAs ci-dessus ; aucune observation de patient réel, FUE navigateur ou avis clinique obtenus via cette fiche. L'absence de validation est une limite explicite, pas un GO.

## Source exacte : main ≠ branche clinique D19

| Surface | `main` | Branche D19 #920 (non mergée) | Décision nécessaire |
| --- | --- | --- | --- |
| Formateur `frontend/lib/core/utils/glucose_formatter.dart` | Facteur `18.018`, entrée non normalisée dans ce helper | `18.016`, `isSupportedUnit`, `toMgDl`, `editedToMgDl` et rejet d'unités inconnues | Un seul contrat d'unité, précision, alias, arrondi et intégrité d'édition |
| Onboarding `frontend/lib/features/auth/onboarding_chat_screen.dart` | Sauvegarde `targetRangeLow:70`/`targetRangeHigh:180` indépendamment de `unitPreference` | Aucun fait de certification des cibles hérité de ces nombres | Cible sans preuve d'autorité : ne pas l'inférer |
| Profil `frontend/lib/features/profile/profile_screen.dart` et `profile_screen_presentation.dart` | Cible brute `toStringAsFixed(0)`, sauvegarde brute, unité choisie après le bloc cible | D19 a des correctifs unités sur certaines routes de mesure, mais **ne constitue pas une décision signée sur D22/cibles** | Séparer unité d'affichage, unité de la quantité, provenance cible ; UI unité avant cible |
| Dashboard Premium et Rapports | Comparaisons mesure brute/cibles brutes ; certains affichages divisent par `18.0` | Certaines présentations utilisent `GlucoseFormatter.convert`; code candidat non fusionné | Ne classer qu'avec des cibles autorisées de même dimension et unité ; source de vérité partagée |
| Drift `frontend/lib/data/drift/database.dart` | Bornes cibles numériques avec défauts 70/180 ; préférence d'unité séparée | Aucune décision approuvée permettant d'inférer provenance/unité des lignes historiques | Contrat du legacy inconnu, migration réversible et preuve par patient |

**Important :** les chiffres 70/180 et les résultats numériques de conversion dans les tests sont des *fixtures et des états constatés*, jamais des valeurs à prescrire ni la preuve d'un objectif individuel validé. Le code peut comporter un risque de mauvaise classification ; cela ne constitue pas un incident patient confirmé.

## Décisions à signer — toutes `PENDING`

| ID | Question bloquante | Choix proposés / recommandation de conception NON approuvée | Autorité attendue |
| --- | --- | --- | --- |
| **G1** | Quelle unité fait autorité pour toute quantité (mesure, borne, export, API) ? | **A (préféré techniquement) :** stocker la quantité en mg/dL canonique, avec unité/provenance explicites aux frontières ; **B :** unité typée par quantité. Ne pas confondre `unitPreference` et `sourceUnit`. | Ingénierie + sécurité données + clinicien sur les usages cliniques |
| **G2** | Qui valide une cible individuelle, avec quelles preuves ? | Une cible doit porter `patient_id`, `source/autorité`, `created_at` et statut de confirmation ; sinon **inconnue/non approuvée**. Les nombres par défaut ne prouvent rien. Le statut/UX exact doit être validé. | Clinicien qualifié + responsable produit |
| **G3** | Comment traiter les lignes historiques sans unité/provenance certaine ? | **A (préféré sécurité) :** garder brut, marquer `unknown` et ne pas classifier ni réécrire ; **B :** récupération documentée avec approbation et rollback. **Interdit :** deviner à partir de la valeur, convertir silencieusement ou attribuer une cible par défaut. | Clinicien + privacy + responsable migration |
| **G4** | Quel facteur, arrondi et politique d'édition ? | Harmoniser `18.018` main, `18.016` D19 et `18.0` écrans. Spécifier source du facteur, précision d'affichage et préservation des données brutes si aucune édition réelle. Pas de choix implicite de la PR non fusionnée. | Responsable calcul D19 + clinicien |
| **G5** | Quelles classifications et métriques sont licites ? | Aucune étiquette « dans ma cible / hors cible » sans objectif traçable et unité connue ; distinguer fractions de relevés manuels de CGM TIR. Définir comportement quand cible absente et dans exports/résumés. | Clinicien/endocrinologie + privacy |
| **G6** | Quels textes et interactions Web sont approuvés ? | Unité avant cibles, langue FR/AR/RTL correcte, états « non défini / à confirmer » localisés, message sans prescription. FUE clavier, offline/reload, profils séparés et taille écran réelle. | Clinicien + relecteur linguistique natif + produit/accessibilité |
| **G7** | Quelles garanties avant écriture/migration/synchronisation ? | Schema/version, backup/rollback, audit d'anciennes valeurs, test patient A/B, aucune propagation d'une provenance absente. Décision de release séparée. | Responsable privacy/sécurité/DB + produit |

**Aucune ligne n'est implicitement « approuvée » par un CI vert, le « go » d'exécution technique, le dépôt de cette fiche ou le rôle de développeur.** Ne pas remplir la colonne d'autorité avec un nom fictif.

## Oracles de recette à implémenter *après* G1–G7

| FUE/scénario | Attendu vérifiable | Preuve demandée | Aujourd'hui |
| --- | --- | --- | --- |
| F01 — nouveau compte Web, mmol/L puis reload | choix d'unité conservé, aucune cible individuelle inventée ; unité déterminée avant toute présentation de cible | source→Drift→UI, navigateur FR/AR 390×844 | NOT_RUN |
| F02 — compte avec cible valide et provenance | variation mg/dL→mmol/L→mg/dL sans changement de quantité ni de source ; règles arrondi G4 | oracle numérique exact, reload/offline + UI 768×1024 | NOT_RUN |
| F03 — profil ancien 70/180 à provenance inconnue | ne pas assimiler par défaut à une cible validée, ne pas reclasser mesures automatiquement, ne pas réécrire les nombres bruts | fixture legacy, assertions négatives + migration/rollback | NOT_RUN |
| F04 — édition inchangée d'une mesure arrondie | original brut inchangé après sauvegarde sans changement réel ; alias invalide refusé explicitement | backend et Drift, tests de régression | NOT_RUN |
| F05 — dashboard Premium, rapports, exports, consultation | résultat et libellé cohérents avec même cible approuvée/unité/source ; sans cible, classement indisponible | producer→consumer, screenshots 1280×900, jeu synthétique | NOT_RUN |
| F06 — compte A/logout/compte B + consentement | aucune cible ni donnée transférée entre patients ; invalidité et absence de réseau sans altération | FUE comptes Web, storage et API, logs synthétiques | NOT_RUN |
| F07 — 3 viewports × FR/AR RTL + clavier | scrolling, focus, Tab/Shift+Tab, label unitaires et états vides visibles | **BEFORE → Goal → mockup → AFTER**, mêmes viewports, score visuel | NOT_RUN |

Surfaces potentielles supplémentaires à inventorier avant FUE : historique, ajout/édition d'entrée, graphiques, résumé IA, export PDF/CSV, sauvegarde/synchronisation, CGM et routes API. Les exemples de tests **ne** valent pas exécution du parcours complet. Les pixels BEFORE/AFTER n'existent pas encore.

## Formulaire de décision humaine (ne pas pré-cocher)

- **Clinicien/endocrinologue qualifié :** identité/qualité : `PENDING` ; date et SHA relu : `PENDING` ; G2/G3/G4/G5/G6 : `APPROUVE / MODIFICATIONS DEMANDÉES / REFUSE` = `PENDING` ; source/justification : `PENDING`.
- **Sécurité/confidentialité/DB :** identité : `PENDING` ; G1/G3/G7, preuve d'isolation/rollback : `PENDING`.
- **Revue FR/AR/RTL :** identité/native-language/versions des textes : `PENDING` ; verdict : `PENDING`.
- **Owner produit :** arbitrage G1–G7 à date/SHA fixe : `PENDING` ; autorisation de merge clinique distincte ; autorisation Vercel **non donnée**.
- **Si divergence :** état reste `BLOCKED`, consigner l'objection et réviser la fiche avant tout patch patient.

## Séquence critique restante

1. Attacher cette fiche à [#920](https://github.com/hraaaaf/IAMINA-MVP/pull/920) et [#1165](https://github.com/hraaaaf/IAMINA-MVP/issues/1165) ; intégrer uniquement **documentation** avec CI exact HEAD/postmerge.
2. Obtenir les verdicts humains G1–G7 et leur preuve ; si refus, modifier le contrat sans code patient.
3. Réconcilier la branche D19 (actuellement non fusionnable), découper les correctifs techniques indépendants avec comparaisons à `main`, pas de merge global d'une PR de 59 fichiers sans revue et tests adaptés.
4. D22 Web : captures BEFORE, maquette et implémentation sous contrat approuvé, migrations testées et rollback, tests synthétiques ciblés puis FUE 100 %, FR/AR/RTL 390×844, 768×1024, 1280×900.
5. Certification/examen adversarial, CI exact HEAD, merge approuvé, CI postmerge, closeout canoniques. **Vercel séparé et explicitement autorisé seulement.**

**Résultat de cette fiche :** le gate devient actionnable et vérifiable ; **aucune décision médicale ni D22 fonctionnel n'est validé par ce document**.
