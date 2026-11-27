import json
import unittest
from pathlib import Path

from research_dashboard import dashboard_data


class PrimaryResearchContract(unittest.TestCase):
    def setUp(self):
        self.artifact = json.loads(Path("results/primary287_v1.json").read_text())

    def test_saved_folds_are_disjoint_with_all_levels(self):
        folds = self.artifact["grouped"]["folds"]
        self.assertEqual(sum(f["test_n"] for f in folds), self.artifact["eligible"])
        for fold in folds:
            self.assertTrue(set(fold["held_out"]).isdisjoint(fold["train_families"]))
            self.assertEqual(set(fold["levels"]), {f"L{i}" for i in range(5)})

    def test_dashboard_only_exposes_curated_aggregates(self):
        panel = dashboard_data()["primary287"]
        self.assertEqual(set(panel), {"scope", "eligible", "by_level", "abstention"})
        self.assertEqual(sum(x["n"] for x in panel["by_level"].values()), panel["eligible"])
        self.assertIn("No deployable empirical prediction", panel["abstention"])

    def test_high_rating_counts_and_abstention(self):
        for target, flag in (("high_intrusion_ge5", "high_intrusion"), ("high_discomfort_ge5", "high_discomfort")):
            expected = self.artifact["flags"][flag]["included"]["derived_high"]
            for metrics in self.artifact["grouped"]["targets"][target].values():
                tn, fp, fn, tp = metrics["confusion"]
                self.assertEqual(fn + tp, expected)
                self.assertEqual(tn + fp + fn + tp, self.artifact["eligible"])
        self.assertEqual(self.artifact["coverage"], 0)
