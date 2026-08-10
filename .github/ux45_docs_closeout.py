from pathlib import Path

path = Path('docs/ROADMAP.md')
text = path.read_text()

old_header = "> **Last updated:** 2026-08-10 — UX visual rebase remains closed: UX-3 unified the wide-shell brand from a cross-product 8.7/10 inconsistency to a canonical IAmina signature at 9.4/10 with exact-head and post-merge certification."
new_header = "> **Last updated:** 2026-08-10 — UX visual rebase remains closed through UX-5: UX-4 restored Summary degraded-state continuity to 9.3/10; UX-5 added the certified floating glass mobile navigation at 9.4/10, with exact-head and post-merge gates green."
if old_header not in text:
    raise SystemExit('Expected ROADMAP header not found')
text = text.replace(old_header, new_header, 1)

old_row = "| UX visual rebase | 100% | ✅ Closed | UX-0/1/2 remain closed; UX-3 PR #89 unified the desktop shell brand **8.7/10 → 9.4/10**; post-merge CI #1472 + drift #1284 green |"
new_row = "| UX visual rebase | 100% | ✅ Closed | UX-0/1/2/3 remain closed; UX-4 PR #91 restored Summary degraded-state continuity to **9.3/10** (merge `57f2a672`); UX-5 PR #92 added the floating glass mobile nav at **9.4/10** (merge `76daf3ad`); post-merge CI #1492 + drift #1304 green |"
if old_row not in text:
    raise SystemExit('Expected UX visual rebase dashboard row not found')
text = text.replace(old_row, new_row, 1)

marker = "The Journal redesign and UX visual rebase are separate product-quality workstreams and do not change the MENA critical-path numerator."
addition = marker + "\n\n**UX-4/UX-5 closeout:** PR #91 fixed only the Summary degraded/error composition without fabricating patient metrics or insights. PR #92 replaced the stock mobile navigation presentation with a route-preserving glass rail, 240 ms selected-state glide, haptic feedback, dark-mode support, >=48 px targets and certified FR/AR RTL behavior. UX-5 final rendered evidence: run `31436069213`, artifact `9081084594`, digest `sha256:337e4a4ccac714418de269abc69104eebfc086cd6665c24df7aaa0a29c2372a9`, 8/8 real 390×844/360×560 FR/AR Dashboard/Journal captures, one Flutter view and zero page errors."
if marker not in text:
    raise SystemExit('Expected MENA numerator note not found')
text = text.replace(marker, addition, 1)

path.write_text(text)
