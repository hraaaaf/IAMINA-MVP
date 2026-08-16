# Importer product audit — 2026-08-16

Status: SMART audit complete; truthfulness corrections implemented; certification pending.

## Product contract

Importer is the acquisition hub. Its primary real action is Document Import. Direct CGM connectors may be shown only as unavailable/future capabilities and must never look connected. Existing local-data status must describe what is actually stored, without inventing urgency.

## SMART section audit

| Section | Product interest | Score | Decision / status |
|---|---|---:|---|
| Canonical header | Establishes acquisition context consistently | 9.5/10 | KEEP |
| Local-data status banner | Reassures the user that readings exist locally and gives useful recency context | 6.5/10 baseline → 9.3/10 provisional | IMPROVED — now uses maximum effective event time `loggedAt ?? createdAt` |
| Three-day stale warning | Attempted to flag old local data | 4.5/10 baseline | REMOVED — arbitrary urgency with no actionable connector path |
| First-use Document Import CTA | Gives a real productive action when no readings exist | 9.5/10 | KEEP |
| Returning-user Document Import card | Keeps the only production acquisition path visually primary | 9.5/10 | KEEP |
| Document-type chips | Clarify accepted acquisition use cases | 9.0/10 | KEEP; actual file-format details belong to Document Import |
| “Direct connections” section | Separates future device integrations from the working document path | 8.5/10 | KEEP if unavailable state stays unmistakable |
| Dexcom G6/G7 card | Communicates roadmap capability without fake connection | 8.5/10 | KEEP as unavailable / soon only |
| Abbott LibreLink card | Same | 8.5/10 | KEEP as unavailable / soon only |
| Unavailable connector action | Prevents dead controls masquerading as working integrations | 9.5/10 | KEEP |
| Demo-data control | Useful development aid only | 9.5/10 debug / N/A production | KEEP behind `kDebugMode`; never surface in production |
| Desktop two-column connector layout | Uses space efficiently without changing semantics | 9.0/10 | KEEP |
| Mobile single-column layout | Keeps acquisition cards readable and touch-safe | 9.0/10 | KEEP |

## Verified findings

- Baseline `_loadStats()` ordered rows by `createdAt DESC` and then displayed `loggedAt ?? createdAt`, so an older measurement imported later could masquerade as the latest reading.
- Baseline `_isDataStale` turned the status into a warning after exactly three days although no clinical or connector contract established three days as an authoritative freshness threshold.
- The stale warning was especially low-value while both direct CGM connectors are explicitly unavailable.
- First use routes to the real `/pulper` Document Import path.
- Dexcom and Libre cards use `_UnavailableAction` and a localized “soon” badge rather than fake callbacks.
- Demo seeding is protected by `kDebugMode`.
- The page correctly makes Document Import primary over future direct connections.

## Runtime correction

Branch: `agent/importer-product-audit-v2`

- `_loadStats()` now computes the maximum effective event time across local readings using `row.loggedAt ?? row.createdAt`.
- `_totalLogs` is derived from the same row set used for the status computation.
- The arbitrary three-day stale-warning branch and `_isDataStale` state are removed.
- The status banner remains factual and neutral: local reading count + actual latest stored reading time.
- No connector, notification, schema, persisted data or clinical rule was added or changed.

## Certification gate

No final page score or CLOSED status before exact-head gates, real Chrome 390×844 inspection, merge/post-merge recertification and canonical closeout.

MENA roadmap numerator remains unchanged by this page audit.
