"""Real Chromium integration tests against an isolated local Kiwadoi server.

Run from the repository root: python -m unittest discover -s browser_tests -v
No production requests, credentials or respondent records are used.
"""
import io
import json
import os
from pathlib import Path
import threading
import unittest
from http.server import ThreadingHTTPServer

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright, expect

from marketer_app import Handler


ARTIFACTS = Path(os.environ.get("BROWSER_TEST_ARTIFACTS", "browser-test-artifacts"))
AD_COPY = "We know where you live."


class BrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.addClassCleanup(server.server_close)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        cls.addClassCleanup(thread.join, 5)
        cls.addClassCleanup(server.shutdown)
        cls.base = f"http://127.0.0.1:{server.server_port}"
        cls.pw = sync_playwright().start()
        cls.addClassCleanup(cls.pw.stop)
        cls.browser = cls.pw.chromium.launch()
        cls.addClassCleanup(cls.browser.close)

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1440, "height": 900})
        self.addCleanup(self.context.close)
        self.page = self.context.new_page()
        self.page.set_default_timeout(15000)
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.addCleanup(self.record_artifacts)

    def record_artifacts(self):
        # Record every case, including failed assertions; fixture inputs are fictional.
        if not self.page.is_closed():
            self.page.screenshot(path=str(ARTIFACTS / (self._testMethodName + ".png")),
                                 full_page=True, timeout=10000)
        (ARTIFACTS / (self._testMethodName + ".json")).write_text(
            json.dumps({"page_errors": self.errors, "url": self.page.url}, indent=2),
            encoding="utf-8")
        self.assertEqual(self.errors, [], "Uncaught browser JavaScript errors")

    def open_page(self, path="/"):
        response = self.page.goto(self.base + path, wait_until="domcontentloaded")
        self.assertIsNotNone(response)
        self.assertEqual(response.status, 200)

    def assert_abstention(self, data):
        self.assertEqual(data["threshold_decision"]["status"], "insufficient_evidence")
        self.assertIsNone(data["threshold_decision"]["recommended_level"])
        expect(self.page.locator("#empirical-decision-title")).to_be_visible()
        expect(self.page.locator("#empirical-decision-title")).to_contain_text("abstain")

    def analyze(self, selector="#analyze-btn"):
        with self.page.expect_response(
            lambda r: r.url.endswith("/api/analyze") and r.request.method == "POST",
            timeout=120000
        ) as pending:
            self.page.locator(selector).click()
        response = pending.value
        self.assertEqual(response.status, 200, response.text())
        expect(self.page.locator("#result-content")).to_be_visible(timeout=15000)
        expect(self.page.locator("#analyze-btn")).to_be_enabled()
        return response.json()

    def test_navigation_and_research(self):
        self.open_page()
        expect(self.page.locator("h1")).to_contain_text("privacy and pressure cues")
        expect(self.page.get_by_role("link", name="Source code")).to_have_attribute(
            "href", "https://github.com/harisankar-work/personalised-threshold")
        self.page.locator(".header-nav a[href='/simulation']").click()
        expect(self.page.locator("h1")).to_contain_text("fictional")
        expect(self.page.locator("#sim-levels tr")).to_have_count(5)
        self.page.locator(".header-nav a[href='/research']").click()
        expect(self.page.locator("#dashboard-content")).to_be_visible()
        expect(self.page.locator("#dashboard-error")).to_be_hidden()
        expect(self.page.locator("#threshold-value")).to_have_text("insufficient_evidence")
        expect(self.page.locator("#survey-v2")).not_to_have_text("—")
        expect(self.page.locator("#interval-high")).not_to_have_text("—")
        self.page.locator(".header-nav a[href='/']").click()
        expect(self.page.locator("#ad-form")).to_be_visible()

    def test_generic_and_intrusive_samples(self):
        self.open_page()
        generic = self.analyze('[data-sample="safe"]')
        self.assert_abstention(generic)
        expect(self.page.locator("#tier-pill")).to_have_text("Low rubric score")
        intrusive = self.analyze('[data-sample="creepy"]')
        self.assert_abstention(intrusive)
        self.assertGreater(intrusive["privacy_score"], generic["privacy_score"])
        expect(self.page.locator("#evidence-list .evidence-item").first).to_be_visible()
        self.assertTrue(self.page.evaluate("""() =>
            Boolean(document.querySelector('#empirical-decision-title')
                .compareDocumentPosition(document.querySelector('#score-number')) &
                Node.DOCUMENT_POSITION_FOLLOWING)"""))

    def test_text_validation_and_stale_results(self):
        self.open_page()
        self.page.locator("#analyze-btn").click()
        expect(self.page.locator("#form-error")).to_contain_text("Paste ad copy")
        self.page.locator("#ad-text").fill(AD_COPY)
        data = self.analyze()
        self.assert_abstention(data)
        self.assertGreater(data["privacy_score"], 0)
        self.page.locator("#ad-text").fill("Discover our new collection.")
        expect(self.page.locator("#result-content")).to_be_hidden()
        expect(self.page.locator("#result-empty")).to_be_visible()

    def test_permission_hold_and_financial_scenario(self):
        self.open_page()
        data = self.analyze('[data-sample="creepy"]')
        self.assertEqual(data["strategy"]["action"], "hold_for_review")
        expect(self.page.locator("#strategy-action")).to_contain_text("Hold for review")
        expect(self.page.locator("#compatibility-summary")).to_contain_text("permission")
        self.page.locator("#campaign-details > summary").click()
        self.page.locator("#central-conversions").fill("20")
        data = self.analyze()
        self.assert_abstention(data)
        self.assertEqual(data["strategy"]["available_budget_headroom"], 20000)
        expect(self.page.locator("#strategy-budget")).to_contain_text("20,000")
        expect(self.page.locator("#scenario-result")).to_be_visible()
        expect(self.page.locator("#scenario-label")).to_contain_text("hypothetical")
        expect(self.page.locator("#scenario-values")).to_contain_text("20 extra conversions")

    def test_real_local_ocr_and_manual_correction(self):
        self.open_page()
        self.page.locator("#image-tab").click()
        expect(self.page.locator("#image-limit")).to_have_text("10")
        image = Image.new("RGB", (1000, 220), "white")
        ImageDraw.Draw(image).text((35, 55), AD_COPY, fill="black",
                                  font=ImageFont.load_default(size=64))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        self.page.locator("#image-file").set_input_files(
            {"name": "fictional-ad.png", "mimeType": "image/png", "buffer": buffer.getvalue()})
        expect(self.page.locator("#image-preview")).to_be_visible()
        data = self.analyze()
        self.assert_abstention(data)
        self.assertIn("where you live", data["ocr_text"].lower())
        self.assertGreater(data["privacy_score"], 0)
        self.page.locator("#ocr-details > summary").click()
        self.page.locator("#corrected-ocr").fill("Discover our new collection.")
        corrected = self.analyze("#reanalyze-ocr")
        self.assertEqual(corrected["corrected_ocr_text"], "Discover our new collection.")
        self.assertEqual(corrected["ocr_text"], data["ocr_text"])
        self.assertEqual(corrected["privacy_score"], 0)
        self.assert_abstention(corrected)
        expect(self.page.locator("#ocr-correction-status")).to_contain_text("Original OCR is preserved")

    def test_invalid_upload_and_local_size_limit(self):
        self.open_page()
        self.page.locator("#image-tab").click()
        expect(self.page.locator("#image-limit")).to_have_text("10")
        field = self.page.locator("#image-file")
        field.set_input_files({"name": "invalid.txt", "mimeType": "text/plain", "buffer": b"test"})
        expect(self.page.locator("#form-error")).to_contain_text("Choose a PNG")
        field.set_input_files({"name": "oversized.png", "mimeType": "image/png",
                               "buffer": b"x" * (10 * 1024 * 1024 + 1)})
        expect(self.page.locator("#form-error")).to_contain_text("up to 10 MB")
        expect(self.page.locator("#image-preview")).to_be_hidden()

    def test_simulation_permission_and_input_change(self):
        self.open_page("/simulation")
        expect(self.page.locator("#sim-levels tr")).to_have_count(5)
        expect(self.page.locator("#real-decision-title")).to_contain_text("abstain")
        expect(self.page.locator("#sim-recommendation")).to_contain_text("synthetic scenario", ignore_case=True)
        # Unknown data permissions must prevent all personalized levels from being eligible.
        for index in range(1, 5):
            expect(self.page.locator("#sim-levels tr").nth(index)).to_contain_text("Review required")
        self.page.locator("#trait0").fill("6")
        expect(self.page.locator("#sim-levels tr")).to_have_count(0)
        with self.page.expect_response(lambda r: r.url.endswith("/api/simulation")
                                       and r.request.method == "POST") as pending:
            self.page.locator("#compare").click()
        response = pending.value
        self.assertEqual(response.status, 200)
        self.assertEqual(response.json()["real_threshold_status"], "insufficient_evidence")
        expect(self.page.locator("#sim-levels tr")).to_have_count(5)

    def test_mobile_layout(self):
        self.page.set_viewport_size({"width": 390, "height": 844})
        for route in ("/", "/simulation", "/research"):
            with self.subTest(route=route):
                self.open_page(route)
                if route == "/simulation":
                    expect(self.page.locator("#sim-levels tr")).to_have_count(5)
                elif route == "/research":
                    expect(self.page.locator("#dashboard-content")).to_be_visible()
                else:
                    self.assert_abstention(self.analyze('[data-sample="safe"]'))
                dimensions = self.page.evaluate("""() => ({
                    viewport: document.documentElement.clientWidth,
                    content: document.documentElement.scrollWidth
                })""")
                self.assertLessEqual(dimensions["content"], dimensions["viewport"] + 2,
                                     f"Horizontal page overflow: {route}")
                self.page.screenshot(path=str(ARTIFACTS / ("mobile-" + (route.strip("/") or "planner") + ".png")),
                                     full_page=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
