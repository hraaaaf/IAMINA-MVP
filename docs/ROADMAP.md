# IAMINA — ROADMAP UNIQUE · DÉCISIONS RESTANTES · WEB/PWA

**Date de consolidation : 10 novembre 2026.** **Statut : candidat documentaire, non fusionné, non déployé.** Cette page constitue l'unique plan d'exécution. Les numéros D1–D12 ci-dessous sont **renumérotés par importance et dépendances**, et remplacent la numérotation prospective historique. Un seul focus actif à la fois. Ne pas compter un travail simplement préparé, ni refaire une fonctionnalité déjà livrée et acceptée.

**Règles non négociables :** sécurité → exactitude → preuve → efficacité. Web/PWA uniquement ; FR/AR RTL ; 390, 430, 768 et 1280 px. Aucune donnée patient réelle en QA. Aucun déploiement Vercel, y compris Preview, sans autorisation explicite distincte. Une PR fusionnée ne prouve pas automatiquement la certification médicale, et une CI verte ne prouve pas un fonctionnement patient réel.

## ROADMAP ACTIVE — 12 DÉCISIONS, PAR PRIORITÉ

### D1 — Sécuriser le coffre Web, l'identité et les données historiques
**Importance : P0 / BLOQUANT.** *Anciens identifiants : D18, D9, D10, D26, résidus D7, W01/W02.*

**GOAL :** conserver sans perte les coffres legacy (y compris vieux clients PWA/offline), interdire l'attribution à un mauvais compte et établir une récupération volontaire après preuve de possession. Séparer connexion distante et déverrouillage local ; app-lock, révocation et effacement selon une politique validée.

**SUCCESS :** aucune écriture concurrente par ancien onglet ; aucun transfert implicite du coffre A vers B ; A→B→A, logout, backup/restore, coffre chiffré et migration éventuelle sans perte démontrés ; aucune activation clinique prématurée.

