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
| PDF arabe : copie/sélection/extraction du texte sans morcellement | **FAIL / BLOCKER** | `pdftotext` et PyMuPDF : `تقرير متابعة` peut être extrait `تقرير مت ابعة` ; phrases arabes morcelées. PDF tagué et `/Lang(ar)` ne suffisent pas pour valider l'accessibilité ou les lecteurs d'écran |
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

**Autorisé maintenant :** développement et tests synthétiques isolés, examen de la génération PDF, validation via CI/FUE. **Non autorisé :** brancher `ReportsScreen` à une vraie exportation, activer les boutons de partage/impression, appeler le PDF « accessible/clinique », lever CAL-12 en l'absence de validations métier. Pour progresser : corriger d'abord la fidélité de copie du texte arabe, implémenter le contrat de consentement et le parcours export fictif, effectuer le FUE A/B sur la même build ; ensuite arbitrages R1/R3/R4/R6, puis **une décision explicite de merge** et une décision **distincte** de déploiement Vercel. Le signataire technique indépendant R5 n'est plus requis.

**Maintien de l'état : `CAL12_TECH_PREFLIGHT_IN_PROGRESS / REAL_PATIENT_OFF / NO_MERGE / NO_DEPLOY`.** Ce dossier sera complété par la conclusion du run GitHub exact-HEAD de la présente PR.


## 10/11/2026 — Simulation in-memory CAL-12 : consentement/destinataire A→B→A

Nouveau module pure Dart `SyntheticDoctorExportGate` : seule une **prévisualisation HTML des 12 relevés fictifs au maximum** est autorisée, sans API patient, disque, partage, mail, presse-papiers, téléchargement ni réseau. Les propriétaires `alpha/beta`, destinataires `doctorOne/doctorTwo`, raison `doctorFollowUp` sont des **enums d'essai**, pas des identités patient/médecin, ni une preuve de signature ; `patientExportEnabled=false` est constant. Rejeter avant rendu identité courante ≠ propriétaire du rapport/consentement, mauvais destinataire ou absence de confirmation explicite, date UTC absente, consentement non effectif/expiré/révoqué, date du rapport future. Tous les contrôles sont exécutés de nouveau sur chaque appel (mais pas sur un acte de partage réel, puisqu'il n'existe pas). Tests : FR/EN/AR + A→B→A synthétique + cas négatifs. Le workflow interdit tout branchement direct de ce module sur ReportsScreen. **Cela ne clôture ni CAL-12 métier, ni le vrai FUE navigable authentifié.**
