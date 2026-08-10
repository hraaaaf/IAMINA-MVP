from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
old = '''  final loader = FontLoader(_auditFontFamily);
  loader.addFont(Future<ByteData>.value(ByteData.sublistView(bytes)));
  await loader.load();
'''
new = '''  for (final family in <String>[_auditFontFamily, 'Roboto', 'Ahem']) {
    final loader = FontLoader(family);
    loader.addFont(Future<ByteData>.value(ByteData.sublistView(bytes)));
    await loader.load();
  }
'''
if text.count(old) != 1:
    raise SystemExit('font loader anchor mismatch')
text = text.replace(old, new, 1)
text = text.replace(
    'find.byType(TextButton)',
    "find.byKey(const Key('personal-response-disclosure'))",
)
old_layout = '''        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsetsDirectional.fromSTEB(20, 24, 20, 24),
            child: PersonalResponseSection(
              unit: 'mg/dL',
              loader: () async => result,
            ),
          ),
        ),
'''
new_layout = '''        child: LayoutBuilder(
          builder: (context, constraints) {
            final width = constraints.maxWidth;
            final horizontalPadding = width >= 1100
                ? (width - 980) / 2
                : width >= 700
                    ? 28.0
                    : 20.0;
            return SingleChildScrollView(
              child: Padding(
                padding: EdgeInsetsDirectional.fromSTEB(
                  horizontalPadding,
                  24,
                  horizontalPadding,
                  24,
                ),
                child: PersonalResponseSection(
                  unit: 'mg/dL',
                  loader: () async => result,
                ),
              ),
            );
          },
        ),
'''
if text.count(old_layout) != 1:
    raise SystemExit('responsive host anchor mismatch')
text = text.replace(old_layout, new_layout, 1)
path.write_text(text)
