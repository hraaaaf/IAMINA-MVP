# Add Log — decision A

Date: 2026-08-15

## Decision

Add Log remains a glucose-reading capture flow with optional context attached to that reading.

Medication intake, including insulin, is canonical in `MedicationEvents` / the Medications surface and is no longer entered from Add Log.

Legacy `/ajouter?focus=insulin` intent routes to Medications instead of exposing a second intake path.

## Why

- `LogEntries.bloodSugar` is required, so Add Log is not a truthful generic event journal.
- Keeping insulin in both `LogEntries.insulinUnits` and `MedicationEvents` creates two competing intake sources.
- A focused glucose flow is simpler and avoids implying that meal/activity/insulin are standalone logs when the current persisted model cannot represent them independently.

## Scope

No database migration and no clinical threshold change.

The existing nullable `LogEntries.insulinUnits` column is retained for backward compatibility and historic records, but new Add Log entries write it as null.

MENA roadmap numerator is unchanged.
