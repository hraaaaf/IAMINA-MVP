# P0-MENA-2 — RTL screen certification

**Status:** technically certified after permanent Flutter gates pass.

**Scope:** all routes currently reachable from `app_router.dart` and `diabetes_module.dart`, plus the shared navigation shell.

## Certified registry

| Route | Widget | Source | Result |
|---|---|---|---|
| `/login` | `LoginScreen` | `features/auth/login_screen.dart` | Directional layout |
| `/reset-password` | `ResetPasswordScreen` | `features/auth/reset_password_screen.dart` | Directional layout |
| `/consent` | `ConsentScreen` | `features/auth/consent_screen.dart` | Directional layout |
| `/onboarding` | `OnboardingChatScreen` | `features/auth/onboarding_chat_screen.dart` | Directional bubbles and corners |
| `/profile` | `ProfileScreen` | `features/profile/profile_screen.dart` | Directional padding |
| `/dashboard` | `DashboardScreen` | `features/dashboard/dashboard_screen.dart` | Directional padding |
| `/summary` | `AISummaryScreen` | `features/journal/ai_summary_screen.dart` | Directional padding |
| `/journal` | `JournalScreen` | `features/journal/journal_screen.dart` | Directional padding, alignment and corners |
| `/importer` | `ImportScreen` | `features/import/import_screen.dart` | Directional padding |
| `/ajouter` | `AddLogScreen` | `features/journal/add_log_screen.dart` | No physical directional primitive found |
| `/pulper` | `DocumentImportScreen` | `features/documents/document_import_screen.dart` | Directional padding |
| `/journal/:id/edit` | `EditLogScreen` | `features/journal/edit_log_screen.dart` | Directional padding |
| shell | `MainShell` | `features/navigation/main_shell.dart` | Directional gradients, padding and active marker |

## Permanent executable proof

`frontend/test/rtl_screen_contract_test.dart` enforces all of the following:

1. every route declared in the application router or diabetes module exists in the registry;
2. every registry entry resolves to the expected widget source;
3. registered screens contain no physical `left`/`right` layout primitives covered by the contract;
4. Arabic localization resolves to `TextDirection.rtl` in an actual Flutter widget test.

The contract rejects:

- `EdgeInsets.only(left/right)`;
- `EdgeInsets.fromLTRB`;
- physical `Alignment.*Left/*Right`;
- `TextAlign.left/right`;
- physical `Positioned(left/right)`;
- physical `BorderRadius.only` corners;
- an explicitly forced LTR `Directionality` inside a registered screen.

Any new route that is not explicitly registered makes the Flutter suite fail. Any regression back to a physical primitive in a registered screen also fails.

## CI

The permanent frontend job now runs both:

```bash
flutter analyze --no-fatal-infos
flutter test --no-pub
```

Before this lot, Flutter tests existed but were not a mandatory GitHub Actions gate. They are now blocking.

## Conversion rules

The screen sources use semantic direction rather than physical orientation:

- `start` / `end` instead of `left` / `right`;
- `EdgeInsetsDirectional` instead of physical edge insets;
- `AlignmentDirectional` instead of left/right alignment;
- `BorderRadiusDirectional` for asymmetric bubbles;
- `PositionedDirectional` for the active navigation marker.

`frontend/tool/rtl_directionalize.py` is an idempotent, registry-scoped maintenance codemod. It does not scan or modify unrelated files.

## Non-claims

This certification proves technical directionality for the current routed surface. It does **not** claim:

- native-speaker approval of Arabic or Darija wording;
- clinical approval of translated safety messages;
- visual-design preference approval by a human reviewer;
- completion of the separate Darija high-severity corpus gate.

Those remain independent roadmap gates.
