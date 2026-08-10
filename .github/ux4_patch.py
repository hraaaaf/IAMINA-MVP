from pathlib import Path
import re

path = Path('frontend/lib/features/journal/ai_summary_screen.dart')
source = path.read_text()
replacement = r'''  Widget _buildError() {
    final l10n = AppLocalizations.of(context)!;
    return LayoutBuilder(
      builder: (context, constraints) {
        final isWide = constraints.maxWidth >= 720;
        final periodLabel = '$_periodDays ${l10n.dayShort}';
        final icon = Container(
          width: isWide ? 58 : 50,
          height: isWide ? 58 : 50,
          decoration: BoxDecoration(
            color: AminaTheme.dangerBg,
            borderRadius: BorderRadius.circular(AminaTheme.radiusXL),
          ),
          child: Icon(
            Icons.cloud_off_outlined,
            color: AminaTheme.dangerFg,
            size: isWide ? 28 : 24,
          ),
        );
        final periodChip = Container(
          padding: const EdgeInsetsDirectional.fromSTEB(10, 6, 10, 6),
          decoration: BoxDecoration(
            color: AminaTheme.bg(context),
            borderRadius: BorderRadius.circular(999),
            border: Border.all(color: AminaTheme.divider(context)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                Icons.calendar_today_outlined,
                size: 13,
                color: AminaTheme.textSecondary(context),
              ),
              const SizedBox(width: 6),
              Text(
                periodLabel,
                style: TextStyle(
                  color: AminaTheme.textSecondary(context),
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        );
        final retry = FilledButton.icon(
          onPressed: _fetchData,
          icon: const Icon(Icons.refresh, size: 17),
          label: Text(l10n.retry),
          style: FilledButton.styleFrom(
            minimumSize: const Size.fromHeight(48),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AminaTheme.radiusXL),
            ),
          ),
        );
        final copy = Column(
          crossAxisAlignment: isWide
              ? CrossAxisAlignment.start
              : CrossAxisAlignment.center,
          children: [
            Text(
              l10n.navIamina,
              textAlign: isWide ? TextAlign.start : TextAlign.center,
              style: TextStyle(
                fontSize: 12,
                height: 1.2,
                fontWeight: FontWeight.w800,
                letterSpacing: 0.18,
                color: AminaTheme.textSecondary(context),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              l10n.analysisLoadError,
              textAlign: isWide ? TextAlign.start : TextAlign.center,
              style: TextStyle(
                fontSize: isWide ? 20 : 16,
                height: 1.35,
                fontWeight: FontWeight.w800,
                color: AminaTheme.textPrimary(context),
              ),
            ),
            const SizedBox(height: 14),
            periodChip,
          ],
        );

        return SingleChildScrollView(
          padding: EdgeInsetsDirectional.fromSTEB(
            isWide ? 28 : 20,
            isWide ? 22 : 28,
            isWide ? 28 : 20,
            28,
          ),
          child: Align(
            alignment: AlignmentDirectional.topStart,
            child: ConstrainedBox(
              constraints: BoxConstraints(maxWidth: isWide ? 960 : 520),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (isWide) ...[
                    _GreetingHeader(periodDays: _periodDays),
                    const SizedBox(height: 18),
                  ],
                  Semantics(
                    container: true,
                    liveRegion: true,
                    label: l10n.analysisLoadError,
                    child: Container(
                      width: double.infinity,
                      padding: EdgeInsets.all(isWide ? 28 : 24),
                      decoration: BoxDecoration(
                        color: AminaTheme.surface(context),
                        borderRadius: BorderRadius.circular(AminaTheme.radius2XL),
                        border: Border.all(color: AminaTheme.divider(context)),
                        boxShadow: AminaTheme.shadowClinical,
                      ),
                      child: isWide
                          ? Row(
                              crossAxisAlignment: CrossAxisAlignment.center,
                              children: [
                                icon,
                                const SizedBox(width: 20),
                                Expanded(child: copy),
                                const SizedBox(width: 28),
                                SizedBox(width: 190, child: retry),
                              ],
                            )
                          : Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                icon,
                                const SizedBox(height: 16),
                                copy,
                                const SizedBox(height: 20),
                                SizedBox(width: double.infinity, child: retry),
                              ],
                            ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildContent() {'''
pattern = re.compile(r"  Widget _buildError\(\) \{.*?\n  Widget _buildContent\(\) \{", re.S)
updated, count = pattern.subn(replacement, source, count=1)
if count != 1:
    raise SystemExit(f'Expected one _buildError block, replaced {count}')
path.write_text(updated)

test = Path('frontend/test/ux_4_summary_degraded_contract_test.dart')
test.write_text(r'''import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('UX-4 keeps degraded Summary integrated into the page shell', () {
    final source = File(
      'lib/features/journal/ai_summary_screen.dart',
    ).readAsStringSync();

    expect(source, contains('constraints: BoxConstraints(maxWidth: isWide ? 960 : 520)'));
    expect(source, contains('_GreetingHeader(periodDays: _periodDays)'));
    expect(source, contains('AlignmentDirectional.topStart'));
    expect(source, contains('liveRegion: true'));
    expect(source, contains('l10n.analysisLoadError'));
    expect(source, contains('label: Text(l10n.retry)'));
    expect(source, contains("final periodLabel = '\$_periodDays \${l10n.dayShort}';"));
    expect(source, isNot(contains('const Alignment(0, -0.30)')));
    expect(source, isNot(contains('maxWidth: isWide ? 480 : 420')));
  });
}
''')
