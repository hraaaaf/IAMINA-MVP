# IAMINA WEB — W03 / D3 : rappel local sur l'Accueil, port sur main actuel

Date : 20 octobre 2026. Base : `main`, branche `feat/w03-d03-reminders-current-main-20261020`.
**Statut : CANDIDAT INDÉPENDANT — PR DRAFT, non fusionné, non déployé.** D2 Notifications (PR #1135), W01 auth/Neon (PR #1128) et W02 restent isolés.

## Goal → succès → preuve

**Goal exact :** afficher sur le Dashboard Web un accès clair aux rappels réellement enregistrés dans le coffre local du patient, immédiatement **après** la section clinique Tendance, sans repousser cette section dans le premier viewport mobile, sans montrer des titres privés sur l'Accueil.

**Succès observable :** la carte de rappel montre correctement 0/1/N actifs, distingue chargement/erreur, respecte FR/EN/AR et RTL, ouvre `/reminders`. Elle ne doit jamais afficher des données de l'utilisateur A pendant une transition vers le coffre de B ; pas de push ni réseau pour cette carte.

**Preuve nécessaire :** Flutter analyze/tests/CI SHA exact ; test A→B→A + Drift mémoire FR/EN/AR ; captures réelles et comparaison BEFORE/AFTER aux mêmes états 390×844, 768×1024, 1280×900 ; navigation clavier/lecteur d'écran ; revue indépendante. Les tests sont une preuve de contrat, non une certification médicale.

## BEFORE → mockup → AFTER (code candidat)

**BEFORE :** sur le `main` actuel, le Dashboard contient `DashboardResponsiveSections` (Tendance) puis `_DataTools`, sans résumé des rappels entre les deux. L'action icône de raccourci Rappels demeure dans la barre ; pas de résumé des rappels actifs en Home. L'ancienne PR D3 [#1085](https://github.com/hraaaaf/IAMINA-MVP/pull/1085) est 35 commits derrière `main` malgré **8/8 CI SUCCESS** sur son propre SHA `c462fa987aa27fa5e44b10897c3c0ed9731881f7`. Ne pas réutiliser ce SHA comme preuve pour le nouveau port.

**Reference / mockup écrit :** « Tendance [inchangée] → 18 px → petite carte blanche Rappels [icône agenda, statut local 0/1/N, chevron directionnel] → 22 px → Outils ». Compteur agrégé, pas de nom de médicament ni de notification système présentée comme livrée. Style/marge locaux du Dashboard conservés.

**AFTER candidat :** nouveau `dashboard_reminders_summary_card.dart`, repris à l'identique d'une PR D3 testée, abonnement `AppDatabase.watchReminders()` rebondi lors du changement de fournisseur `AppDatabase`; `StreamBuilder` basé sur `ObjectKey(_activeDatabase)` pour éviter l'affichage de la capture d'un autre patient. Dashboard insère la carte **après** `DashboardResponsiveSections`. Tests de retour A→B→A, statut 0/1, titre sensible absent, désactivation/reactivation, navigation vers `/reminders`, FR/EN/AR + ordre Tendance. Aucun backend/API, AI, notifications OS, Vercel ou Neon modifié.

**Écart de périmètre à ne pas masquer :** D3 complète prévoit 2–3 rappels effectivement programmés sur Home ; cette carte affiche seulement leur **nombre** pour éviter d'exposer des intitulés médicaux sur l'Accueil. La pertinence/affichage de 2–3 événements n'est **pas implémentée ici** et doit faire l'objet d'un sous-lot UX autorisé ; ne pas certifier D3 entière sur cette carte.

## Validation et séquence

1. Vérifier les tests Flutter + CI exact nouveau HEAD, réparer tout échec.
2. Inspecter les captures Chrome du rendu AFTER, comparer aux BEFORE mêmes fixtures/viewports (source [issue D3 #950](https://github.com/hraaaaf/IAMINA-MVP/issues/950)). Score visuel suspendu sans Target↔Render effectif ; français puis arabe RTL.
3. Examiner compatibilité future avec D2 PR #1135 qui modifie aussi `dashboard_premium_screen.dart`. Ne pas fusionner deux PR indépendantes avec une collision non résolue.
4. Reporter certification sécurité/Neon globale à la fin des décisions comme demandé, sans prétendre libérer W01/W02. Aucune opération Production et aucun déploiement Vercel sans autorisation expresse.

**Next exact :** ouvrir la PR DRAFT du port puis relever les runs du HEAD ; continuer une décision W03 indépendante pendant leur exécution.
