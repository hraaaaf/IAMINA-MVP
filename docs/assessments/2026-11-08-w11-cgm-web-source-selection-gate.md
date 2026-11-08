# IAMINA Web V2 — W11-00 — Contrat de choix de source CGM (candidat, non activé)

**Date de recherche :** 2026-11-08  
**Statut :** DESIGN CANDIDATE / NOT IMPLEMENTED / NOT CERTIFIED  
**Base :** `main@0a096ac195d79b494e8f2722be95c3b54396cd2d`  
**Décision ciblée :** premier écran du futur parcours W11 (D1/D25), **choisir une voie d'accès aux données CGM** en Web/PWA. **Ce fichier ne change aucun contrat runtime**.

## 1. Objectif, différence avec l'existant et limites

**GOAL :** une personne doit pouvoir identifier *une voie potentiellement compatible* sans croire qu'IAMINA sait lire son capteur ni que ses données sont déjà synchronisées. La voie n'est activable que si les preuves juridiques, techniques, de sécurité et d'isolement patient sont établies, notamment pour le Maroc.

**AVANT, vérifié dans le dépôt :** `docs/assessments/2026-09-11-cgm-guided-onboarding-v3.md` décrit un parcours certifié **via Nightscout** (Dexcom, Libre, LinX/AiDEX X), avec route `/cgm` et configuration Nightscout. Ce socle historique n'est pas supprimé.

**CIBLE W11 (roadmap) :** Nightscout devient **facultatif** dans l'expérience future. Le choix initial offre trois familles de voies, sans simuler leur disponibilité :
1. **Connexion officiellement autorisée** : cloud/API fournisseur ou partenaire après examen d'une permission contractuelle, du territoire, de l'OAuth, du traitement des données et de la disponibilité réelle.
2. **Importer un export** : uniquement lorsque le format, la provenance, les unités et l'import patient-scoped sont démontrés par des fixtures synthétiques ; un PDF AGP n'est pas une liste complète de lectures CGM.
3. **Mode avancé Nightscout** : conserver le chemin historiquement documenté, mais n'en faire ni un passage obligatoire ni une connexion fabricant directe.

Les options ne donnent **pas** accès au capteur par simple utilisation d'un navigateur Web. Aucune lecture BLE/PWA universelle, API fabricant universelle, synchronisation temps réel, alerte médicale, décision de traitement ou capacité iOS/Android égale n'est présumée.

**Hors scope de W11-00 :** écrans Flutter, adaptateurs, OAuth, bases, migrations, persistance, CGM réel, capture, import réseau, réécriture du connecteur Nightscout, Vercel, activation clinique, merge de ce contrat. Ce lot est de **cadrage**, pas un D1/D25 certifié.

## 2. Sources par fabricant — ne jamais transformer « existe » en « accessible à IAMINA »

| Source envisagée | Fait documenté | Preuve manquante avant affichage « Connecter » | Verdict W11-00 |
|---|---|---|---|
| Dexcom G6/G7 et gammes admissibles | Programme développeurs officiel ; REST/OAuth 2.0 ; accès sur candidature/partenariat | Accès IAMINA accepté, produits/région Maroc, scopes, modalités de conservation, délais vérifiés et autorisation de transfert | **HOLD** : montrer « Accès en cours de qualification » |
| Abbott FreeStyle Libre | LibreView permet la consultation/partage des historiques ; mécanismes de partage officiels existent | **API tiers contractualisée pour IAMINA**, autorisation Abbott, produits et territoire Maroc, format et cadence ; ne pas traiter LibreLinkUp privé comme API publique | **HOLD** |
| MicroTech LinX / AiDEX | Portail officiel AiDEX API visible ; le dépôt décrit un chemin tiers Juggluco → Nightscout pour LinX/AiDEX X | Accord écrit MicroTech, support explicite du **produit LinX** via API, accès international/Maroc, documentation des scopes, coût et cadence, tests d'appareil réels | **HOLD** pour API directe |
| Nightscout | Documentation publique de l'écosystème et des uploaders ; IAMINA dispose historiquement d'un lecteur Nightscout | Autorisation d'accès à l'instance choisie, liste de domaines, preuve de connexion/lecture isolée, sécurité des identifiants, E2E Web sur cible autorisée | **VOIE AVANCÉE CANDIDATE**, non nouvelle activation |
| Export local (CSV ou équivalent) | La roadmap W11 l'envisage comme alternative | Source et schéma de fichier réellement émis, colonnes/horodatage/fuseau, unités, identité patient, validation antivirus/fichier et absence d'egress | **VOIE CANDIDATE**, pas de parseur approuvé |

