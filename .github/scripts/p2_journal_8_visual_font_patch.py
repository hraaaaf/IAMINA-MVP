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
path.write_text(text.replace(old, new, 1))
