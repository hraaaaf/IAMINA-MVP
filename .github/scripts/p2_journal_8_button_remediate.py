from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1]).resolve()
expected = "1b8fcdac441a2bb2f000e198eecdb444047420ae"
head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
if head != expected:
    raise SystemExit(f"stale product head: {head}")

path = root / "frontend/lib/features/journal/widgets/personal_response_section.dart"
text = path.read_text()
old = '''                if (snapshot.data!.patterns.length > 1)
                  Align(
                    alignment: AlignmentDirectional.centerStart,
                    child: TextButton.icon(
                      onPressed: () {
                        setState(() => _showAllPatterns = !_showAllPatterns);
                      },
                      icon: Icon(
                        _showAllPatterns
                            ? Icons.expand_less
                            : Icons.expand_more,
                        size: 18,
                      ),
                      label: Text(
                        _showAllPatterns
                            ? l10n.personalResponseShowLess
                            : l10n.personalResponseShowMore(
                                snapshot.data!.patterns.length - 1,
                              ),
                      ),
                      style: TextButton.styleFrom(
                        foregroundColor: AminaTheme.primaryTeal,
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 6,
                        ),
                        textStyle: const TextStyle(
                          fontSize: 11.5,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ),
'''
new = '''                if (snapshot.data!.patterns.length > 1)
                  Align(
                    alignment: AlignmentDirectional.centerStart,
                    child: Semantics(
                      button: true,
                      child: InkWell(
                        key: const Key('personal-response-disclosure'),
                        onTap: () {
                          setState(() => _showAllPatterns = !_showAllPatterns);
                        },
                        borderRadius: BorderRadius.circular(10),
                        child: Padding(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 8,
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                _showAllPatterns
                                    ? Icons.expand_less
                                    : Icons.expand_more,
                                size: 18,
                                color: AminaTheme.primaryTeal,
                              ),
                              const SizedBox(width: 6),
                              Flexible(
                                child: Text(
                                  _showAllPatterns
                                      ? l10n.personalResponseShowLess
                                      : l10n.personalResponseShowMore(
                                          snapshot.data!.patterns.length - 1,
                                        ),
                                  style: const TextStyle(
                                    fontSize: 11.5,
                                    height: 1.25,
                                    fontWeight: FontWeight.w700,
                                    color: AminaTheme.primaryTeal,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
'''
if text.count(old) != 1:
    raise SystemExit(f"disclosure block mismatch: {text.count(old)}")
path.write_text(text.replace(old, new, 1))
