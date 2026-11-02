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


## 01/11/2026 — décision propriétaire D22 G2–G5 produit approuvée (NON clinique)

**Déclaration explicite :** « Je valide les quatre principes produit G2–G5 de D22. Poursuis les travaux techniques autorisés, sans considérer cela comme une certification clinique et sans déploiement Vercel. »

**État actuel :** G2, G3, G4, G5 = APPROUVÉ AU NIVEAU PRODUIT UNIQUEMENT. La table historique « toutes PENDING » ci-dessus reste la preuve du statut initial ; cette section met à jour seulement l'autorité produit.

- **G2 / Owner PRODUCT_APPROVED :** aucune cible individuelle présentée comme prescrite ou médicalement validée sans patient, source/autorité clinique traçable et confirmation. **Clinicien qualifié : PENDING.**
- **G3 / Owner PRODUCT_APPROVED :** préserver brutes les anciennes valeurs d'unité/provenance inconnue ; aucun reclassement, conversion ou attribution d'autorité silencieux. **Clinicien et privacy/migration : PENDING.**
- **G4 / Owner PRODUCT_APPROVED :** unité d'affichage sans réécriture silencieuse ; contrat unique documenté pour la conversion/les arrondis. **Facteur exact 18.018 vs 18.016 vs 18.0, règles d'édition et validation clinique : PENDING.**
- **G5 / Owner PRODUCT_APPROVED :** aucune classification « dans/hors cible » sans objectif personnel vérifié ; aucune mesure de temps dans la cible CGM déduite de relevés manuels épars. **Contrat des métriques et revue clinique : PENDING.**

**Restent à autoriser par autorités qualifiées :** G1 unité source/canonique, G2–G5 détails cliniques, G6 FR/AR/RTL et terminologie, G7 DB/privacy/rollback/identité. La déclaration propriétaire ne prouve aucune qualification d'endocrinologie et ne remplace pas les signatures spécialisées. Ni merge, ni modification patient, ni déploiement Vercel autorisés.

