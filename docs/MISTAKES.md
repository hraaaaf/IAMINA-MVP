# Mistakes Log

Errors caught during development. Read at the start of every session to avoid repeating them.

---

## Tools

**1. One file per edit call.**
Attempting to modify two different files in a single tool call injects content into the wrong file. Use separate calls per file.

**2. Clean generated code.**
Auto-generated imports (`json_annotation`, `dart:convert`, etc.) left in place pollute lint reports. Strip unused imports from generated files immediately.

**3. Async test syntax (Drift).**
`() async` not `async` alone in test closures. Missing parentheses breaks `build_runner` compilation.

**4. Windows sandboxing.**
`run_command` fails on Windows. Create file structures via write tools. Delegate `manage.py check` to the user if the environment blocks execution.

**5. `__init__.py` re-exports during module migrations.**
When moving modules, add re-exports in `__init__.py` to avoid breaking circular imports or global config files like `urls.py`.

---

## Flutter

**6. `withOpacity` is deprecated.**
Use `.withValues(alpha: ...)` to align with Flutter 2024+ standards.

**7. Accidental field deletion during refactoring.**
When adding a new constructor parameter, verify all existing fields are still present. Missing `heroTag` after adding `initialOffset` caused immediate compile error.

**8. Theme variables in helper methods.**
Always define `final isDark = Theme.of(context).brightness == Brightness.dark;` at the top of any `build` or helper method that uses it.

**9. Provider injection.**
All classes accessed via `context.watch` or `context.read` must be registered in `MultiProvider`. Common miss: `PatientProfileData` from Drift.

**10. `Expanded` inside `SingleChildScrollView`.**
Never nest a widget with `Expanded` inside `SingleChildScrollView` without a fixed-height parent. Results in a blank screen on web.

**11. `GoRouter` in `build` method.**
Never create the `GoRouter` instance inside `build` — it resets navigation state on every rebuild. Instantiate in `initState` or at the app level.

**12. `StreamProvider<T?>` typing.**
When watching a `StreamProvider<T?>`, watch the nullable type `T?` explicitly. Type mismatch causes a runtime provider lookup failure.

**13. Django cache not rolled back in TestCase.**
`django.test.TestCase` wraps each test in a DB transaction but does NOT reset the Django cache. If test A writes to cache and test B runs alphabetically after it, test B sees stale cache data. Fix: `setUp` with `cache.clear()` + unique usernames per test (`f"user_{self._testMethodName}"`).

**14. Demo seed in production.**
`db.seedDemoData()` called unconditionally on empty DB shows fake clinical data ("87% en cible") to real patients. Always guard with `kDebugMode` in Flutter. In Django, seed commands must be opt-in only.

**15. `FallbackProvider` silently swallows quota errors.**
When Gemini daily cap is hit and no paid failover is configured, returning the generic `FallbackProvider` response gives no signal to the user that they've run out of quota. Use `QuotaExhaustedProvider` instead — it surfaces the quota message explicitly so users understand and can upgrade.

---

## Navigation

**16. `_NavItem._navigate()` must stay in sync with index assignments.**
> ✅ FIXED in P6-A (Phase 24): nav/routes are now generated from `ModuleRegistry`; the integer-index
> switch is gone. Kept as a warning — do not reintroduce index-based routing.
The sidebar `_NavItem` uses integer indices to decide which route to push. If the index-to-route mapping in `_selectedIndex()` or the item list is changed, `_navigate()` **must** be updated in the same commit. Mismatched indices cause silent mis-routing (e.g. pressing IAmina navigates to /ajouter). Checklist:
1. `_selectedIndex()` — path → int
2. Sidebar `_NavItem(index: N, ...)` constructor calls
3. `_NavItem._navigate()` switch cases
4. Bottom `NavigationBar.onDestinationSelected` cases
All four must agree.

**17. Flutter web cannot be tested with Playwright / Selenium.**
Flutter web renders entirely to a `<canvas>` element — the DOM contains no visible widgets, no text nodes, no buttons. `getByText()`, `locator('button')`, and all CSS/text selectors return empty. `signInAnonymously()` also requires a live Firebase project and network. Testing Flutter web UI requires **Flutter Integration Tests** (`flutter_test` + `IntegrationTestWidgetsFlutterBinding`), not browser-automation tools.

---

## LLM / AI

**18. Smaller LLM models are unreliable with JSON schemas.**
`gemini-2.5-flash-lite` frequently ignores the specified JSON schema and returns keys like `"response"` instead of the required `"reply"`. Always use `gemini-2.5-flash` (or better) for schema-constrained prompts. Add a parser-level alias fallback (`_REPLY_ALIASES`) as a safety net, but treat it as a last resort — not an excuse to use a weaker model.

