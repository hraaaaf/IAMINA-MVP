from pathlib import Path
import sys

root = Path(sys.argv[1])
path = root / 'docs/ROADMAP.md'
text = path.read_text()
old = "6. In the product-quality lane, complete P1-JOURNAL-7 exact-final-head certification and expected-head merge/post-merge verification, then execute P2-JOURNAL-8 as the next Journal LOT without changing the MENA critical-path numerator."
new = "6. **Journal product-quality lane is closed.** Do not reopen it without a new evidence-backed roadmap decision; after blockers 1–5 are cleared, move to the real-patient pilot go/no-go and cohort execution gates."
if text.count(old) != 1:
    raise SystemExit('stale Journal blocker anchor mismatch')
path.write_text(text.replace(old, new, 1))
