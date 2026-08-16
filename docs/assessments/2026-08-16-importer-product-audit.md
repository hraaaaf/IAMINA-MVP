# Importer product audit — 2026-08-16

Status: **CLOSED — PASS 9.5/10**.

## Product contract

Importer is the acquisition hub. Its primary real action is Document Import. Direct CGM connectors may be shown only as unavailable/future capabilities and must never look connected. Existing local-data status must describe what is actually stored, without inventing urgency.

## SMART section audit

| Section | Product interest | Final score | Decision / status |
|---|---|---:|---|
| Canonical header | Establishes acquisition context consistently | 9.5/10 | KEEP |
| Local-data status banner | Reassures the user that readings exist locally and gives useful recency context | 9.5/10 | IMPROVED — uses maximum effective event time `loggedAt ?? createdAt` |
| Three-day stale warning | Attempted to flag old local data | Removed | REMOVE — arbitrary urgency with no actionable connector path |
| First-use Document Import CTA | Gives a real productive action when no readings exist | 9.5/10 | KEEP |
| Returning-user Document Import card | Keeps the only production acquisition path visually primary | 9.5/10 | KEEP |
| Document-type chips | Clarify accepted acquisition use cases | 9.0/10 | KEEP; detailed formats belong to Document Import |
| Direct connections section | Separates future device integrations from the working document path | 9.0/10 | KEEP — unavailable state is explicit |
| Dexcom G6/G7 card | Communicates roadmap capability without fake connection | 9.0/10 | KEEP as unavailable / soon only |
| Abbott LibreLink card | Same | 9.0/10 | KEEP as unavailable / soon only |
| Unavailable connector action | Prevents dead controls masquerading as working integrations | 9.5/10 | KEEP |
| Demo-data control | Useful development aid only | 9.5/10 debug / N/A production | KEEP behind `kDebugMode` |
| Desktop two-column connector layout | Uses space efficiently without changing semantics | 9.0/10 | KEEP |
| Mobile single-column layout | Keeps acquisition cards readable and touch-safe | 9.5/10 | KEEP — real Chrome 390×844 certified |

## Verified correction

- Baseline `_loadStats()` ordered rows by `createdAt DESC` and then displayed `loggedAt ?? createdAt`, so an older measurement imported later could masquerade as the latest reading.
- `_loadStats()` now computes the maximum effective event time across local readings using `row.loggedAt ?? row.createdAt`.
- `_totalLogs` is derived from the same row set used for the status computation.
- The arbitrary three-day stale-warning branch and `_isDataStale` state are removed.
- The status banner remains factual and neutral: local reading count + actual latest stored reading time.
- Dexcom and Libre remain explicitly unavailable; no connector, notification, schema, persisted-data or clinical rule was added or changed.

## Certification evidence

Runtime PR: **#261**  
Runtime merge SHA: `88f2e2c057309bb73daee369ce086524a54a5f97`

Exact-head before merge (`d392d208983c6c18fc86c75296c0f318f134ace0`):
- CI #2515 — PASS
- Django migration drift #2327 — PASS
- UI screenshot audit #129 — PASS
- UI browser screenshot certification #92 — PASS
- Real Chrome `importer-390x844.png` inspected: Document Import remains primary; Dexcom/Libre are clearly `BIENTÔT` / unavailable; no fake action, urgency or overflow.

Post-merge (`88f2e2c057309bb73daee369ce086524a54a5f97`):
- CI #2517 — PASS
- Django migration drift #2329 — PASS
- UI screenshot audit #131 — PASS
- UI browser screenshot certification #94 — PASS

## Final assessment

**9.5/10 — PASS.** The production acquisition path is truthful and clear, the latest-reading status reflects event time rather than import time, and unavailable connectors cannot masquerade as working integrations. Lower-scored future-connector cards are intentionally informational and do not weaken the primary production flow.

MENA roadmap numerator remains unchanged by this page audit.
