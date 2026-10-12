# IAMINA V1-01 — Dossier de revue humaine CAL-09/10/11/12

**12 octobre 2026. État : propositions, aucune décision médicale ou privacy approuvée.** Code technique CAL-11 : PR DRAFT #945, `90855610f02d6e8d058527ec084cf5c853ef23ba`, [19/19 workflows verts](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38306271658), [USDA source](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38306271271), [Chrome FR/EN/AR](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38306271368) : 18/18 sans pageerror, 9/9 comparaisons BEFORE/AFTER. Produit local-first, zéro client annoncé, aucun merge ni Vercel. Ces preuves ne valent pas autorisation clinique.

## CAL-11 — Nutrition, relecteur diététicien/nutritionniste

**Vérifié** : cinq variétés de pommes crues avec peau dans USDA Foundation Foods April 2026, FDC 1750339–1750343, donnent **14.1–15.7 g glucides pour 100 g comestibles**; bananes FDC 1105073/1105314 : **20.1–23.0 g/100 g**, portions pelées **110/115 g**. SHA ZIP USDA : `186e988ec542e913f51ef62b86a47758e8cdd0d1dc3889e7b055581f3c09c77a`. La plage représente les cultivars *échantillonnés*, **pas** un intervalle de confiance universel ni une dose. USDA confirme que Foundation Foods mesure une variabilité d'échantillons et de cultivars : https://fdc.nal.usda.gov/Foundation_Foods_Documentation/ ; https://fdc.nal.usda.gov/data-documentation/.

**Choisir et signer** : A — plage indicative avec limite/source visibles ; B — restreindre aux cultivars/préparations explicitement identifiés ; C — suspendre la valeur générique en attendant des données locales. Le poids d'une pomme entière reste inconnu, les portions marocaines non curatées restent non numériques. Relire libellés FR/EN/AR/Darija, éviter toute prescription.
**Décision / motif / nom-qualification du relecteur / date / signature : NON RENSEIGNÉS.**

## CAL-09 — Jour clinique, clinicien + UX

**Vérifié dans le code** : `paired_meal_response.py` groupe par `pre_at.date()`; `personal_response.py` utilise `_event_at(entry).date()` deux fois ; `governed_longitudinal.py` utilise `observed_at.date()`. Le seuil de répétition préexistant est **3 observations et 2 jours**, pouvant différer UTC vs jour local. Ex. `2026-10-12T23:30Z` = **13 octobre 00:30** en `Africa/Casablanca` (Python `zoneinfo` vérifié).

**Options** : A — date civile du patient sous fuseau IANA explicitement choisi/sourcé (préférence technique *non approuvée*) ; B — jours UTC étiquetés comme tels ; C — offset original par événement, seulement si persistance/provenance vérifiées. Ne jamais inventer le fuseau via IP ni supposer Casablanca universel. Définir règle en cas de zone absente, voyage, historique et rétroactivité. Éprouver DST Paris 29 mars et 25 octobre 2026 (gap/fold), minuit, Home/Reports/IAmina, isolement patient. Réfs : https://docs.python.org/3/library/zoneinfo.html ; https://peps.python.org/pep-0495/.
**Décision / motif / clinicien + responsable produit / date / signatures : NON RENSEIGNÉS.**

## CAL-10 — Intervalle repas, clinicien

**Vérifié** : lien explicite `meal_episode_id`, une lecture avant et une après, `post_at > pre_at`, délai positif calculé, **aucune borne clinique maximale**; delta descriptif, non causal. Un intervalle très long est aujourd'hui techniquement possible.

**Options** : D — montrer seulement données descriptives et délai explicite ; E — bornage par protocole clinique spécifié et signé ; F — suspendre motifs résumés sans borne qualifiée. **Aucun seuil minute ne doit être inventé.** Éprouver inversion temporelle, multi-lectures, très longues durées, malformations et séparation patient.
**Décision / motif / clinicien + sécurité médicale / date / signatures : NON RENSEIGNÉS.**

## CAL-12 — Export PDF, clinicien + privacy/DPO + linguiste

**Vérifié** : `LocalReportPdf.build` est un générateur déterministe **ASCII/Helvetica seulement**, champs `LocalReportLine` non typés, UTC requis; arabe Unicode refusé. **PDF clinique patient OFF** et pas de revendication de partage.

**Contrat proposé, à arbitrer avant code** : type de mesures (glycémie mesurée/CGM/estimation nutrition séparés), unité et source par ligne, identité minimale, période UTC et timezone d'affichage, champs absents explicites, provenance, finalité/destinataire, consentement explicite valable et révocable, stockage/partage local-first, absence d'export automatique, sécurité des noms de fichiers et caches. Exiger Unicode, shaping arabe, ordre logique LTR/RTL, sélection/copie, extraction et lisibilité accessibles. Réfs : W3C https://www.w3.org/International/questions/qa-bidi-unicode-controls.en ; ISO PDF/UA https://www.iso.org/standard/64599.html (aucune conformité revendiquée).
**Schéma/consentement/mode de partage / clinique-privacy-FR-AR-Darija / date / signatures : NON RENSEIGNÉS.**

## Double contre-audit interne — aucun avis professionnel

**Exactitude** : le code actuel confirme l'ambiguïté de date, le délai repas non borné et l'export ASCII fail-closed. **Adversarial** : une plage USDA peut sembler personnalisée, la date UTC peut modifier artificiellement l'évidence, un délai éloigné peut être pris pour une réponse thérapeutique, le PDF peut exposer l'identité. Contrôles conservatoires : maintien DRAFT, aucune nouvelle règle médicale, PDF OFF.

## Gate et Next

**0/4 arbitrages signés** (CAL-09, CAL-10, CAL-11, CAL-12), **0 revue formelle** sur #945 au dernier contrôle. Faire désigner de vrais relecteurs qualifiés, leur soumettre ce dossier et récupérer choix, motifs, restrictions, noms, dates et signatures. Après décisions : changement de code ciblé, tests synthétiques et visuels, CI sur nouveau HEAD, revue globale du diff des PR DRAFT #920/#943/#944/#945, **permission explicite avant merge**, validation post-merge, autorisation Vercel séparée. Sans reviewers, ce lot est à **human gate réel**; aucun patient. Décision V1 #19 ouverte; P5 historique 6/12=50% distinct du % V1-01 inconnu.
