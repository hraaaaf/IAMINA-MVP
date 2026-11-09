#!/usr/bin/env python3
"""D22 F05: real local Flutter ReportsScreen fail-closed Chrome proof.

Legacy bounds 70/180 remain deliberately unapproved, no patient data/API.
This is NOT PDF/CSV export, verified CGM sensor or clinical release evidence.
"""
import hashlib
import http.server
import json
import pathlib
import socketserver
import struct
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEB = ROOT / "frontend" / "build" / "web"
OUT = ROOT / "d22-f05-web-proof"
VIEWS = ((390, 844), (1280, 900))
LANGS = {
    "fr": dict(title="Rapport de vos mesures", target="Objectifs non vérifiés",
               descriptive="Ce rapport reste descriptif",
               forbidden="Mesures dans la cible"),
    "ar": dict(title="تقرير قياساتك", target="الأهداف غير مؤكدة",
               descriptive="هذا التقرير وصفي فقط",
               forbidden="قياسات ضمن النطاق"),
}


class Server(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def log_message(self, *args):
        pass


class TCP(socketserver.TCPServer):
    allow_reuse_address = True


def run():
    assert (WEB / "main.dart.js").is_file(), "F05 actual Web build not found"
    OUT.mkdir(exist_ok=True)
    proof = {
        "result": "NOT_RUN", "decision": "D22 F05",
        "scope": "local real Flutter ReportsScreen + Drift Web/IndexedDB",
        "checks": [], "captures": [],
        "not_run": [
            "PDF/CSV exports and backend producer data parity",
            "clinical target G1/G2/G5 authority",
            "real CGM sensor provenance, TIR, GMI and AGP",
            "hosted API/auth, physician signoff, prod deployment",
        ],
    }
    failures = []
    blocked = []
    try:
        with TCP(("127.0.0.1", 0), Server) as server:
            threading.Thread(target=server.serve_forever, daemon=True).start()
            origin = f"http://localhost:{server.server_address[1]}"
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                try:
                    for language, copy in LANGS.items():
                        for width, height in VIEWS:
                            context = browser.new_context(
                                viewport={"width": width, "height": height},
                                locale="fr-FR" if language == "fr" else "ar-MA",
                                service_workers="block", accept_downloads=False,
                            )
                            try:
                                page = context.new_page()
                                page.on("pageerror", lambda error: failures.append(str(error)[:250]))

                                def local_only(route):
                                    url = route.request.url
                                    if url.startswith(origin + "/") or url.startswith(("blob:", "data:")):
                                        route.continue_()
                                    else:
                                        blocked.append(url.split("?", 1)[0])
                                        route.abort()

                                page.route("**/*", local_only)
                                response = page.goto(f"{origin}/?lang={language}",
                                                     wait_until="domcontentloaded",
                                                     timeout=60000)
                                assert response and response.status == 200
                                page.wait_for_selector("flutter-view, flt-glass-pane", timeout=60000)
                                placeholder = page.locator("flt-semantics-placeholder")
                                if placeholder.count():
                                    placeholder.first.evaluate("(el) => el.click()")
                                page.get_by_text(copy["title"], exact=True).first.wait_for(
                                    state="visible", timeout=30000)
                                page.get_by_text(copy["target"], exact=True).first.wait_for(
                                    state="visible", timeout=30000)
                                page.get_by_text(copy["descriptive"], exact=True).first.wait_for(
                                    state="visible", timeout=30000)
                                assert page.get_by_text(copy["forbidden"], exact=True).count() == 0, (
                                    f"F05 a legacy target incorrectly classified measurements: {language}"
                                )
                                assert page.get_by_text("AGP", exact=True).count() == 0
                                assert page.get_by_text("TIR", exact=True).count() == 0
                                target = page.get_by_text(copy["target"], exact=True).first
                                target.scroll_into_view_if_needed(timeout=20000)
                                target.wait_for(state="visible", timeout=15000)
                                out = OUT / f"f05-failclosed-{language}-{width}x{height}.png"
                                page.screenshot(path=str(out), animations="disabled", full_page=False)
                                image = out.read_bytes()
                                assert struct.unpack(">II", image[16:24]) == (width, height)
                                geometry = page.evaluate("""() => ({
                                  width: window.innerWidth,
                                  rootScrollWidth: document.documentElement.scrollWidth,
                                  flutterWidth: Math.round(document.querySelector('flutter-view')
                                   ?.getBoundingClientRect().width || 0)
                                })""")
                                assert geometry["width"] == width
                                assert geometry["flutterWidth"] == width
                                assert geometry["rootScrollWidth"] <= width
                                proof["checks"].append({
                                    "locale": language, "viewport": f"{width}x{height}",
                                    "target_legacy_unapproved": [70, 180],
                                    "has_classification": False,
                                    "target_status": "unverified",
                                    "report_only": True, "result": "PASS",
                                    "geometry": geometry,
                                })
                                proof["captures"].append({
                                    "file": out.name, "viewport": f"{width}x{height}",
                                    "sha256": hashlib.sha256(image).hexdigest(),
                                })
                            finally:
                                context.close()
                finally:
                    browser.close()
        assert not failures, f"Flutter browser errors: {failures[:3]}"
        # CanvasKit may request its optional Noto Sans Symbols glyph font
        # even with --no-web-resources-cdn. All external requests were
        # already ABORTED by local_only: do not allow network egress here.
        # Fail for ANY unexpected external request; keep the denied
        # Noto font URL count as a diagnostic, not clinical proof.
        optional_font_prefixes = (
            "https://fonts.gstatic.com/s/notosanssymbols/",
            "https://fonts.gstatic.com/s/notosansarabic/",
        )
        # These optional Flutter glyph requests were denied by route.abort().
        # Whitelist only their exact font URL patterns in the audit log,
        # NEVER the requests themselves. Any other external URL fails.
        unexpected = [
            url for url in blocked
            if not (url.startswith(optional_font_prefixes)
                    and url.endswith(".woff2"))
        ]
        assert not unexpected, f"Unexpected external request (blocked): {unexpected[:3]}"
        proof["external_requests_denied"] = len(blocked)
        proof["optional_noto_font_requests_denied"] = (
            len(blocked) - len(unexpected)
        )
        proof["network_egress_permitted"] = False
        assert len(proof["checks"]) == 4
        proof["result"] = "PASS_BOUNDED_REAL_CHROME"
    finally:
        (OUT / "proof.json").write_text(
            json.dumps(proof, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


if __name__ == "__main__":
    run()