**PROOF :** tests Drift/IndexedDB/VFS, Chrome/Safari, PG16 isolé, API réelle sur comptes fictifs, cas négatifs + captures, approbations privacy/sécurité. [D18 #1265](https://github.com/hraaaaf/IAMINA-MVP/pull/1265), [D9 #1159](https://github.com/hraaaaf/IAMINA-MVP/pull/1159), [D10 #1246](https://github.com/hraaaaf/IAMINA-MVP/pull/1246) Draft. **D18 SAFE-HOLD / PATIENT NO-GO ; D7 hosted C01–C05 et approbations clinique/privacy encore ouverts.**

### D2 — Visiteur sans compte, authentification avant action métier
**Importance : P0.** *Anciens D37, D30 (compatibilité seulement). Dépend de D1 pour toute persistance.*

**GOAL :** permettre de parcourir tout le shell Web/PWA à vide ou avec exemples explicitement fictifs ; demander une connexion/inscription dès qu'une action requiert lecture/écriture santé, coffre, API métier ou service externe. **Pas de limite arbitraire de cinq minutes.**

**SUCCESS :** aucun coffre ni données de santé persistantes pour invité, aucune lecture/API métier automatique, connexion au point d'usage puis retour à la tâche ; les coffres anciens restent hors accès invité.

**PROOF :** matrice routeur + DB + API, absence d'auto-fetch, tests direct URL/offline/anciens onglets, FR/AR 390/430/768/1280, A→B→A, captures BEFORE/AFTER. Gardes fail-closed.

### D3 — Consentements IA séparés et révocation immédiate
**Importance : P0.** *Anciens D24 et D26.*

**GOAL :** consentements indépendants OFF par défaut pour photo, habitudes et compagnon ; choix réversible et vérifié serveur, finalité explicitée, minimisation des données, contrôle des requêtes concurrentes.

**SUCCESS :** un retrait bloque immédiatement toute nouvelle sortie IA, sans réactivation d'un accord ancien ; aucune fuite A/B ; saisie manuelle utilisable avec IA OFF.

**PROOF :** tests négatifs Web/API, egress, révocation durant une requête, revue privacy ; [#1244](https://github.com/hraaaaf/IAMINA-MVP/pull/1244) Draft. Dépend de D1 pour la session fiable.

### D4 — Saisie fiable, brouillon récupérable et sauvegarde unique
**Importance : P1.** *Anciens D13, D15 manuel, résidu D12.*

**GOAL :** une écriture clinique seulement après Save explicite ; protéger contre retour, retry, double clic, perte réseau et navigation ; brouillon récupérable uniquement avec compte protégé.

**SUCCESS :** 1 Save = 1 entrée ; invalides refusées ; aucune donnée clinique invitée ; anti-doublon et restauration cohérents.

**PROOF :** vrai Save Drift, tests FR/AR, offline, multi-onglets, A/B ; [D13 #1250](https://github.com/hraaaaf/IAMINA-MVP/pull/1250) Draft. [D12 #1251](https://github.com/hraaaaf/IAMINA-MVP/pull/1251) fusionnée vers branche D13 : **ne rapatrier que le delta absent de main**, pas refaire le travail livré. Dépend de D1–D2.

### D5 — Validation scientifique et autorité clinique
**Importance : P1 / GATE TRANSVERSAL.** *Anciens D32, résidus D19, D28 et D20.*

**GOAL :** vérifier règles déterministes, unités, périodes, arrondis, données manquantes, mesures capillaires/CGM, tendances et qualité des preuves ; aucune recommandation thérapeutique non autorisée.

**SUCCESS :** calculs vérifiables par oracles indépendants et validation clinique qualifiée ; aucun diagnostic, dose ni adaptation de traitement inventés.

**PROOF :** matrice G1–G7, tests Flutter/backend, dossiers de source, avis médical ; [#920](https://github.com/hraaaaf/IAMINA-MVP/pull/920) Draft. **La livraison technique de l'ancien D22 est fusionnée : ne pas la refaire.**

### D6 — Exports PDF/CSV/XLSX avec consentement médical réel
**Importance : P1 / GATE CLINIQUE.** *Ancien D4 ; CAL-12.*

**GOAL :** exports exacts et accessibles FR/AR ; consentement distinct du consentement IA, destinataire professionnel confirmé, identité et droit d'export revalidés au moment du partage, politique de conservation/purge et A→B→A.

**SUCCESS :** vrais flux Flutter Web/DRIFT/API refusent données d'autrui, droits périmés et destinataires non confirmés ; aucune copie patient réelle sans sign-offs.

**PROOF :** FUE Flutter Web authentifiée, écran Reports, tests Chrome/Safari, assistive AR et validations R1 médical/R3 privacy/R4 accessibilité AR/R6 produit. [#1332](https://github.com/hraaaaf/IAMINA-MVP/pull/1332), [#1333](https://github.com/hraaaaf/IAMINA-MVP/pull/1333), [#1335](https://github.com/hraaaaf/IAMINA-MVP/pull/1335), [#1336](https://github.com/hraaaaf/IAMINA-MVP/pull/1336) Draft : les FUE HTML fictives **ne valent pas** livraison clinique. **REAL PATIENT EXPORT NO-GO.** Dépend de D1 et D5.

### D7 — Une page Paramètres cohérente
**Importance : P1.** *Anciens D36, D38, D23, inventaire D25 et partie D26.*

**GOAL :** remplacer Profil par Paramètres, regrouper profil/compte, unités, données, IA/consentements, notifications, sécurité, suppression et inventaire CGM sans prétendre que les appareils sont déjà connectés. Section « Paramètres de l'application » **fermée par défaut**.

**SUCCESS :** une seule entrée de navigation, contrôles réellement opérationnels ou clairement indisponibles, aucune préférence A affichée chez B.

**PROOF :** BEFORE → cible → AFTER mêmes viewports 390/430/768/1280 FR/AR RTL, clavier, zoom 200 %, tests a11y. D1/D3 bloquent les réglages sensibles non vérifiés.

### D8 — Notifications consenties, tendances de poids et feedback
**Importance : P2.** *Anciens D2, résidus D20 et D29.*

**GOAL :** rappels volontaires et révocables, cadence maîtrisée, historique/aperçu et purge J+7 seulement après sécurité du scheduler ; tendance poids descriptive, feedback libre non intrusif.

**SUCCESS :** aucun envoi ni profilage sans accord ; aucun scheduler annoncé actif sans preuve ; suppression et surveillance vérifiées.

**PROOF :** tests Web/API hébergés A/B, scheduler authentifié, alerte, PITR/backup, revue privacy ; [#1153](https://github.com/hraaaaf/IAMINA-MVP/pull/1153) Draft **trop large à ne pas fusionner en bloc**. Dépend D1/D3 et D5 pour tout message clinique. Les rappels Accueil déjà livrés ne sont pas à refaire.

### D9 — Photo alimentaire et saisie multimodale
**Importance : P2.** *Anciens D34, D14, D15.*

**GOAL :** benchmark d'un modèle vision/VLM léger adapté aux repas marocains/MENA ; propositions incertaines d'aliments et portions, correction et confirmation humaines, ajout d'aliment inconnu, favoris ; un seul brouillon photo/texte/voix.

**SUCCESS :** aucune sauvegarde sans confirmation explicite, aucun envoi sans accord D3, saisie manuelle toujours disponible, aucun dosage conseillé.

**PROOF :** benchmark qualité/latence/coûts sur photos fictives, détections erronées, Web FR/AR, egress et rétention ; [#1245](https://github.com/hraaaaf/IAMINA-MVP/pull/1245), [#1257](https://github.com/hraaaaf/IAMINA-MVP/pull/1257) Draft. **Ancien D14 PAUSED : sa réactivation nécessite un arbitrage distinct**. Dépend D3/D4.

### D10 — Habitudes et personnalisation opt-in
**Importance : P2.** *Anciens D35 et résidu D28 non clinique.*

**GOAL :** proposer favoris et tendances descriptives d'horaires de repas/mesures, sommeil uniquement déclaré ou source autorisée ; apprentissage désactivé par défaut, transparent, corrigible et effaçable.

**SUCCESS :** aucun apprentissage invité ou non consenti ; révocation coupe collecte et sorties ; A/B cloisonnés, pas d'inférence thérapeutique.

**PROOF :** tests de provenance et d'effacement, consentement, rétention et offline/sync. Dépend D1/D3, revue privacy.

### D11 — Connexion CGM officielle : DERNIÈRE FONCTIONNALITÉ
**Importance : P3 / APRÈS LES AUTRES FONCTIONS.** *Anciens D1 et D25 connexion.*

**GOAL :** intégrer **une source fabricant/API légalement et techniquement autorisée à la fois**, Nightscout facultatif, lecture seule et révocation garantie.

**SUCCESS :** provenance, fraîcheur, trous de données, métriques et erreurs correctement signalés ; aucune valeur artificielle ni promesse de compatibilité non vérifiée.

**PROOF :** droit API/pays, contrat fabricant, tests dispositifs/autorisations, métriques D5 et privacy. Aucun connecteur supposé actif.

### D12 — Certification Web/PWA et lancement maîtrisé
**Importance : GATE FINAL.** *Ancien W14.*

**GOAL :** certifications produit/UX/sécurité/clinique/privacy/réglementaires, restauration, accessibilité, CI exact SHA et pilote contrôlé après clôture des lots requis.

**SUCCESS :** aucun blocker ouvert, revues indépendantes adaptées, merge/postmerge documentés ; séparation explicite code merged ≠ site déployé.

**PROOF :** audits, tests Chrome/Safari + iPhone web et desktop, 390/430/768/1280 FR/AR RTL/zoom, tests A→B→A et backups, CI sur HEAD exact, dossier GO/NO-GO. **Chaque déploiement Vercel Preview ou Production demande une autorisation explicite distincte.**

## HORS ROADMAP — NE PAS REPROGRAMMER

**Déjà fusionnés et acceptés sur leur périmètre :** anciens D3 (rappels Accueil [#1230](https://github.com/hraaaaf/IAMINA-MVP/pull/1230)), D5 (choix pays [#1205](https://github.com/hraaaaf/IAMINA-MVP/pull/1205)), D8 (unité choisie manuellement [#1269](https://github.com/hraaaaf/IAMINA-MVP/pull/1269)), D22 (affichage/unité techniquement clos [#1249](https://github.com/hraaaaf/IAMINA-MVP/pull/1249)), D30 (ancien mode local sur son périmètre [#1169](https://github.com/hraaaaf/IAMINA-MVP/pull/1169)), W03 (bouton compagnon [#1302](https://github.com/hraaaaf/IAMINA-MVP/pull/1302)). Selon l'audit Notion du 04/11, anciens D6, D11, D17, D21, D27 également livrés bornés ; ancien D16 copie sélective seulement. Ne les rouvrir qu'en présence d'une régression prouvée. Les tests D7 [#1334](https://github.com/hraaaaf/IAMINA-MVP/pull/1334) sont fusionnés mais la certification hébergée D7 reste ouverte sous la nouvelle D1.

**Contradictions tranchées :** unité auto-proposée selon IP remplacée par choix manuel ; consentement IA global remplacé par trois autorisations indépendantes ; connexion « après 5 minutes » abandonnée pour login au besoin ; ancien mode local D30 ne permet pas au nouvel invité d'ouvrir un coffre santé ; D14 PAUSED n'est pas levé par la décision photo ; D22 technique n'autorise pas la politique clinique ; tests PDF synthétiques CAL-12 ne sont pas un export patient.

**Différé hors Web :** anciens tests natifs physiques D31 ; doctrine Web-first D33 n'est pas une décision de développement. **Archives consultables, jamais une deuxième roadmap :** [Notion D1–D30](https://app.notion.com/p/40777c6633628177b325d3cb5412fc18), [ancienne roadmap GitHub](archive/roadmap-pre-single-active-2026-11-10.md), [anciens choix D1–D38](https://github.com/hraaaaf/IAMINA-MVP/pull/1270).

## NEXT EXACT — D1

**Audit en lecture seule d'abord** : cartographier Web routeur → AuthService → coffre Drift/IndexedDB/VFS → API Django → sessions/révocation avec vrai parcours A→B→A fictif et vieux client offline ; relever preuves d'isolation, risques de récupération et absence de migration silencieuse. Puis choisir le plus petit correctif sûr, tests ciblés, revue, et mise à jour de ce fichier. **Ne pas toucher à Neon patient, ne pas fusionner, ne pas déployer sans gates.**

**Canonicité :** `docs/ROADMAP.md` sur la branche de consolidation, puis `main` après CI, revue et fusion autorisée. Notion « 01 — ROADMAP CANONIQUE » est le miroir du même document, **pas une seconde feuille de route**.
