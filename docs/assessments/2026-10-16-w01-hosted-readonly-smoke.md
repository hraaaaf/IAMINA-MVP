# W01 — 16/10/2026 : vérifications HTTPS existantes (lecture seule)

**Chantier : W01 uniquement. Statut : preuves partielles ; G1-G7 NON VALIDÉS collectivement.**
Provenance : métadonnées et GET HTTP réalisés par l'app connectée Vercel le 16 octobre 2026, sans nouveau déploiement, sans requête patient, sans Neon IAMINA production et sans lecture de secrets. Les réponses ne constituent pas un essai navigateur interactif ni un contrôle de la Root Directory.

| Service existant | Résultat GET observé | Limite |
|---|---|---|
| `https://iamina-review.vercel.app/` | **HTTP 200**, document HTML Flutter/IAMINA | Prouve uniquement le service de l'origine frontend, pas la branche Git, l'identité d'utilisateur, l'API depuis le navigateur ni les settings Vercel |
| `https://iamina-certified.vercel.app/api/v1/health` | **HTTP 200**, JSON `{"status":"ok","db":"ok","cache":"unavailable"}` | L'API confirme son contrôle interne de DB ; **n'identifie ni la branche, ni la base, ni le projet Neon**, ni la séparation prod/preview |
| Preview Web préexistante `iamina-925-flutter-empty-pg-20261015-m8eld3zvx.vercel.app/` | **HTTP 200**, document HTML Flutter | SHA Vercel `675d8c5afd27a9a128d2b24ac6f55e6f1cb22314` (branche preview ancienne) ; pas de preuve de flux vers le backend |
| Preview API préexistante `iamina-925-django-empty-pg-20261015-7lsddl41h.vercel.app/api/v1/health` | **HTTP 404** | Ce déploiement existant ne fournit pas le parcours de santé attendu à ce chemin. Son SHA `f86d1c13b464ed24df4adcb57440b3355cd1c083` n'est ni celui du frontend ci-dessus ni la candidate W01 actuelle |
| Projet séparé `iamina-925-synthetic-ingress-20261015` | Page HTML de cache purement synthétique **HTTP 200**, explicitement *sans backend ni patients* | Ne sert pas d'API IAMINA ni de preuve d'intégration clinique |

Les deux déploiements Vercel précédemment observés `target=production` (`iamina-review` : `60de80ec070157f912cb62c80a7ded1e9bde75a6` ; `iamina-certified` : `9d24cff11fc422fe0c6235757dbf317eebe32912`) diffèrent encore du SHA `main` de l'audit. L'API Vercel connectée expose projets, déploiements, URLs et noms de variables, mais **pas** les paramètres effectifs Root Directory ni les valeurs/fingerprints des DSN. Une observation HTTP positive ne remplace donc pas G1–G5.

**Preuve indépendante G6 (en GitHub CI local uniquement)** : [PR #1106](https://github.com/hraaaaf/IAMINA-MVP/pull/1106) intégrée sur `main@19ad69aed3223027b0f13fe59854d834825bcd73`. [W01 CI #38926248888](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38926248888) et [migrations #38926248493](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38926248493) **SUCCESS** prémerge ; [générale #38926248728](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38926248728) **SUCCESS**. Le log W01 contient explicitement `PASS W01-G6 disposable PG16` : dump Django migré, restauration en base jetable distincte, marqueur synthétique, transaction rollback, `manage.py migrate --check`. Les CI postmerge [générale #38926794793](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38926794793), [W01 #38926794725](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38926794725) et [migrations #38926794826](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38926794826) doivent être contrôlées sur le SHA fusionné.

**À ne pas certifier :** restauration sur Neon distant, downgrade d'une migration, backup de production, vrai Web→Django→Neon preview, identité patient, W02, W14 ou autorisation de déploiement.

**Next W01 :** G1 Root Directory et branches Git effectives dans dashboard Vercel ; G2/G3 séparation et protection Neon/env ; G4/G5 essais distants uniquement sur ressources synthétiques autorisées ; G6 restauration/rollback Neon sandbox ; G7 closeout exact SHA.
