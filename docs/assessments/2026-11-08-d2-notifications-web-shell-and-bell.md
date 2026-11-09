# IAMINA — D2 — Cloche Notifications Web et page autonome

**08/11/2026 | Statut : UI candidate / non déployé / D2 non certifié**

## Décision et frontières

**D2 produit validé :** la cloche supérieure droite ouvre exclusivement les **notifications d'application**, réparties en événementielles et proactives. **D3 :** rappels programmés restent dans la carte en bas de l'accueil avec leur écran /reminders. L'envoi proactif suppose opt-in explicite OFF par défaut, contrôles serveur et sûreté ; ce lot **n'active aucun envoi**.

**GOAL :** réaliser le plus petit changement UI honnête : une vraie route et page /notifications, une cloche vers cette page, sans créer un faux compteur ni une liste inventée.

## BEFORE — code exact

Base : `main@0a096ac195d79b494e8f2722be95c3b54396cd2d`.

- `frontend/lib/features/dashboard/dashboard_premium_screen.dart` : `dashboard-reminders-action` (icône cloche) déclenche `context.go('/reminders')`, malgré la séparation demandée.
- `frontend/lib/modules/diabetes_module.dart` : `/reminders` full-screen, **pas de** `/notifications`.
- `DashboardMyRemindersCard` existe au bas de l'accueil dans les parcours avec et sans mesures et navigue séparément vers /reminders.
- Aucun branchement production prouvé du centre D2 persistant, aucune notification réelle ; [PR D2 politique #1322](https://github.com/hraaaaf/IAMINA-MVP/pull/1322) GREEN technique mais Draft/non fusionnée.

## Implémentation ciblée AFTER

- `frontend/lib/features/notifications/d2_notifications_screen.dart` : page réelle dédiée Notifications avec header et retour vers Accueil, **état de non-activation explicite** FR/EN/AR, style IAMINA, informations séparant D2 des rappels D3 et rappelant la future exigence de consentement proactif. Aucune liste fictive, badge, bouton « tout marquer comme lu » inerte, compteurs arbitraires, API, données santé, consentement simulé ou push.
- `frontend/lib/modules/diabetes_module.dart` : module full-screen `/notifications` distinct de `/reminders`, sous les gates d'authentification/lock du routeur existant.
- `frontend/lib/features/dashboard/dashboard_premium_screen.dart` : l'icône cloche `dashboard-notifications-action` pointe vers `/notifications`, tooltip traduit FR/EN/AR ; `DashboardMyRemindersCard` reste intact.
- `frontend/lib/ui_browser_audit_main.dart` : route additionnelle pour screenshot Chrome **local synthétique uniquement**.
- `frontend/test/features/dashboard/d2_notification_center_web_test.dart` : contrat de route, séparation D3 et test widget vrai header/route/départ-retour en trois langues et aux 390×844, 430×932, 768×1024 et 1280×900.

## SUCCESS / PROOF / FUE

**Critères :** la cloche de l'accueil n'ouvre plus les rappels ; la route Notifications affiche honnêtement l'indisponibilité ; sortie revient à Accueil ; la carte D3 et son accès /reminders ne régressent pas ; tout reste lisible/tappable et FR/AR RTL.

**PREUVES à lire avant verdict :** exact HEAD PR, fichier diff, Flutter analyze/tests/build et, si possible, screenshot Chrome BEFORE → AFTER aux mêmes viewports. Chaque test échoué est un refus de certification à diagnostiquer, jamais une raison de supprimer l'assertion.

**Limites :** les tests widget avec base **synthétique en mémoire** ne remplacent ni un E2E hébergé authentifié, ni un test de persistance D2, ni la revue des consentements/privacy, ni la certification clinique. Une maquette d'état vide sur `/notifications` n'est **pas** une inbox fonctionnelle ; le libellé reste « non activée ». Ne pas utiliser la PR comme preuve d'émission de notifications.

## Scope et release gates

Aucune mutation Neon, migration C7, donnée patient réelle, CGM D1/D25, changement de D3, fusion, Vercel Preview/Production, API d'envoi, registre de consentement, scheduler ou permission push. D2 reste **NO-GO patient** ; la PR UI doit rester Draft jusqu'à FUE et revue des garde-fous.

**NEXT exact :** CI et captures du code final, correction des défauts révélés, vérification accessibilité FR/AR, puis sous-lot D2 de sources d'événements attestés, consentement/identité/isolement et boîte patient réelle. Le futur inbox restera OFF jusqu'à certification indépendante.

**Notion canonique :** https://app.notion.com/p/3df77c66336281f5b308ec17f7f0a63b
