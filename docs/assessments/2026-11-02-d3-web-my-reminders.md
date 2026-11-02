# IAMINA — D3 Web : Mes rappels sur Accueil

Date : 2026-11-02. Base vérifiée : `main@9570e4c695844aa7dd5e79d9da0e80d4b8c7dc5c`.
Branche : `feat/d3-web-my-reminders-20261102`.
État : **CANDIDAT — tests et preuve navigateur à certifier**. Aucune Preview/Production déployée dans ce lot.

## Décision / Goal / Succès / Preuve
**Décision D3 (registre du 08/10, option A)** : remplacer `Your next step` sur l'Accueil par **Mes rappels**, 2 à 3 prochaines échéances réelles et ordonnées, **Voir tout** ouvrant la liste, **Aucun rappel configuré** → **Créer un rappel**. Rappels planifiés distincts des notifications proactives/cloche (D2).

**Goal** : un bloc réellement branché au coffre local sélectionné, sur Home à la place de l'ancien bloc de prochaine action, sans décaler la Tendance initiale, ni données démo ou réseau.

**Succès attendu** :
- Home avec mesures : Tendance → Insights → Mes rappels (mobile) ; Tendance → Insights + Mes rappels côte à côte (desktop). Home sans mesure : carte après la première mesure CTA, sans faux patient.
- Vrais rappels **activés** et de date future (limite 3) par `dueAt` croissant, puis `id` ; titre et échéance lisibles en FR/EN/AR et RTL.
- Si aucun enregistré : état vide et **Créer un rappel**, avec bouton **Voir tout**. Si uniquement passés/inactifs : aucun « à venir » inventé.
- Navigation réelle vers `/reminders`, accessible au clavier, touch, focus. La source est `AppDatabase.watchReminders()`, et le `StreamBuilder` est réinitialisé par `ObjectKey(database)` lors d'un changement de coffre A→B→A.

**Preuve exigée** : Flutter analyze/tests/build PWA SHA exact ; tests A→B→A, filtrage/tri/limite3, état vide/navigation, FR/EN/AR ; capture BEFORE→AFTER Chrome vraie Home aux mêmes 390×844 / 768×1024 / 1280×900 FR/AR ; contrôle visuel et accessibilité, recette Preview autorisée par le propriétaire ; puis merge, postmerge, Production sur autorisation distincte.

## BEFORE / référence / AFTER
**BEFORE réel code** : `dashboard_responsive_sections.dart` contient `DashboardTrendSection`, `DashboardInsightSection`, `DashboardNextActionSection` ; dernier propose `Your next step` sous forme d'action évaluée. L'ancienne PR D3 #1137 introduit *seulement* un compteur de rappels **après** les sections, donc ne remplace pas `Your next step` ni ne montre 2–3 échéances ; elle n'est pas fusionnée.

**Mockup approuvé / cible** : garder Tendance inchangée, puis dans l'emplacement de l'ancien bloc `Your next step`, une carte sobre **Mes rappels** (icône agenda, bouton **Voir tout** en haut à droite), lignes « Titre du rappel — date + heure », maximum trois. Carte vide « Aucun rappel configuré » + « Créer un rappel ». En largeur ≥760, carte adjacente à Insights ; sous 760, carte sous Insights. Sur Home vierge, carte indépendante placée sous la CTA première mesure.

**AFTER code candidat** :
- `dashboard_my_reminders_card.dart` : cartes réelle/locale, 0/1/2/3 prochaines échéances, state loading/error, action gestion, FR/EN/AR/RTL, adaptation patient.
- `dashboard_responsive_sections.dart` : remplacement de `DashboardNextActionSection` en conservant Tendance/Insight ;
- `dashboard_premium_screen.dart` : accès aux rappels même sans relevé glycémique ;
- tests ciblés `dashboard_my_reminders_card_test.dart`.

## Limites / sécurité
Le schéma `ReminderData` actuel contient `title`, `dueAt`, `enabled`, `createdAt` uniquement. **Aucun champ d'accomplissement ni règle de récurrence** : l'application ne peut pas marquer une occurrence accomplie ni calculer la suivante sans une évolution de schéma et décision dédiée ; ne rien inventer. Échéances affichées à l'heure locale du navigateur avec `toLocal()`. Les titres sont visibles sur l'Accueil à la demande explicite du propriétaire ; aucun push, écran verrouillé, démo, backend ni API externe ajoutés. Un futur audit de confidentialité doit considérer le partage d'écran/appareil et le verrou local, hors du périmètre du présent écran.

**D2** : la cloche de l'ancien header route encore vers `/reminders` ; c'est une dette distincte D2 (l'utilisateur a décidé de réserver la cloche aux notifications). Ne pas affirmer D2 corrigée. Ne pas modifier les décisions D12, D13, D18 ni D22.

## Gates / Next
- Vérifier CI sur le commit exact, diagnostiquer et corriger tout échec sans supprimer une assertion.
- Capturer BEFORE/AFTER avec une fixture locale synthétique identique (vraie Home, pas seulement test widget), FR/AR et mêmes viewports ; attribuer score seulement après lecture des images.
- Exiger autorisation explicite **Preview** avant tout Vercel et recette utilisateur ; aucune production par défaut.
- Traiter les PR D3 antérieures #1085 et #1137 comme candidates historiques / supplantées seulement après validation du nouveau candidat.
