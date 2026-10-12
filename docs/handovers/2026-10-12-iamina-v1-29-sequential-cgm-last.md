# IAMINA V1 — Exécution séquentielle des 29 décisions, CGM en dernier

**Consigne explicite du propriétaire (12 octobre 2026) :** traiter **une décision originale à la fois**, dans l'ordre numérique en décalant les deux décisions de connexion/appareils CGM **#1 et #25 à la toute fin**. Conserver les numéros et l'intitulé canoniques; cela modifie **l'ordre d'exécution**, pas les décisions métier déjà arbitrées ni les états de livraison.

**Source de vérité :** [checklist Notion des 29 décisions](https://app.notion.com/p/3f477c6633628161aba2c43201805156) et [roadmap générale](../ROADMAP.md). Programme P5 séparé (6/12 = 50 % historique). **État initial vérifié :** 29/29 décisions produit arbitrées, **0/29 totalement livrées** au dernier registre, #19/#22/#28 techniquement en cours ; **aucune case « terminée » ajoutée** par ce changement d'ordre. **0 client**, local-first.

## Ordre de passage — 29 étapes, sans renumérotation

| Rang | Décision | Libellé canonique | État au changement de méthode |
| --- | --- | --- | --- |
| 01 | #2 | Notifications proactives et messages IAmina sous contrôle | AUDIT OUVERT — [#947](https://github.com/hraaaaf/IAMINA-MVP/issues/947), PAS LIVRÉE |
| 02 | #3 | Boîte « Rappels » sur l’Accueil | À TRAITER |
| 03 | #4 | Exports Reports déterministes, multi-formats | À TRAITER |
| 04 | #5 | Pays d’utilisation dans l’onboarding | À TRAITER |
| 05 | #6 | Supprimer le sélecteur de ton ; voix IAMINA stable | À TRAITER |
| 06 | #7 | Type de diabète et traitements modifiables | À TRAITER |
| 07 | #8 | Unité suggérée selon pays, librement modifiable | À TRAITER |
| 08 | #9 | Ne pas relancer l’onboarding des comptes existants | À TRAITER |
| 09 | #10 | Récupération de compte claire ; app-lock optionnel | À TRAITER |
| 10 | #11 | Vrai compte neuf sans fausses données démo | À TRAITER |
| 11 | #12 | Smart Slider de saisie glycémique | À TRAITER |
| 12 | #13 | Avertir avant abandon d'une saisie non enregistrée | À TRAITER |
| 13 | #14 | Photo repas : reconnaissance suggérée, incertaine, confirmable | À TRAITER |
| 14 | #15 | Repas multimodal, portions naturelles, brouillon unique | À TRAITER |
| 15 | #16 | Sélection et copie du texte pertinent | À TRAITER |
| 16 | #17 | Détails techniques repliés sous icône « i » | À TRAITER |
| 17 | #18 | Profil progressif : poids, âge et genre minimisés | À TRAITER |
| 18 | #19 | Inventorier, corriger et certifier calculs et autorité clinique | TRAVAUX TECHNIQUES PARTIELS, DÉCISION OUVERTE |
| 19 | #20 | Évolution du poids et notifications facultatives | À TRAITER |
| 20 | #21 | Ramadan masqué par feature flag | À TRAITER |
| 21 | #22 | Choix de l’unité avant les cibles ; cohérence de tous les écrans | TRAVAUX TECHNIQUES PARTIELS, DÉCISION OUVERTE |
| 22 | #23 | Préférences générales et IAmina hiérarchisées | À TRAITER |
| 23 | #24 | Paramètres IA et opt-out effectif | À TRAITER |
| 24 | #26 | Confidentialité, danger zone et déconnexion | À TRAITER |
| 25 | #27 | Avatar IAmina flottant sur Accueil seulement (maquette #3 validée) | À TRAITER |
| 26 | #28 | Intelligence analytique avant chat ; privacy, guidage, UI et ML shadow | TRAVAUX TECHNIQUES PARTIELS, DÉCISION OUVERTE |
| 27 | #29 | Feedback des premiers utilisateurs | À TRAITER |
| 28 | #1 | Connexion CGM native ; Nightscout sans auto-hébergement obligatoire | À TRAITER |
| 29 | #25 | Profil « Données et appareils » et état des connexions | À TRAITER |

**CGM en dernier :** #1 est le hub de connexion CGM ; #25 gère « Données et appareils » et l'état des connexions, couplé aux dispositifs. Les autres décisions doivent rester utilisables **sans CGM** ; tout graphe/AGP, prédiction ou métrique exigeant un capteur certifié doit rester **indisponible/fail-closed**, et non rempli avec des mesures manuelles. Une simple donnée de journal ne confère jamais autorité CGM. Si une sécurité immédiate dépend d'une correction du pipeline CGM, exécuter la protection fail-closed sans ouvrir le lot final d'intégration.

## Cycle de travail obligatoire pour chaque décision

1. **Baseline** : lire intention arbitrée, écran/code actuel, branches/PRs déjà pertinentes, preuves et dépendances. Pour tout changement visuel, conserver **BEFORE sur les mêmes viewports, mockup/objectif et test d'accessibilité**.
2. **Goal = résultat exact / Succès = critère observable / Preuve = tests, diff et comportement reproductibles**. Ne pas extrapoler une CI d'un ancien HEAD.
3. **Implémenter le strict nécessaire** dans une PR/branche identifiable ; tests ciblés puis CI du SHA exact, examen sécurité, confidentialité, données synthétiques et FR/AR/Darija selon portée. Ne pas créer de nouvelles décisions médicales ou d'IA egress implicites.
4. **AFTER** mêmes conditions, comparaison, score visuel uniquement sur preuve, double-check adversarial, docs canoniques cohérentes ; pas de score 10/10 fictif.
5. **Clôture seulement avec preuves proportionnées**, revue requise, merge **autorisé explicitement** et post-merge vérifié si livraison attendue ; Vercel nécessite **autorisation distincte**. Sans approbation, statut **READY_FOR_HUMAN_GATE / NON LIVRÉ**, puis passer au numéro suivant pour tout travail indépendant.
6. À la fin de chaque étape : mettre à jour cette table et la checklist Notion avec **référence SHA, CI, capture/test, limites, Next exact**. Les cas à validation humaine restent ouverts et seront repris avant release et avant toute donnée patient.


### Décision #2 — audit/protection API en cours, preuve distincte

**Baseline vérifiée par SHA sur `main` et sur #941** : `proactive.py`, `proactive_preview.py`, `proactive_intelligence.py`, `proactive_insight.py` et les tests existants ont les mêmes blob SHA. La lecture seule GET `/api/v1/proactive-insights/preview/` ne consomme pas d'attention ; POST `/evaluate/` met à jour un état *in-app*, **pas un push système**. Les rappels Drift locaux restent séparés de ces observations ; l'interface rappelle que les notifications système ne sont pas actives.

**Implémentation autorisée et limitée** : [PR DRAFT #949](https://github.com/hraaaaf/IAMINA-MVP/pull/949), HEAD `b0e20a4bcda85c4215a13d249193736608ddb053`, sur `main` : un seul fichier de **tests Django synthétiques**, contrôlant GET/POST anonymes, tentative de substitution `patient_id` par query/body, GET repeatable non mutable, POST exact-once sans second surfacing. **Aucun code runtime patient/Flutter, aucun push, consentement ou clinique changé.** [Migration drift #38317586482](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38317586482) et [CI #38317586620](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38317586620) ont démarré mais **leur verdict n'est pas transférable du parent**.

La PR dépendante #948 a été **fermée non mergée** en faveur de #949, car les workflows du dépôt écoutent `main/dev` et non sa branche cible. Le vrai sujet reste [issue #947](https://github.com/hraaaaf/IAMINA-MVP/issues/947).

**Restant pour #2** : vérifier tests SQLite/PG exact-HEAD, puis inventorier l'entrée notifications côté UI, la séparation notifications/rappels/chat et les droits de notification ; dossier UI BEFORE / mockup / AFTER aux mêmes viewports avant tout changement visuel ; revue privacy/clinique et permission explicite avant merge. **Décision #2 OPEN / NON LIVRÉE** ; passage #3 seulement après clôture réelle ou blocage humain/non technique justifié. CGM #1/#25 reste à la fin.


### Décision #2 — deuxième étape, correction visuelle sous contrôle (12 octobre 2026)

**BEFORE + référence écrite AVANT patch**, détails dans [issue #947](https://github.com/hraaaaf/IAMINA-MVP/issues/947) : [Chrome Dashboard responsive #38252290934](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290934) artifact [#11749017316](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290934/artifacts/11749017316), screenshots mobile 390×844, tablette 768×1024, desktop 1280×900. Bouton `dashboard-reminders-action` vers `/reminders` représenté à tort par cloche notifications. Blob Flutter dashboard même SHA sur `main` et #941. **Cible design** : garder cercle 48×48 identique, icône Material `event_note_outlined` comme écran Rappels, tooltip accessible « Rappels / Reminders / التذكيرات ». Aucune cloche notifications artificielle.

**Nouveau HEAD candidate [PR #949](https://github.com/hraaaaf/IAMINA-MVP/pull/949) `e6563d8ca76dba6abe06017ac459433d59c11309`** : ajoute l'icône appropriée/tooltip et un test Flutter source (en complément des régressions API authentification/anti-rejeu). [CI complète #38318106071](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38318106071) et [vraie capture Dashboard #38318106112](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38318106112) avec 7 autres workflows déclenchés. **Tous résultats en cours/queued au lancement; aucune certification du nouveau SHA.** La preuve antérieure #949 `b0e20a4` (2/2 workflows success) reste sur ce SHA ancien et ne suffit plus. L'UI AFTER, la comparaison visuelle même viewport, le score, les contrôles Flutter/JS/RTL et les revues sont **à faire / vérifier**. Aucun changement de logique clinique, push OS, LLM, consentement ou SQL.

**Statut réel :** #2 **EN COURS**, non livrée (notification inbox, consentement, opt-out, chat et vraies notifications encore ouverts). Next exact : verdict exact-HEAD 9 workflows, inspecter artefact 9 PNG et comparer BEFORE/AFTER; corriger si fail, puis décider suite indépendante en maintenant gates humains. #1 et #25 CGM dernières.

## Next exact : décision #2 — notifications et messages IAmina

**Intention canonique :** icône notifications réservée aux événements d'information, **rappels séparés** (la boîte Accueil fait partie de #3) ; proactivité IAmina strictement contrôlée, éventuel message chat lié à une notification, préférences/opt-in/opt-out, pas de prédiction médicale non validée. La décision #2 correspond au lot V1-08 mais peut être étudiée sans l'ensemble de V1-08.

**Audit commencé :** [issue #947](https://github.com/hraaaaf/IAMINA-MVP/issues/947), Goal et critères inscrits ; inspection des composants de rappels locaux, `proactive_preview`, `proactive_intelligence` et API GET/POST sur PR DRAFT #941. Rappels explicitement locaux, notifications OS non activées ; aucun nouveau push, prédiction, envoi patient, merge ni déploiement. Les autres chemins sont encore à auditer.

**Premier travail autorisé** : inventorier code et états de notifications, rappels, opt-out, proactivité et ingestion messages, puis établir une matrice d'oracles synthétiques (zéro événement, opt-out, pas de source, urgence, répétition, consentement retiré, isolation patient) et la séparation notification/rappel/chat. **Aucun envoi réel, push, conseil médical, prédiction, appel LLM ou déploiement** avant preuve et gates qualifiés.

**Exceptions préservées :** V1-01/CAL-09/10/11/12 = [gate qualifié #946](https://github.com/hraaaaf/IAMINA-MVP/issues/946), PR #945 DRAFT, PDF clinique OFF ; V1-02 [#921](https://github.com/hraaaaf/IAMINA-MVP/pull/921) dernier HEAD `ef93edf16746cee5cea4f15887495c05278b153f`, tests backend CI [#38315876015](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38315876015) SUCCESS + migration drift [#38315876021](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38315876021) SUCCESS, non fusionné ; V1-03 PR #941 DRAFT, non livré. Les trois peuvent servir de base/protection, mais ne changent pas l'ordre séquentiel.

**Fichier canonique d'exécution :** `docs/handovers/2026-10-12-iamina-v1-29-sequential-cgm-last.md` (ce document) — **0/29 livrées à la date de mise en place**.