**Traçabilité :** [PR #1213 — décision propriétaire](https://github.com/hraaaaf/IAMINA-MVP/pull/1213#issuecomment-6560126684) et Notion Chantier B. Des oracles synthétiques sans intégration runtime peuvent désormais être renforcés ; ils ne prouvent pas le comportement patient ni la FUE.


## 02/11/2026 — Revise mandatory seven-signature gate after primary-source research

**Decision: replace a blanket requirement for seven formal G1–G7 signatures with a risk/scope-based release policy.** This section supersedes earlier statements in this file requiring a qualified written signature on *every* G1–G7 gate before *any* D22 code can merge or be released. It does **not** retroactively approve patient-specific targets, migration, privacy controls, or clinical algorithms. Explicit owner authorization for merge and Vercel production deployment was granted in the conversation on 02/11/2026; authorization to execute does not itself prove release readiness.

### Primary references actually consulted
- American Diabetes Association, *Standards of Care in Diabetes—2026*, section 6, Recommendations 6.3–6.9: glycemic goals must be individualized; published TIR 70–180 mg/dL (3.9–10.0 mmol/L) applies to many nonpregnant adults and is NOT automatically an individual's prescribed target. https://doi.org/10.2337/dc26-s006
- Battelino et al., *International Consensus on Time in Range* (2019): standardized CGM metrics and recommended ~14-day window with at least ~70% data availability for interpretation. A percentage of manual spot checks is **not CGM time in range**. https://diabetesjournals.org/care/article/42/8/1593/36184/Clinical-Targets-for-Continuous-Glucose
- NIST Chemistry WebBook, glucose C6H12O6, molecular weight 180.1559 g/mol: mathematical conversion `1 mmol/L = 18.01559 mg/dL` by unit arithmetic. This documents the candidate arithmetic, **not the software-wide approved rounding/serialization policy**. https://webbook.nist.gov/cgi/cbook.cgi?ID=50997
- FDA January 2026 Clinical Decision Support Software guidance: software qualification depends on *intended function* and whether users can independently evaluate recommendations; it does **not** prescribe seven named D22 signatories. This is U.S. context, NOT a Moroccan regulatory determination. https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software
- Morocco, Law 09-08 and CNDP notices: health information processing can require formal CNDP authorization/notification according to purpose, legal basis and implementation, subject to Article 22 and related rules. **Regulatory authorization is distinct from internal engineering signatures.** Check the project's existing CNDP status separately; do not infer that it was obtained or that this unchanged-purpose patch automatically requires a new one. https://www.cndp.ma/conditions/ and https://www.cndp.ma/images/lois/Loi-09-08-Fr.pdf

### Binding engineering rules — apply without seven specialist signatures for fail-closed mitigation only

1. **G1 source unit:** never convert, classify or relabel a quantity without a known source unit. Keep original `rawInput`, explicitly typed `sourceUnit`, owner and provenance distinct from `unitPreference`. Unknown legacy `70/180` stays stored without inference; no automatic correction.
2. **G4 arithmetic:** document and regression-test the mathematical factor 18.01559 against NIST **in an isolated candidate**; display rounding must never write back into the raw measurement. Reconcile legacy `18.0/18.016/18.018` before connecting candidate to clinical outputs; do not silently change their semantics by a broad replace.
3. **G2/G3 patient target:** source documents establish **general guidance, not personal approval**. Never activate edit, classification or personalized coaching based on an unverified target. A source-reference text alone cannot authenticate its prescriber.
4. **G5 CGM:** do not calculate or label TIR/TAR/TBR as *time* metrics from manual spot measurements. Require verified CGM provenance, sampling window, coverage and approved presentation before enabling CGM-specific output. Existing manual counts are not clinical TIR.
5. **G6 Web UX:** keep the unit selector before the unavailable/unknown-target state, with clear FR/AR/EN language. Do not claim FR/AR real-Chrome, keyboard/zoom or visual score without running them.
6. **G7 data:** **no production schema migration, forced overwrite, target-source backfill, remote data transfer or cross-account restoration** in a fail-closed mitigation release. Preserve patient data, owner scoping and rollback path. Independently check privacy, CNDP/legal basis and live release configuration before altering health-data processing.

### Two distinct GO/NO-GO gates

- **Gate A — fail-closed Web safety patch only (may proceed on engineering evidence + owner's existing explicit merge/prod instruction, not seven signatures):** exact-SHA clean CI; genuine Chrome evidence for affected safe paths; source diff proves no personalized target activation, no new medication advice, no new patient-data processing or actual migration, no manual-CGM TIR; negative tests of legacy and A/B owner scoping; concrete UI baseline and AFTER at the same viewports with comparison; rollback and production project/commit verified. Any missing mandatory visual/privacy/release evidence remains an actual blocker, but **not a missing formal endocrinologist's signature**. Record exact scope in release notes.
- **Gate B — new clinically active targets, reinterpretation of historical data, therapeutic advice, CGM clinical interpretation, schema changes or changed health-data purposes (DO NOT launch under Gate A):** require demonstrated patient-specific provenance and clinical correctness, a documented accountable human clinical review where needed, privacy/regulatory assessment and real migration/rollback testing. Source-based recommendations can inform design but do not on their own authorize individualized medical decisions. Record approvals to the level needed for the actual feature; no artificial requirement for seven distinct signers.

**Current verified status at the time of this decision:** code SHA `0546c6cd6f2a5d149ade7b5f5d52b75c9049d771` had 17/17 GitHub workflows green; scoped Chrome `PASS_PARTIAL` covers F01/F03/English F07, but same-state BEFORE screenshots, FR/AR Chrome, independent UI score and remote privacy/migration evidence are absent. Current D22 patch is a fail-closed candidate and **does not** qualify Gate B. Updating this documentation itself creates a new HEAD: never transfer prior CI verdicts to the new HEAD without checking.

**Next exact:** run/reconcile affected Gate A visual and privacy evidence; only then consider merging and shipping the **restricted fail-closed** Web patch under the owner's existing explicit operation approval. Clinical Gate B remains disabled. No Vercel action while this gate is incompletely evidenced.
