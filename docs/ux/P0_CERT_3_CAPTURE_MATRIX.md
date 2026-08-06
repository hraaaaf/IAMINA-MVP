# P0-CERT-3 — Matrice finale de captures

## Statut

`CAPTURE_MATRIX_COMPLETE`

Ce lot certifie la production de captures internes réelles et distinctes. Il ne constitue pas encore l'audit UX final ni la classification des défauts, qui relèvent de P0-CERT-4.

## Source certifiée

- Commit produit de départ : `bf77fb36d2d92284fa361029b856b37dbbcb7fca`
- Build Flutter Web : `--release --dart-define=IAMINA_AUDIT_ACCESS=true`
- Origine : `127.0.0.1`
- Accès : `audit=visual-cert`
- Fuseau navigateur : `Africa/Casablanca`

Le workflow temporaire de capture a été supprimé avant ouverture de la PR. Aucun code produit, backend, schéma, migration, compteur MENA ou traduction métier n'est modifié par ce lot.

## Exécution valide

- Workflow run : `31059862588`
- Commit technique temporaire de capture : `844de00f580e42c6824eefa00de2d0e33cac19c3`
- Artifact ID : `8951732813`
- Artifact : `p0-cert-3-capture-matrix`
- Taille : `1 655 722` octets
- Digest : `sha256:3c2e7aa1f04c32950bd2d9c5babbba25e04e1225b5b1ac37784bab8b3697b403`
- Résultat : 25 vues rendues, 25 `flutter-view` présents, 0 erreur de page bloquante.

## Matrice

| Profil | Taille | Locale | Dashboard | Journal | Importer | Pulper | Profil |
|---|---:|---|---:|---:|---:|---:|---:|
| Desktop FR | 1440×1000 | `fr-FR` | ✅ | ✅ | ✅ | ✅ | ✅ |
| Mobile FR | 390×844 | `fr-FR` | ✅ | ✅ | ✅ | ✅ | ✅ |
| Mobile compact FR | 360×560 | `fr-FR` | ✅ | ✅ | ✅ | ✅ | ✅ |
| Mobile AR | 390×844 | `ar-MA` | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tablette AR | 768×1024 | `ar-MA` | ✅ | ✅ | ✅ | ✅ | ✅ |

Les images ouvrent les routes internes attendues :

- `/dashboard`
- `/journal`
- `/importer`
- `/pulper`
- `/profile`

## Exécution invalidée

Le premier passage, workflow run `31059464079`, a été rejeté. Le navigateur n'avait pas de locale explicite et Flutter Web échouait avant rendu avec `Incorrect locale information provided`. Les 25 images blanches de ce passage ne sont pas des preuves et ne sont pas utilisées.

## Limite du présent lot

La présence d'une page rendue ne signifie pas que son contenu est conforme. L'inspection préliminaire a notamment observé du contenu central français dans certaines vues arabes. Cette observation est transmise à P0-CERT-4 pour analyse page par page, sévérité et verdict final.
