# IAMINA V1 decision #16 — Selectable companion replies

**BEFORE and written mockup before implementation**: [issue #979](https://github.com/hraaaaf/IAMINA-MVP/issues/979), code `_MessageBubble` uses `Text(message.text)`, not selectable; role labels, provenance and urgent liveRegion already exist. [Empty companion 390x844 baseline](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38322527667/artifacts/11779667087) proves only initial viewport, NOT reply appearance. The accompanying exact-HEAD visual workflow builds **actual HEAD minus this one changed source blob** for BEFORE and current HEAD for AFTER, with the same `p1-proof=1` wholly synthetic deterministic reply and viewport/semantics controls.

**Goal**: native selection/copy only on a user's gesture, preserve text, colors, margins, role labels, local fallback provenance, urgent alert liveRegion, and RTL FR/EN/AR. No custom clipboard write, no analytics, no OS push, no LLM egress or user data changes.

**Patch**: one widget `SelectableText` replaces `Text` in bubble without changing style or layout. Flutter widget tests synthetic service across FR/EN/AR at 390/768/1280 and urgent alert selectable text, no patient/network.

**Required proof**: exact-HEAD full CI + designated real Chromium screenshot workflow BEFORE/AFTER at same viewport, inspect screenshot differences, no JS failures, confirm text selection. Scope limitation: the legacy `amina_chat_view_presentation.dart` is a separate surface and remains to audit; this covers canonical `CompanionConversationScreen` only. Clipboard OS may retain copied medical text, so privacy review before merge. No merge or Vercel without permission, CGM #1/#25 last.
