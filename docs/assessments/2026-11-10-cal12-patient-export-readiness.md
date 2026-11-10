# IAMINA — CAL-12 — Dossier d'acceptation des exports médicaux (10 novembre 2026)

**Verdict actuel : `TECHNICAL_SYNTHETIC_PROOF / PATIENT_EXPORT_NO_GO`.** CAL-12 n'est ni signée, ni cliniquement autorisée, ni activée. Ce dossier est un contrôle de sécurité pré-déploiement, pas un certificat médical. Données patient réelles : **aucune** utilisée pour cette preuve.

**Décision propriétaire 10/11/2026 :** FUE et tests exact-HEAD suffisent comme contrôle **technique** ; pas de deuxième auditeur de code indépendant (ancien R5) à solliciter. Ils ne remplacent pas la décision médicale, les engagements de confidentialité, la linguistique arabe et l'autorisation produit. Aucun merge ou Vercel sans permission explicite.

## Référence avant contrôle

- D4 [PR #954](https://github.com/hraaaaf/IAMINA-MVP/pull/954), baseline `bb17e199de328b58550ce4392cb244ebcd4f452b` : [D4 6 PDF #42727554298](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42727554298), [CI #42727554310](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42727554310), [D2 SQLite/PostgreSQL FUE #42727554453](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42727554453), [P5-5 #42727554510](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42727554510) : **4/4 SUCCESS** sur l'ancien HEAD. Nouvelle preuve CAL-12 nécessite nouveau run exact-HEAD.
- `frontend/lib/features/journal/reports_screen.dart` et `reports_screen_presentation.dart` : affichage local de statistiques issues du coffre ; **aucun bouton ni appel D4 CSV/JSON/PDF/Share identifié dans ces deux fichiers**. Une vérification statique fail-closed est ajoutée au workflow D4 pour signaler une future connexion directe de ces primitives à cette UI.
- `frontend/lib/services/local_report_pdf.dart` : ancienne primitive PDF, texte ASCII uniquement, refus de l'arabe. Ne pas la détourner pour le rapport médical.
- `frontend/lib/services/synthetic_doctor_report.dart` et `synthetic_report_formatter.dart` : **modèles synthétiques** ; mesures manuelles de démonstration, maximum 12, provenance/UTC, null distinct de zéro, CSV contre injection de formules. La chaîne `synthetic_only` n'est **pas une garantie de non-PII** si un futur appelant fournit de vraies données.
- `frontend/lib/services/consent_service.dart`, `consent_notice_contract.dart` et `consent_evidence_store.dart` : consentement de **traitement IA externe**, avec version/hachage par langue et révocation ; **ne constitue pas un consentement spécifique à l'export PDF/CSV vers un destinataire**.
- `docs/operations/PATIENT_DATA_EXPORT.md` : export JSON administratif authentifié indépendant, avec procédure 0600/empreinte/audit ; **ne prouve pas** la sécurité du futur bouton Reports ni son consentement.

## Matrice CAL-12 — constat vérifié, jamais supposé

| Condition de mise en service | Statut | Preuve / limite |
| --- | --- | --- |
| Aucun export Reports patient actif | **PASS — périmètre inspecté** | UI `reports_screen*.dart` sans D4/Share ; garde CI fail-closed ajoutée ; ne vaut pas inventaire de toutes les routes/appareils |
| Formateur synthétique : dates UTC, manuel/source, unités, absence explicite, bornes, Unicode CSV/JSON, injection | **PASS synthétique** | Tests de contrat D4 ; 3 et 12 relevés |
| PDF visuel FR/EN/AR en A4 et warnings de non-usage clinique | **PASS visuel synthétique** | 6 PDF 1 page, PNG Poppler, polices embarquées et `/Lang` `fr/en/ar` ; aucune qualification clinique |
| Gabarits HTML sans scripts, CDN ni appels externes | **PASS synthétique**, CI renforcée | Contrôle des 6 HTML, 6 warnings/langues/directions, source locale des polices |
| PDF arabe : extraction/copier-coller fidèle sur les phrases critiques synthétiques | **PASS technique sur fixtures** | Correctif CI WeasyPrint 68 + Noto Naskh : les 2/2 PDF arabes en 3/12 lignes extraient `تقرير متابعة`, avertissement entier, date et phrases finales ; `تقرير مت ابعة` absent, PDF balisé, polices Unicode CID. **Ce test ne certifie pas PDF/UA, VoiceOver ou une traduction native.** |
| PDF/UA / lecteurs d'écran / zoom élevé et restitution tabulaire bidirectionnelle | **NOT PROVEN** | Pas de qualification assistive/AT ni revue native arabe ; un PDF accessible ne se déduit pas d'un PNG |
| Identité A→B→A, coffre courant, déconnexion/révocation, absence de fuite du document | **NOT RUN D4** | FUE D2 sur sessions/rétention synthétiques ≠ parcours de partage Reports ; bouton patient OFF |
| Consentement d'export distinct, versionné, finalité et révocation au moment du partage | **NOT IMPLEMENTED D4** | Consentement IA `ConsentService` non substituable |
| Destinataire explicite, canal choisi, fichier temporaire/cache, rétention/purge, journal sans contenu médical | **NOT IMPLEMENTED D4** | Aucun partage, sauvegarde ni envoi D4 autorisé |
| Champs patients typés (glycémie manuelle vs CGM vs estimation), unité source, provenance fiable | **NOT APPROVED** | Projet D32 #1248 sur unités/KPI/CGM ; ne pas export d'objectifs, TIR, AGP, GMI, diagnostic ou conseil non qualifiés |
| Approbation médical R1, confidentialité R3, linguistique R4, périmètre/risques R6 | **NOT SIGNED** | [Issue de gouvernance #946](https://github.com/hraaaaf/IAMINA-MVP/issues/946) ; aucune identité ou signature inventée ; deuxième QA technique indépendant R5 non requis par décision propriétaire |

## Contrat minimal à implémenter **avant** un export réel (non codé, non autorisé)

1. **Entrée typée** : identité de coffre local active, propriétaire des mesures exactement égal à l'utilisateur authentifié ; mesures horodatées et provenance réelles fiables, unités source et conversion approuvées ; données non qualifiées exclues (dont KPI CGM/targets D32).
2. **Consentement distinct** : finalité « rapport médical destiné à un médecin », catégorie et période des données, prévisualisation, choix explicite du destinataire/canal, version du texte FR/EN/AR, horodatage et preuve de consentement, révocation contrôlée au moment de générer et juste avant tout partage. Une case « IA » préexistante ne donne pas cette autorisation.
3. **Livraison sous contrôle** : déclenchement par geste explicite ; pas d'upload, impression, téléchargement ou email automatique ; nom de fichier sans identifiant sensible, chemin/temporaire contrôlé, durée de rétention configurable et prouvée, nettoyage aussi à l'échec, aucune donnée de santé dans logs/traces.
4. **Document médical descriptif** : mention des absences, sources et unités par ligne ; pas d'objectifs personnalisés, prescription, dose ou interprétation non validés ; en-tête/date/numérique LTR stables dans RTL ; phrase explicite du caractère descriptif, mais **pas** de bandeau « synthétique » sur un vrai document.
5. **FUE produit à réaliser** : dossiers fictifs A/B distincts ; connexion A → export prévisualisé → refus/révocation → changement B → absence de données A → retour A ; frais de cache, mode offline, fermeture/session expirée, nom/permissions fichier, partage annulé, destinataire différent, CSV injection, FR/EN/AR, zoom 200%, clavier, sélection/copie, lecture écran et PDF 1/2/plusieurs pages. Preuves exactes SHA/app/UI, sans patient réel.

## Résolution / prochaine décision

**Autorisé maintenant :** développement et tests synthétiques isolés, examen de la génération PDF, validation via CI/FUE. **Non autorisé :** brancher `ReportsScreen` à une vraie exportation, activer les boutons de partage/impression, appeler le PDF « accessible/clinique », lever CAL-12 en l'absence de validations métier. Pour progresser : fidélité arabe synthétique corrigée et contrat de refus de prévisualisation fictive testé ; **restent** l'implémentation du consentement/export patient réel, sa destination et sa purge, le FUE navigable A/B sur un environnement explicitement autorisé, la validation assistive/AR native et les arbitrages R1/R3/R4/R6 ; puis **une décision explicite de merge** et une décision **distincte** de déploiement Vercel. Le signataire technique indépendant R5 n'est plus requis.

**État mis à jour : `CAL12_SYNTHETIC_TECH_PASS / REAL_PATIENT_OFF / NO_MERGE / NO_DEPLOY`.** Les tests synthétiques ciblés ont passé ; la qualification produit, médicale et de confidentialité reste ouverte.


## 10/11/2026 — Simulation in-memory CAL-12 : consentement/destinataire A→B→A

Nouveau module pure Dart `SyntheticDoctorExportGate` : seule une **prévisualisation HTML des 12 relevés fictifs au maximum** est autorisée, sans API patient, disque, partage, mail, presse-papiers, téléchargement ni réseau. Les propriétaires `alpha/beta`, destinataires `doctorOne/doctorTwo`, raison `doctorFollowUp` sont des **enums d'essai**, pas des identités patient/médecin, ni une preuve de signature ; `patientExportEnabled=false` est constant. Rejeter avant rendu identité courante ≠ propriétaire du rapport/consentement, mauvais destinataire ou absence de confirmation explicite, date UTC absente, consentement non effectif/expiré/révoqué, date du rapport future. Tous les contrôles sont exécutés de nouveau sur chaque appel (mais pas sur un acte de partage réel, puisqu'il n'existe pas). Tests : FR/EN/AR + A→B→A synthétique + cas négatifs. Le workflow interdit tout branchement direct de ce module sur ReportsScreen. **Cela ne clôture ni CAL-12 métier, ni le vrai FUE navigable authentifié.**


## 10/11/2026 — AFTER : preuves GitHub exact-HEAD et état fiable

**Commit technique vérifié** [`7deda2f9f221ef6549d1b02d85389d67961e7264`](https://github.com/hraaaaf/IAMINA-MVP/commit/7deda2f9f221ef6549d1b02d85389d67961e7264) : [D4 PDF/contrats #42782599955](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42782599955), [CI générale #42782599910](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42782599910), [D2 backend SQLite/PostgreSQL et Flutter #42782599909](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42782599909), [P5-5 #42782599924](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/42782599924) tous `completed/success`. Artefact D4 ID `13746836525` digest `sha256:66049e0a01333faaa62f30828bd340e68d86515558f5d133756d83851e9fd206`, ZIP retéléchargé et vérifié indépendamment : 6/6 PDF A4 1 page, 6 HTML, 6 PNG, 6 TXT, deux PDF arabes sans corruption des principaux mots, sans pièces jointes PDF. Le rendu arabe à 12 lignes est lisible. Les tests d'isolement A→B→A et du consentement/destinataire fictifs passent au même SHA.

**Limite obligatoire :** `patientExportEnabled=false` demeure. Aucun consentement de partage médical authentifié/stocké/révocable, aucune prévisualisation utilisateur intégrée, aucun PDF patient généré ni partage réseau/e-mail, aucun FUE Web produit complet, aucune validation médecin/DPO/native AR ou PDF lecteur écran. Le code synthétique est une **preuve de conception fail-closed**, pas l'autorisation CAL-12 d'utiliser des données réelles.


## 10 novembre 2026 — FUE Web CAL-12 isolée : préparation à l'exécution

Goal : un parcours Flutter Web qui permet, sur deux profils inventés, de prévisualiser une mesure fictive, de consentir explicitement à une simulation, de sélectionner/confirmer un médecin fictif, puis de simuler un partage sans aucune émission. Un changement de profil efface immédiatement le consentement et le résultat en mémoire. La valeur A est 142 mg/dL, la valeur B est 119 mg/dL, afin de rendre visible une fuite A vers B. Une révocation remet le parcours au départ.

Sources techniques :
- frontend/lib/features/journal/synthetic_doctor_export_web_flow.dart : widget Flutter isolé, jamais importé par l'application normale.
- frontend/lib/cal12_synthetic_web_main.dart : point d'entrée spécifique au navigateur local.
- frontend/test/cal12_synthetic_web_flow_test.dart : tests de widgets sur FR/AR, 390×844, 768×1024, 1280×900, y compris les refus sans consentement ou destinataire confirmé, A→B→A et révocation.
- tools/cal12_synthetic_web_fue.js et .github/workflows/cal12-synthetic-web-fue.yml : build Flutter Web distinct, Chromium Playwright local 127.0.0.1, requêtes externes/POST bloquées, aucun popup ni téléchargement, captures AVANT/APRÈS identiques par viewport et preuve JSON avec SHA-256.

BEFORE : seul le service d'autorisation pure Dart fictif était présent ; aucun écran Web de consentement/export fictif navigable n'existait dans D4. AFTER attendu : six parcours FR/AR × mobile/tablette/desktop, captures avant aperçu, après simulation, bascule B et retour A. La comparaison visuelle se fait aux mêmes viewports, avec vérification automatique des dimensions PNG, absence de débordement horizontal et absence d'erreur navigateur. Le score visuel doit être établi sur des captures réellement inspectées, jamais inventé.

Ce FUE est exécuté seulement dans Chromium local de GitHub Actions ; il ne prouve PAS le login patient, un coffre réel A/B, le consentement juridique, le destinataire réel, la rétention/purge du fichier, les lecteurs d'écran ni une intégration de ReportsScreen. Il n'active pas le partage, l'export médical, un endpoint, une route publique, une Preview ou une Production Vercel. CAL-12 patient réel demeure NO_GO. Le second reviewer technique indépendant n'est pas exigé par décision propriétaire ; les validations médicales, DPO, linguistiques et de release sont distinctes.