**Règle d'affichage :** aucune marque ne reçoit un bouton **« Connecter maintenant »** tant qu'un registre `source × produit × région × voie × autorisation × test E2E` ne marque chaque exigence **PASS**. « En étude », « Non disponible dans votre pays » et « Inconnu » sont trois états distincts ; n'affirmer un pays non disponible qu'avec une preuve.

**Différence importante :** disposer d'un portail fournisseur, d'une application de suivi ou d'un pont communautaire ne constitue ni un droit d'accès ni une API exploitable légalement dans IAMINA.

## 3. Parcours Web projeté (spécification, non implémentation)

**Écran A — Choisir la source :** « Quel capteur utilisez-vous ? » → Dexcom / FreeStyle Libre / LinX-AiDEX / Autre / Je ne sais pas. Une option **Importer un fichier** reste visible. Référence au capteur ≠ preuve de source de données.

**Écran B — Choisir la voie :** ne montrer que les voies supportées pour ce produit et cette région selon une matrice de preuves. Voie non qualifiée : explication courte et action neutre (« Comprendre les options »), jamais un faux formulaire d'identifiants.

**Écran C — Comprendre les données :** expliquer la différence entre mesure du capteur, lecture historique synchronisée, mise à jour différée et éventuels trous. Une PWA de lecture n'est pas une source fiable d'alertes de sécurité. Signaler chaque service externe et son pays/rétention dès qu'ils sont connus.

**Écran D — Consentement (futur, gate) :** choix explicite et révocable *par finalité et fournisseur* ; refus ne bloque pas la consultation des fonctions indépendantes. Auth fabricant exclusivement via mécanisme officiel approuvé ; **jamais** de mot de passe LibreLinkUp/Dexcom/MicroTech dans le formulaire IAMINA.

**Écran E — Activer/importer (désactivé ici) :** ne présenter une action réelle qu'après W01/W02/W04, sécurité/privacy, CNDP et API/format prouvés. Données synthétiques pendant les tests. Gestion claire de l'expiration, des erreurs d'accès et de l'absence de mesures.

**Écran F — Vérifier et révoquer :** afficher provenance précise (fournisseur et voie), unité, horodatage de la mesure, horodatage de la dernière synchro, état « à jour / retardé / incomplet / aucune lecture / déconnecté ». Révocation côté IAMINA ET procédure fournisseur si nécessaire ; ne jamais prétendre que la suppression locale révoque automatiquement un jeton distant sans preuve.

**Accessibilité future :** FR + AR/RTL, 390×844 / 768×1024 / 1280×900 ; clavier, focus visible, étiquettes lisibles, états erreurs, retour arrière, reprise après perte réseau. Aucun FUE n'a été exécuté pour ces écrans inexistants.

## 4. Contrat de provenance et sûreté avant tout prototype connecté

- **Autorité clinique :** données CGM importées = observations datées, non prescription, décision sur dose, diagnostic, triage urgent ou notification de sécurité. Conserver le lecteur primaire du fabricant.
- **Séparation :** mesures manuelles, import, CGM continu et estimations ne sont pas interchangeables. Aucune conversion « nombre absent → 0 » ni séries/AGP/TIR/GMI inventés en présence de trous.
- **Champs requis en étude :** `patient_owner` (serveur), `manufacturer`, `product`, `connector_kind`, `source_identifier`, `measured_at_utc`, `reported_timezone` (si connu), `received_at_utc`, `raw_value`, `raw_unit`, `normalized_value` (si qualifié), `sample_id` (si fourni), `status`, `provenance_evidence`. Ces noms sont **conceptuels**, pas un schéma autorisé.
- **Validation technique à exiger :** normalisation unités par oracles indépendants, fuseaux/DST, répétitions et collisions de timestamps, identifiants instables, données hors ordre, délais, pagination, trous, doublons, export importé deux fois, révocation pendant synchro, reprise après erreur, A→B→A, droits d'accès, pertes réseau et absence de fuite dans logs/telemetry.
- **Sécurité :** permission du propriétaire et consentement serveur avant egress ; scopes minimaux, secrets uniquement côté serveur autorisé et chiffrés, zéro mot de passe fabricant collecté par IAMINA, pas d'API privée rétro-ingénierée activée, aucune IP privée/URL arbitraire via pont Nightscout ; aucun appairage BLE non validé.
- **Réglementation :** la disponibilité, les droits d'utilisation, l'hébergement hors Maroc, la Loi 09-08/CNDP, la conservation et la finalité doivent être vérifiés spécifiquement avant usage réel.

