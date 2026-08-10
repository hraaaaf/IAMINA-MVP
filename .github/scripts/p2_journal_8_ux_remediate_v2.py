from pathlib import Path

script = Path(__file__).with_name("p2_journal_8_ux_remediate.py")
source = script.read_text()
source = source.replace(
    'anchor = "  testWidgets(\'AR ready state keeps RTL hierarchy without overflow\', (tester) async {"',
    'anchor = "  testWidgets(\'AR ready state keeps RTL hierarchy without overflow\', ("',
)
if "(tester) async" in source.split("new_test =", 1)[0].split("anchor =", 1)[1].split("\n", 1)[0]:
    raise SystemExit("formatted anchor shim was not applied")
exec(compile(source, str(script), "exec"), {"__name__": "__main__", "__file__": str(script)})
