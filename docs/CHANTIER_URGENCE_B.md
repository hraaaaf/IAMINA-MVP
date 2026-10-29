# IAMINA — CHANTIER D’URGENCE B — Reprise canonique Web/PWA

**Autorité d'exécution :** [Notion — Chantier d'urgence B, décisions dépendantes](https://app.notion.com/p/40777c66336281729c03c9bb294e71b7) ; [Chantier A, décisions autonomes](https://app.notion.com/p/40777c6633628173b672cd02104a0003) est exécuté séparément. [Tri D1–D30](https://app.notion.com/p/40777c6633628177b325d3cb5412fc18) est un registre de distribution. **Décision explicite du propriétaire le 29/10/2026 : A et B, et non `docs/ROADMAP.md` / W00–W14, dictent désormais l'ordre.** Conserver l'ancien fichier comme historique technique ; il ne justifie aucun changement de priorité dans B. Ce Markdown est un **miroir/handover B**, non une troisième roadmap.

**Dépôt :** `hraaaaf/IAMINA-MVP`. **Base de l'audit D8 :** `main@9ba0f737e184e1c65ca83a4db14b3b22f220c0ae` (29/10/2026). **Cible exclusive :** Flutter Web/PWA. **Aucun déploiement Vercel** sans autorisation explicite.

## Périmètre / ordre strict B (17 décisions)

1. **D7** — Type de diabète et traitements modifiables
2. **D22** — Unité avant objectifs glycémiques
3. **D8** — Unité suggérée selon pays mais modifiable
4. **D10** — Récupération et verrouillage facultatif
5. **D9** — Retour patient existant sans onboarding imposé
6. **D24** — Désactivation IA effective côté API
7. **D26** — Confidentialité, déconnexion, suppression
8. **D28** — Intelligence déterministe gouvernée
9. **D2** — Notifications intelligentes consenties
10. **D4** — Rapports PDF/CSV/XLSX
11. **D14** — Photo repas : suggestion IA incertaine et validation patient
12. **D15** — Brouillon repas multimodal unique
13. **D20** — Tendances pondérales et alertes descriptives optionnelles
14. **D23** — Paramètres Application et IAmina centralisés
15. **D29** — Retour de première utilisation facultatif
16. **D1** — CGM sans Nightscout obligatoire
17. **D25** — Données/appareils : connexion et révocation

**Ne jamais emprunter D16/W03 ni les autres décisions du chantier A.** Le travail sur A (D30, D19, D5, D16…) est hors de notre propriété d'exécution ; son code/CI peut être consulté uniquement pour vérifier les dépendances de B. Un seul lot produit actif par chantier ; audit/preflight d'une décision future permis, **pas de fermeture hors ordre**.

## État vérifié, sans confusion des sous-lots

| Décision B | Statut précis | Dépendance / preuve | Next |
| --- | --- | --- | --- |
| **D7** | **OPEN / FUE_NO_GO** ; tests limités et documentation fusionnés, pas D7 produit | [#1164](https://github.com/hraaaaf/IAMINA-MVP/pull/1164), [#1172](https://github.com/hraaaaf/IAMINA-MVP/pull/1172) ; verdict D30 du chantier A et FUE patients/profils encore à vérifier | Après clôture D30, prouver les parcours réels D7 Web (types, traitements, persistance, FR/AR RTL, A/B, offline) |
| **D22** | **OPEN / FUE_NO_GO** ; préflight uniquement terminé | [#1173](https://github.com/hraaaaf/IAMINA-MVP/pull/1173), [#1174](https://github.com/hraaaaf/IAMINA-MVP/pull/1174), [#1175](https://github.com/hraaaaf/IAMINA-MVP/pull/1175) : préflight tests/docs fusionnés et exact-SHA CI/postmerge verts, **sans correctif produit** ; D19 clinique [#920](https://github.com/hraaaaf/IAMINA-MVP/pull/920) sous autorité A, décisions G1–G7 sans approbation | Contrat clinique et privacy/RTL validés, puis correction Web des unités/objectifs avec FUE complète |
| **D8** | **AUDIT PRÉPARATOIRE SEULEMENT ; OPEN** | Dépend de D5 (A) et D22 (B) ; [issues #964](https://github.com/hraaaaf/IAMINA-MVP/issues/964) et [#965](https://github.com/hraaaaf/IAMINA-MVP/issues/965) ouvertes | Ne pas activer de mapping pays→unité avant politique et contrats approuvés |
| **D10…D25** | Non examinées dans ce sous-lot | Respecter l'ordre et les dépendances propres détaillées dans Notion B | Auditer à tour de rôle après gates, sans anticipation de clôture |

**Événement externe observé :** PR D30 [#1169](https://github.com/hraaaaf/IAMINA-MVP/pull/1169) du chantier A **MERGED** à `main@9ba0f737e184e1c65ca83a4db14b3b22f220c0ae`. **Cela ne prouve pas que D30 est complètement certifiée** (postmerge, sécurité/privacy, FUE et statuts canoniques doivent être contrôlés par A). Aucune mutation D30 par le chantier B.

## D8 — préflight source statique, sans implementation

**Goal D8 fonctionnel (ultérieur) :** après D5 + D22, suggérer au besoin une unité de glycémie en fonction du pays **explicitement choisi**, selon une convention documentée/validée, tout en laissant chaque personne choisir et changer librement l'unité. **Le pays n'est ni une ordonnance, ni une géolocalisation vérifiée, ni un fuseau horaire implicite.**

**Source sur main `9ba0f737` :**

| Source | Constat dans code principal | Conséquence |
| --- | --- | --- |
| `frontend/lib/features/auth/onboarding_chat_screen.dart` | `String _unit = 'mg/dL'`, indépendamment de `_country` ; deux choix UI `mg/dL`/`mmol/L` ; la sélection `_unit` reste explicite et éditable | **Aucune suggestion conditionnelle pays→unité prouvée** ; le défaut de valeur de départ universelle doit être étudié avant un changement |
| Même écran `didChangeDependencies` | En mode `preferencesOnly`, relit `profile?.unitPreference` et le pays local connu ; IP peut seulement suggérer le pays non encore touché | Une suggestion D8 ne doit **jamais écraser une préférence persistée** |
| Même écran `_finish()` | Enregistre séparément `country: _country!` et `unitPreference: _unit` ; les bornes `targetRangeLow:70` et `targetRangeHigh:180` sont toujours écrites, quelle que soit l'unité | **GATE D22 obligatoire** : ne pas introduire de conversion ou objectif implicite |
| `frontend/lib/services/locale_preference_service.dart` | `suggestCountryFromIp()` est faillible et ne persiste pas le pays ; `setExperience` vérifie le code ISO choisi et le stocke explicitement ; pas de politique pays→unité dans ce service | Séparer géo-IP indicative, choix de pays D5, préférence unité D8 ; ne pas dépendre du réseau |
| `frontend/lib/services/country_choices.dart` | Liste ISO hors-ligne de pays/territoires ; pas de matrice d'unité clinique approuvée | Ne pas supposer `MA=mg/dL` ou `FR=mmol/L` |
| Tests actuels `onboarding_ip_country_test.dart`, `onboarding_explicit_country_boundary_test.dart` | 249 entrées ISO attendues ; échec de pays `OTHER` et `ZZ` ; langue seule n'écrit jamais un pays ; choix explicite de pays conservé | Tests D5 existants utiles mais **ne sont pas une validation de suggestion D8** |

**Choix non autorisés :** inventer une table `MA/FR/autres → unité` fondée sur la langue ou l'adresse IP, déduire la cible clinique, changer les seuils ou interpréter les valeurs legacy sans provenance, activer `g/L` sans contrat complet, auto-écraser une sélection ancienne. Voir [#964](https://github.com/hraaaaf/IAMINA-MVP/issues/964) : la France utilise également le g/L dans certaines pratiques ; la conformité d'une suggestion locale précise demande une validation. Le mapping D8 est donc **PENDING** et n'est pas inclus dans cette PR.

### Tests de réception D8 à exécuter ultérieurement

| Cas | Attendu | Statut |
| --- | --- | --- |
| Pays réellement choisi, policy approuvée disponible | Suggestion libellée comme suggestion, deux unités manuellement sélectionnables | NOT_RUN |
| Pays inconnu / IP non disponible / politique absente | Aucune suggestion mensongère ; choix utilisateur disponible | NOT_RUN |
| Pays modifié après une sélection manuelle | Préférence explicite jamais effacée ni remplacée à l'insu du patient | NOT_RUN |
| Ancien compte / profil déjà configuré | Préférence persistée conservée ; aucune réinterprétation des objectifs/mesures | NOT_RUN |
| Objectifs hérités sans unité/provenance | Pas de classification ou conversion clinique par simple convention pays | NOT_RUN |
| FR/AR RTL, clavier et mobiles/tablettes/desktop | BEFORE → Goal → mockup → AFTER mêmes viewports 390×844, 768×1024, 1280×900 ; navigation, offline/reload, isolation A→B | NOT_RUN |
| Home/Reports/IAmina/exports et synchronisation | Même unité affichée sans altérer quantité/source ni introduire d'effective target | NOT_RUN |

**Human gates :** D5 contrat pays réellement sélectionné, D19/D22 contrat clinique des cibles/calculs approuvé, politique de suggestion par pays sourcée et validée par les spécialistes compétents, privacy/FR-AR-RTL ; FUE produit complète, CI exact HEAD, merge/postmerge. **Aucune FUE D8 exécutée par ce preflight.**

## Closeout et continuité

- **Sous-lot actuel :** cadrage de priorité B et audit D8 *documentation uniquement*, pas de code clinique ni UI, DB ou Vercel. L'évaluation technique et le closeout CI restent à documenter sur le SHA de la PR correspondante.
- **Next exact :** contrôler CI prémerge du lot documentaire, fusionner docs seulement si verts, vérifier `main` et CI postmerge, synchroniser [Notion B](https://app.notion.com/p/40777c66336281729c03c9bb294e71b7) et issues D8. Puis reprendre **D7** seulement après les gates D30, puis **D22** après D19, puis **D8**, toujours dans cet ordre.
- **Verdict décisions B :** aucune fermeture produit D7/D22/D8 revendiquée par le présent fichier. Aucun pourcentage chantier calculé sans périmètre prouvé. Aucun Vercel sans accord explicite.