**19. `strip_fences()` must handle newlines after the opening fence.**
LLMs sometimes return ` ```json\n{...}\n``` ` (newline immediately after `json`). A regex that only strips ` ```json ` (with a space) will leave a leading newline, causing `json.loads()` to fail. Use `re.sub(r'^```(?:json)?\s*', '', s)` (with `\s*`) to strip the fence and any trailing whitespace including newlines.

---

## Product

**20. IAmina is NOT a POC — it is a real medical product.**
Never refer to IAmina as a "proof of concept", "POC", "demo", or "prototype" in code comments, documentation, commit messages, or conversation. It is a production medical application used by real patients managing diabetes. Consequences of incorrect framing: reduced rigor in safety decisions, misleading documentation, loss of user trust.

---

## Medical / Clinical

**21. Treatment-type-specific advice must be conditional on `treatment_type`.**
Never include insulin-specific instructions (e.g. "check your dose", "verify your injection") in generic alert messages shown to all patients. Type 2 patients on oral medication or lifestyle-only management will receive confusing or inapplicable advice — "check your insulin" has no meaning for them and may cause distress or unsafe self-experimentation.

**Rule:** Before including any insulin-related content in an alert or recommendation, check `profile.treatment_type` and gate on `insulin_dependent` / `insulin_pump` / `mdi` values. Always provide a safe universal fallback ("Ne modifie pas ton traitement sans avis médical.") for patients whose treatment type is unknown or non-insulin.

*Caught in diabetologist review (commit e64a8b6): `HYPER_SEVERE` alert previously instructed all patients to "Vérifiez votre insuline" — removed and replaced with universal guidance.*

**22. Demo seed staleness — IAmina 14-day window.**
`setup_demo` seeds log entries with absolute dates at first run. After 14 days all entries fall outside IAmina's analysis window, causing it to report "pas de données" despite the DB containing records. This produces silent degradation: the app appears functional but the AI returns useless responses.

**Fix pattern:** Never store absolute seed dates. Either:
- Use relative dates (`now() - N days`) recomputed at each seed call, or
- Add a `--reset` flag (`python manage.py setup_demo --reset`) that deletes and reseeds entries relative to today.
**Always run `setup_demo --reset` before a demo or QA session longer than 14 days after initial setup.**

---

## Backend / Infrastructure

**23. Never use a module-level dict as a cross-request session store.**
`_pending: dict = {}` in `documents.py` worked in single-process dev but silently failed on any multi-worker deploy (Gunicorn `--workers 3` = 3 separate dicts; `confirm_import` on a different worker always returns 404). Also a DoS vector: unauthenticated uploads with no TTL bloat memory indefinitely.

**Fix pattern:** Use `django.core.cache` (backed by Redis in production). Set a bounded TTL (`_PENDING_TTL = 3600`). Use namespaced keys (`"pulper:pending:{batch_id}"`). Consume-once semantics: `cache.get()` then `cache.delete()` before processing, not `pop()` on a dict.

**Note:** Django cache with `IGNORE_EXCEPTIONS=True` gracefully degrades to `None` on Redis miss — the app stays up, the user sees "Session expirée — veuillez réimporter" and can retry.

---

## IAmina — Throttle & Streaming

**24. Advice throttle SSE : la garantie est sur ce que le patient voit, pas sur la DB.**
Le tail-hold (sentence-buffering dans `_event_generator()`) filtre les disclaimers avant qu'ils atteignent le client. Pour le premier disclaimer de la fenêtre 24h : le client le voit, le timestamp est stampé, et `apply_advice_throttle()` dans `stream_chat()` le retire ensuite de `full_reply` avant persist DB. La copie DB n'a donc pas le disclaimer — c'est voulu. Ce qui compte est que le patient l'a vu et que le timestamp est posé.

**Règle :** ne jamais supposer que DB reflète exactement ce que le patient a vu en mode SSE. Le canal d'autorité pour "le patient a vu le disclaimer" est `deep_memory.last_advice_given_at`, pas l'historique de chat.

**25. Arabic comma ، (U+060C) non couvert par `_SENTENCE_RE`.**
`_SENTENCE_RE = re.compile(r'(?<=[.!?؟\n])\s+')` ne split pas sur ،. Conséquence : une réponse Darija courte du type `"الماكلة زينة، شوف الطبيب."` est traitée comme une seule phrase. Si suppression tenterait de la vider, `apply_advice_throttle()` retourne l'original (garde anti-vide) — le disclaimer passe, timestamp inchangé.

**À ne pas corriger en ajoutant ، au splitter :** trop agressif, ، est une virgule ordinaire en arabe. Le garde anti-vide est le bon comportement. Documenter comme gap accepté, pas comme bug à corriger.
