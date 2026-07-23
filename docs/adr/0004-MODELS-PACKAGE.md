# ADR 0004 — `diabetes/models/` en package

- **Statut :** accepté (rétroactif)
- **Date :** 2026-04-17
- **Mis à jour :** 2026-06-03 — app renommée `logs` → `diabetes`
- **Décideurs :** Software Architect, Senior SWE

## Contexte

`diabetes/models.py` (devenu `diabetes/models.py`) définissait `PatientProfile`, `LogEntry`, `AISummary` et `DemoFeedback` dans un même fichier (~300 lignes). `TEAM.md` (Software Architect, signal d'alerte) : "Plus de 3 modèles dans un même fichier → envisager de séparer".

Le plan MVP (`AMINA_MVP_PLAN.md` §2) prévoit en outre `AuditLog` et des fichiers dédiés par agrégat (`patient.py`, `entry.py`, `summary.py`, `feedback.py`, `audit.py`), pour anticiper une extraction future en apps Django dédiées (patients, entries, ai, …).

## Décision

Remplacer `diabetes/models.py` par un package `diabetes/models/` :

- `patient.py` — `PatientProfile` + choix + validateurs.
- `entry.py` — `LogEntry` + choix de repas / source.
- `summary.py` — `AISummary`.
- `feedback.py` — `DemoFeedback`.
- `audit.py` — `AuditLog`.
- `chat.py` — `AIChatMessage`.
- `memory.py` — `IAminaMemorySnapshot`, `IAminaDeepMemorySnapshot`.
- `lab_report.py` — `LabReport`.
- `__init__.py` ré-exporte les classes pour les migrations et pour la compatibilité `from diabetes.models import LogEntry`.

Chaque modèle déclare `class Meta: app_label = 'diabetes'` pour éviter toute ambiguïté d'enregistrement.

## Conséquences

**Positives**

- Un fichier par agrégat ; les changements de `LogEntry` ne polluent plus les diff de `PatientProfile`.
- L'extraction future en app dédiée consiste à déplacer un fichier et son test, pas à démêler un module.
- Les imports existants (`from logs.models import ...`) continuent de fonctionner grâce au `__init__.py`.

**Négatives**

- Double découverte possible si `diabetes/models.py` et `diabetes/models/__init__.py` coexistent — Python résout le package, mais le fichier `.py` orphelin prête à confusion. Traité : `diabetes/models.py` supprimé (commit `d67bc5c`).
- Les migrations historiques continuent de référencer `logs.models` au niveau module, ce qui reste valide tant que `__init__.py` ré-exporte chaque modèle.

## Alternatives rejetées

- **Garder le fichier unique et ajouter les modèles Amina** : aurait dépassé 500 lignes et rendait la revue plus lourde encore.
- **Extraire immédiatement les agrégats en apps Django distinctes** : trop tôt — frontières métier non stabilisées par l'usage (cf. ADR 0001 pour la même logique côté views).

## Suivi

- Les nouveaux modèles (ex. AuditLog dans `audit.py`) suivent la même règle : un agrégat = un fichier.
- La directive `app_label = 'diabetes'` reste obligatoire tant que le package vit dans l'app `logs`.
