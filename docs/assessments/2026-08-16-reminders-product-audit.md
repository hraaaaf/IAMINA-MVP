# Reminders product audit — 2026-08-16

Status: SMART audit complete; truthfulness/destructive-action corrections identified; runtime correction pending.

## Product contract

Reminders are locally stored user-authored memory aids. In the current product version they do not schedule OS notifications and must not imply clinical monitoring, adherence tracking or treatment instructions.

## SMART section audit

| Section | Product interest | Score | Decision / status |
|---|---|---:|---|
| Canonical header | Clear scope and explicitly avoids invented follow-up | 9.5/10 | KEEP |
| “New reminder” composer | Core utility | 9.2/10 | KEEP |
| No-system-notification notice | Critical truthfulness disclosure | 9.8/10 | KEEP |
| Reminder title | User-authored neutral content | 9.5/10 | KEEP |
| Date/time picker | Core scheduling metadata | 9.0/10 | KEEP; locale formatting is already handled in the separate i18n track |
| Add reminder CTA | Clear factual action | 9.5/10 | KEEP |
| Saved-reminder list | Core history/state surface | 9.5/10 | KEEP |
| Empty state | Truthful and minimal | 9.0/10 | KEEP |
| Enabled/disabled switch | Changes a local boolean but cannot enable any system notification | 3.5/10 | REMOVE until a real notification contract exists |
| Enabled/disabled bell icon | Visually reinforces the same non-functional state | 4.0/10 | SIMPLIFY after switch removal |
| Delete action | Necessary management action | 7.5/10 | IMPROVE — currently deletes immediately with no confirmation |

## Verified findings

- The screen explicitly states that system notifications are not enabled in this version.
- `Switch` calls only `db.setReminderEnabled(item.id, value)`; this screen has no notification-scheduling integration.
- The enabled/off icon therefore represents a local database flag rather than a working reminder-delivery state.
- Delete calls `db.deleteReminder(item.id)` immediately without a confirmation dialog.
- Reminder content is free user text; there is no treatment recommendation or dose logic in this surface.
- Fixed `dd/MM/yyyy HH:mm` formatting is already covered by the separate MENA/i18n date-formatting track and should not be duplicated here.

## Recommended runtime correction

- Remove the enabled/disabled switch and active/off bell semantics until OS notification delivery is actually implemented.
- Keep reminder title and due date as factual stored metadata.
- Add explicit confirmation before deletion.
- Do not introduce medication adherence, dose or treatment semantics into this page.

## Certification gate

No final page score or CLOSED status before runtime correction, exact-head gates, real Chrome 390×844 inspection, merge/post-merge recertification and canonical closeout.

MENA roadmap numerator remains unchanged by this page audit.