## 5. Registre de sortie vers lot d'intégration (tout doit être PASS)

| Gate | Critère observable | Actuellement |
|---|---|---|
| G1 — Contrat | Autorisation écrite fournisseur/partenaire pour produit et Maroc **ou** format de fichier autorisé avec provenance | **NOT_PROVEN** |
| G2 — Technique | API/documentation de version, OAuth/scopes ou fixture de fichier, test de cadence et erreurs | **NOT_PROVEN** |
| G3 — Privacy | Consentement/révocation, résidences, rétention, prestataires et traitement CNDP revus | **NOT_PROVEN** |
| G4 — Intégrité | Tests sur unités, dates, doublons, provenance, séparation patient et données manquantes | **NOT_RUN** |
| G5 — Web réel | Parcours FR/AR RTL/keyboard responsive, FUE 100 % cas applicables sur vrai navigateur | **NOT_RUN** |
| G6 — Autorité clinique | Revue absence d'alertes/doses/diagnostics automatisés et de promesse temps réel | **NOT_RUN** |
| G7 — Déploiement | Autorisation Vercel **distincte** et décision d'activation humaine après W01/W02/W04 | **NOT_AUTHORIZED** |

**Définition de succès W11-00 :** ce registre est versionné, auditable et **n'active rien**. Aucun gate n'est réputé PASS par la seule existence de ce document.

## 6. FUE prévu (pas exécuté)

Couverture requise lors d'un futur changement d'interface : source connue/« Je ne sais pas », région non qualifiée, sans fournisseur, import absent/malformé, refus du consentement, erreur OAuth, données incomplètes/retardées, révocation, retour/reprise, FR+AR/RTL et trois viewports. Pour chaque cas : `entrée → action → attendu → observé → capture/run exact HEAD → PASS/FAIL/NOT_RUN`. **W11-00 = 100 % NOT_RUN**, car aucune UI ou intégration n'est livrée.

## 7. Références et fiabilité (consultation du 08/11/2026)

**Sources primaires externes :**
- [Dexcom Developer Program — Overview](https://ui-g7int-us.platform.dexcomdev.com/docs/) : API REST/OAuth, partenariat et révocation d'accès ; la disponibilité IAMINA/Maroc n'y est **pas prouvée**.
- [MicroTech AiDEX API Open Platform](https://aidexapi.microtechmd.com/) : portail officiel ; le portail seul **ne prouve** ni LinX/Maroc ni les droits d'IAMINA.
- [Abbott — Sharing FreeStyle Libre Data with Healthcare Providers](https://www.freestyle.abbott/en-ca/support/can-i-share-my-freestyle-libre-data-with-my-healthcare-profess.html) : partage LibreView ; pas une autorisation d'intégration tierce.
- [Nightscout — Supported Uploaders](https://nightscout.github.io/uploader/uploaders/) et [Nightscout — projet communautaire](https://nightscout.github.io/) : capacités d'écosystème à tester, projet non approuvé pour traitement.
  
**Sources IAMINA internes :** `docs/ROADMAP.md` W11 D1/D25, `docs/assessments/2026-09-11-cgm-guided-onboarding-v3.md`, `docs/assessments/2026-08-16-cgm-gateway-v1-1-linx-qualification.md`, PR [#1129](https://github.com/hraaaaf/IAMINA-MVP/pull/1129) (REA research en Draft, non fusionnée). [Notion — benchmark CGM W11](https://app.notion.com/p/3fb77c6633628170a817fd130fbd9bdc) contient des hypothèses et certaines recherches historiques ; elles restent **non autorisations**.

## 8. Next exact après W11-00

Sélectionner **une** voie/fournisseur avec le meilleur ensemble de preuves écrites pour le Maroc (sans choisir par simple notoriété). Dans un nouveau lot, obtenir la preuve d'accès ou d'export, définir des fixtures synthétiques et auditer l'architecture existante **avant** toute maquette connectée. Toute mise en service, toute donnée réelle et tout Vercel restent bloqués par des décisions distinctes.
