"""Guard against misleading evidence claims in static public pages."""
from pathlib import Path
import unittest

WEB = Path(__file__).resolve().parent / "web"


class EvidencePresentationTests(unittest.TestCase):
    def test_campaign_abstention_precedes_rubric(self):
        page = (WEB / "index.html").read_text(encoding="utf-8")
        self.assertIn("Academic research prototype", page)
        self.assertEqual(page.count('id="threshold-status"'), 1)
        self.assertLess(page.index('id="empirical-decision-title"'), page.index('id="score-number"'))
        self.assertNotIn("Safe brand copy", page)
        self.assertIn("not a probability of discomfort", page)

    def test_simulation_is_explicitly_fictional(self):
        page = (WEB / "simulation.html").read_text(encoding="utf-8")
        script = (WEB / "simulation.js").read_text(encoding="utf-8")
        self.assertIn("Synthetic simulation", page)
        self.assertIn("No real consumer-level recommendation is supported", page)
        self.assertIn("Synthetic scenario choice", script)
        self.assertIn("Scenario eligible", script)

    def test_all_pages_have_reproducibility_links(self):
        for name in ("index.html", "simulation.html", "research.html"):
            with self.subTest(page=name):
                page = (WEB / name).read_text(encoding="utf-8")
                self.assertIn("Academic research prototype", page)
                self.assertIn("https://github.com/harisankar-work/personalised-threshold", page)
                self.assertIn("README.md", page)


if __name__ == "__main__":
    unittest.main()
