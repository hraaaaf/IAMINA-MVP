# IAMINA V1 — Exécution séquentielle des 29 décisions, CGM en dernier

**Consigne explicite du propriétaire (12 octobre 2026) :** traiter **une décision originale à la fois**, dans l'ordre numérique en décalant les deux décisions de connexion/appareils CGM **#1 et #25 à la toute fin**. Conserver les numéros et l'intitulé canoniques; cela modifie **l'ordre d'exécution**, pas les décisions métier déjà arbitrées ni les états de livraison.

**Source de vérité :** [checklist Notion des 29 décisions](https://app.notion.com/p/3f477c6633628161aba2c43201805156) et [roadmap générale](../ROADMAP.md). Programme P5 séparé (6/12 = 50 % historique). **État initial vérifié :** 29/29 décisions produit arbitrées, **0/29 totalement livrées** au dernier registre, #19/#22/#28 techniquement en cours ; **aucune case « terminée » ajoutée** par ce changement d'ordre. **0 client**, local-first.

## Ordre de passage — 29 étapes, sans renumérotation

| Rang | Décision | Libellé canonique | État au changement de méthode |
| --- | --- | --- | --- |
| 01 | #2 | Notifications proactives et messages IAmina sous contrôle | AUDIT À OUVRIR |
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

## Next exact : décision #2 — notifications et messages IAmina

**Intention canonique :** icône notifications réservée aux événements d'information, **rappels séparés** (la boîte Accueil fait partie de #3) ; proactivité IAmina strictement contrôlée, éventuel message chat lié à une notification, préférences/opt-in/opt-out, pas de prédiction médicale non validée. La décision #2 correspond au lot V1-08 mais peut être étudiée sans l'ensemble de V1-08.

**Premier travail autorisé** : inventorier code et états de notifications, rappels, opt-out, proactivité et ingestion messages, puis établir une matrice d'oracles synthétiques (zéro événement, opt-out, pas de source, urgence, répétition, consentement retiré, isolation patient) et la séparation notification/rappel/chat. **Aucun envoi réel, push, conseil médical, prédiction, appel LLM ou déploiement** avant preuve et gates qualifiés.

**Exceptions préservées :** V1-01/CAL-09/10/11/12 = [gate qualifié #946](https://github.com/hraaaaf/IAMINA-MVP/issues/946), PR #945 DRAFT, PDF clinique OFF ; V1-02 [#921](https://github.com/hraaaaf/IAMINA-MVP/pull/921) dernier HEAD `ef93edf16746cee5cea4f15887495c05278b153f`, tests backend CI [#38315876015](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38315876015) SUCCESS + migration drift [#38315876021](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38315876021) SUCCESS, non fusionné ; V1-03 PR #941 DRAFT, non livré. Les trois peuvent servir de base/protection, mais ne changent pas l'ordre séquentiel.

**Fichier canonique d'exécution :** `docs/handovers/2026-10-12-iamina-v1-29-sequential-cgm-last.md` (ce document) — **0/29 livrées à la date de mise en place**.
