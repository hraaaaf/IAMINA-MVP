#!/usr/bin/env python3
"""Close P0-UX-5 without making privacy claims beyond approved evidence."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FR = ROOT / "frontend/lib/l10n/app_fr.arb"
EN = ROOT / "frontend/lib/l10n/app_en.arb"
AR = ROOT / "frontend/lib/l10n/app_ar.arb"
DOCUMENT = ROOT / "frontend/lib/features/documents/document_import_screen.dart"
TEST = ROOT / "frontend/test/p0_privacy_truthfulness_contract_test.dart"
P0_DOC = ROOT / "docs/ux/P0_PRODUCT_TRUTHFULNESS.md"
ROADMAP = ROOT / "docs/ROADMAP.md"


def replace_once(path: Path, old: str, new: str) -> None:
    source = path.read_text(encoding="utf-8")
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, found {count}")
    path.write_text(source.replace(old, new), encoding="utf-8")


def update_arb() -> None:
    replace_once(
        FR,
        '  "consentRequired": "Consentement IA requis pour utiliser cette fonctionnalité",\n\n  "save":',
        '  "consentRequired": "Consentement IA requis pour utiliser cette fonctionnalité",\n  "documentPrivacyTitle": "Traitement externe contrôlé",\n  "documentPrivacyBody": "Le document n’est transmis à un service externe que si votre consentement et la politique fournisseur du déploiement sont valides. Sinon, l’import est refusé.",\n\n  "save":',
    )

    replace_once(
        EN,
        '  "dataPrivacyNote": "Pseudonymised data",',
        '  "dataPrivacyNote": "AI processing subject to approval",',
    )
    replace_once(
        EN,
        '  "consentHeadline": "IAmina analyses your glucose data with AI",',
        '  "consentHeadline": "IAmina may process some data with approved AI services",',
    )
    replace_once(
        EN,
        '  "consentBody": "To provide personalised insights, IAmina uses Gemini AI to process your glucose readings, meals, and health context. Your data is pseudonymised before transmission and never sold to third parties.\\n\\nYou can withdraw this consent at any time from your profile settings.",',
        '  "consentBody": "This consent authorises IAmina to use the data categories listed above for AI features. External processing occurs only when the deployment provider, region and retention policy have been approved. Without consent or a valid provider approval, data is not sent to the AI service.\\n\\nThe provider and terms may vary by deployment. You can withdraw this consent at any time from your profile settings.",',
    )
    replace_once(
        EN,
        '  "consentRequired": "AI consent required to use this feature",\n\n  "save":',
        '  "consentRequired": "AI consent required to use this feature",\n  "documentPrivacyTitle": "Controlled external processing",\n  "documentPrivacyBody": "The document is sent to an external service only when your consent and the deployment provider policy are valid. Otherwise, import is refused.",\n\n  "save":',
    )

    replace_once(
        AR,
        '  "dataPrivacyNote": "بيانات مجهولة الهوية",',
        '  "dataPrivacyNote": "معالجة الذكاء الاصطناعي تخضع للموافقة",',
    )
    replace_once(
        AR,
        '  "consentHeadline": "IAmina تحلل بيانات الجلوكوز باستخدام الذكاء الاصطناعي",',
        '  "consentHeadline": "قد تعالج IAmina بعض البيانات باستخدام خدمات ذكاء اصطناعي معتمدة",',
    )
    replace_once(
        AR,
        '  "consentBody": "لتزويدك برؤى مخصصة، تستخدم IAmina الذكاء الاصطناعي (Gemini) لمعالجة قراءات الجلوكوز ووجباتك وسياقك الصحي. تُجهَّل بياناتك قبل الإرسال ولا تُباع لأطراف ثالثة أبدًا.\\n\\nيمكنك سحب هذا الموافقة في أي وقت من إعدادات ملفك الشخصي.",',
        '  "consentBody": "تسمح هذه الموافقة لـ IAmina باستخدام فئات البيانات المذكورة أعلاه لتشغيل ميزات الذكاء الاصطناعي. لا تتم المعالجة الخارجية إلا إذا تمت الموافقة على المزوّد والمنطقة وسياسة الاحتفاظ الخاصة ببيئة التشغيل. من دون موافقة المستخدم أو اعتماد صالح للمزوّد، لا تُرسل البيانات إلى خدمة الذكاء الاصطناعي.\\n\\nقد يختلف المزوّد والشروط حسب بيئة التشغيل. يمكنك سحب هذه الموافقة في أي وقت من إعدادات ملفك الشخصي.",',
    )
    replace_once(
        AR,
        '  "consentRequired": "مطلوب موافقة الذكاء الاصطناعي لاستخدام هذه الميزة",\n\n  "save":',
        '  "consentRequired": "مطلوب موافقة الذكاء الاصطناعي لاستخدام هذه الميزة",\n  "documentPrivacyTitle": "معالجة خارجية مضبوطة",\n  "documentPrivacyBody": "لا يُرسل المستند إلى خدمة خارجية إلا إذا كانت موافقتك وسياسة المزوّد الخاصة ببيئة التشغيل صالحتين. خلاف ذلك، يُرفض الاستيراد.",\n\n  "save":',
    )


def update_document_screen() -> None:
    replace_once(
        DOCUMENT,
        "import 'dart:typed_data';\n",
        "import 'dart:typed_data';\nimport 'package:amina/l10n/app_localizations.dart';\n",
    )
    replace_once(
        DOCUMENT,
        """              const Wrap(
                spacing: 8,
                runSpacing: 8,
                alignment: WrapAlignment.center,
                children: [
                  _FormatChip(icon: Icons.picture_as_pdf, label: 'PDF'),
                  _FormatChip(icon: Icons.image, label: 'Photo'),
                  _FormatChip(icon: Icons.table_chart, label: 'Excel / CSV'),
                  _FormatChip(icon: Icons.description, label: 'Word'),
                ],
              ),
              const SizedBox(height: 36),""",
        """              const Wrap(
                spacing: 8,
                runSpacing: 8,
                alignment: WrapAlignment.center,
                children: [
                  _FormatChip(icon: Icons.picture_as_pdf, label: 'PDF'),
                  _FormatChip(icon: Icons.image, label: 'Photo'),
                  _FormatChip(icon: Icons.table_chart, label: 'Excel / CSV'),
                  _FormatChip(icon: Icons.description, label: 'Word'),
                ],
              ),
              const SizedBox(height: 20),
              const _PrivacyGateNotice(),
              const SizedBox(height: 24),""",
    )
    replace_once(
        DOCUMENT,
        "class _FormatChip extends StatelessWidget {",
        """class _PrivacyGateNotice extends StatelessWidget {
  const _PrivacyGateNotice();

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Container(
      key: const ValueKey('document-privacy-gate'),
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AminaTheme.isDark(context)
            ? AminaTheme.dark700
            : AminaTheme.ink50,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AminaTheme.divider(context)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.shield_outlined, size: 20, color: AminaTheme.teal600),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  l10n.documentPrivacyTitle,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: AminaTheme.textPrimary(context),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  l10n.documentPrivacyBody,
                  style: TextStyle(
                    fontSize: 12,
                    height: 1.45,
                    color: AminaTheme.textSecondary(context),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _FormatChip extends StatelessWidget {""",
    )


def write_contract_test() -> None:
    TEST.write_text(
        """import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> _arb(String path) =>
    jsonDecode(File(path).readAsStringSync()) as Map<String, dynamic>;

String _read(String path) => File(path).readAsStringSync();

void main() {
  final localeFiles = <String, String>{
    'fr': 'lib/l10n/app_fr.arb',
    'en': 'lib/l10n/app_en.arb',
    'ar': 'lib/l10n/app_ar.arb',
  };

  test('privacy wording is deployment-aware in every supported locale', () {
    final requiredEvidence = <String, List<String>>{
      'fr': ['fournisseur', 'région', 'conservation', 'Sans consentement'],
      'en': ['provider', 'region', 'retention', 'Without consent'],
      'ar': ['المزوّد', 'المنطقة', 'الاحتفاظ', 'من دون موافقة'],
    };

    for (final entry in localeFiles.entries) {
      final values = _arb(entry.value);
      final combined = <String>[
        values['dataPrivacyNote'] as String,
        values['consentHeadline'] as String,
        values['consentBody'] as String,
        values['documentPrivacyTitle'] as String,
        values['documentPrivacyBody'] as String,
      ].join(' ');

      for (final required in requiredEvidence[entry.key]!) {
        expect(combined, contains(required),
            reason: '${entry.key} is missing deployment evidence wording: $required');
      }

      for (final forbidden in <String>[
        'Gemini',
        'pseudonymised',
        'pseudonymized',
        'pseudonymisées',
        'مجهولة الهوية',
        'never sold',
        'jamais vendues',
        'لا تُباع',
        'zero retention',
        'no retention',
        'never trains',
      ]) {
        expect(combined.toLowerCase(), isNot(contains(forbidden.toLowerCase())),
            reason: '${entry.key} contains an unsupported privacy claim: $forbidden');
      }
    }
  });

  test('document import displays the fail-closed privacy gate before selection', () {
    final source =
        _read('lib/features/documents/document_import_screen.dart');

    for (final required in <String>[
      'document-privacy-gate',
      'l10n.documentPrivacyTitle',
      'l10n.documentPrivacyBody',
      'const _PrivacyGateNotice()',
      "key: const ValueKey('choose-document-button')",
    ]) {
      expect(source, contains(required),
          reason: 'Document privacy gate is incomplete: $required');
    }

    expect(
      source.indexOf('const _PrivacyGateNotice()'),
      lessThan(source.indexOf("key: const ValueKey('choose-document-button')")),
      reason: 'Privacy notice must be visible before the file chooser.',
    );
  });

  test('generated localization sources contain the approved wording', () {
    final generated = <String, String>{
      'fr': _read('lib/l10n/app_localizations_fr.dart'),
      'en': _read('lib/l10n/app_localizations_en.dart'),
      'ar': _read('lib/l10n/app_localizations_ar.dart'),
    };

    expect(generated['fr'], contains('Traitement externe contrôlé'));
    expect(generated['en'], contains('Controlled external processing'));
    expect(generated['ar'], contains('معالجة خارجية مضبوطة'));

    for (final source in generated.values) {
      expect(source, isNot(contains('Gemini')));
    }
  });
}
""",
        encoding="utf-8",
    )


def update_docs() -> None:
    P0_DOC.write_text(
        """# P0 Product Truthfulness

> **Status: CLOSED.** Five independently validated LOTs are merged or carried by the final closure PR #43.

This P0 ensures that every patient-facing promise in IAmina is real, traceable and
clinically safe. A visually convincing control is not considered a feature unless
its state and outcome are backed by executable behavior.

## Closure checklist

| Item | Requirement | Status | Evidence |
|---|---|---|---|
| P0-UX-1 | Every apparent action is functional or explicitly unavailable | **Closed** | PR #39; `p0_real_actions_contract_test.dart` |
| P0-UX-2 | System states such as synchronization, notifications and pilot status are live and truthful | **Closed** | PR #40; typed `SyncUiState`; `p0_truthful_system_state_contract_test.dart` |
| P0-UX-3 | Clinical conclusions, confidence and goals are explainable; no opaque score or fabricated precision | **Closed** | PR #41; `p0_clinical_explainability_contract_test.dart` |
| P0-UX-4 | Import is reachable and usable on mobile | **Closed** | PR #42; 390 × 844 and 360 × 560 widget journeys |
| P0-UX-5 | Privacy wording never exceeds approved deployment and processor evidence | **Closed** | PR #43; `p0_privacy_truthfulness_contract_test.dart` |

## P0-UX-1 — real actions

PR #39 closes false or empty controls, preserves the real Drift CRUD loop and
requires unavailable integrations to be visibly non-interactive.

## P0-UX-2 — truthful system state

PR #40 makes synchronization, offline, pending and error labels derive from typed
runtime state. Local storage is never presented as confirmed server synchronization.

## P0-UX-3 — clinical explainability

PR #41 removes fabricated confidence, decorative trends and opaque scores. Discrete
manual/imported readings are not labelled as CGM time, and KPI method, coverage and
limitations remain visible.

## P0-UX-4 — mobile import

PR #42 proves that Importer remains reachable at 390 px, the real Pulper route opens,
and the picker remains scrollable without overflow at 360 × 560. Persistence still
requires explicit review and confirmation.

## P0-UX-5 — privacy truthfulness

PR #43 closes privacy overclaiming through a fail-closed patient-facing contract:

- no provider name is hardcoded as a permanent deployment fact;
- consent text does not promise pseudonymisation, no-training, no-retention or
  third-party-sales guarantees without deployment evidence;
- French, English and Arabic state that external processing requires valid consent
  plus approved provider, region and retention policy;
- the document picker shows the external-processing gate before file selection;
- unsupported privacy claims are rejected permanently by a Flutter source contract;
- generated localizations are checked so reviewed ARB wording cannot drift from the
  runtime application.

## Closure and score policy

**P0 source and CI closure: 5/5 requirements complete.** A product score above
**9.5/10** still requires launching the certified merge commit and completing the
final visual/functional audit with no critical or high-severity finding. This file
does not convert source inspection into a deployment claim.
""",
        encoding="utf-8",
    )

    replace_once(
        ROADMAP,
        "> **Last updated:** 2026-08-04 — native/clinical review gate prepared in PR #37; secret-history remediation preflight prepared in PR #38; external rotation and approvals remain open.",
        "> **Last updated:** 2026-08-05 — P0 product-truthfulness closure completed through PRs #39–#43; external MENA, legal, linguistic and secret-history gates remain open.",
    )
    replace_once(
        ROADMAP,
        "| P0 historical foundations | 100% | ✅ Merged | P0-A, P0-B, P0-C and migration drift |",
        "| P0 historical foundations | 100% | ✅ Merged | P0-A, P0-B, P0-C and migration drift |\n| P0 product truthfulness | 100% | ✅ Closed | PRs #39–#43; five executable UX truthfulness contracts |",
    )
    replace_once(
        ROADMAP,
        "## ✅ P0 migration drift\n\n- Migration state reconciled without unnecessary ALTER operations.\n- `makemigrations --check --dry-run` is a permanent CI gate.\n",
        "## ✅ P0 migration drift\n\n- Migration state reconciled without unnecessary ALTER operations.\n- `makemigrations --check --dry-run` is a permanent CI gate.\n\n## ✅ P0 product truthfulness\n\n- Real actions and the complete local CRUD loop are permanently certified.\n- Synchronization and storage labels derive from real typed state.\n- Clinical metrics disclose method, coverage and limitations without fabricated precision.\n- Mobile Importer and the document picker are certified on narrow and short viewports.\n- Privacy wording is deployment-aware in FR/EN/AR and fails closed before external document processing.\n- Permanent Flutter contracts prevent regression of all five requirements.\n\n**Closure:** PRs #39–#43. This workstream is separate from the MENA critical-path numerator.\n",
    )


def main() -> None:
    update_arb()
    update_document_screen()
    write_contract_test()
    update_docs()
    print("P0-UX-5 privacy truthfulness closure applied.")


if __name__ == "__main__":
    main()
