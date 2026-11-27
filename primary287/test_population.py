import unittest

from empirical_simulation import evaluate


class PopulationComparison(unittest.TestCase):
    def test_default_has_five_estimates_and_abstains(self):
        result = evaluate({})
        self.assertEqual(len(result["levels"]), 5)
        self.assertEqual(result["levels"][0]["discomfort"], 2)
        self.assertIsNone(result["recommended_level"])
        self.assertEqual(result["real_threshold_status"], "insufficient_evidence")

    def test_empirical_limit_and_budget_drive_choice(self):
        inputs = {"headroom": 10, "costs": [0, 5, None, None, None],
                  "minimum_relevance": 4, "comparable_survey_scenario": True,
                  "max_high_intrusion_risk": .2, "permissions": {"context": "yes", "location": "yes"}}
        self.assertEqual(evaluate(inputs)["recommended_level"], "L1")
        self.assertIsNone(evaluate({**inputs, "headroom": 4})["recommended_level"])
        self.assertIsNone(evaluate({**inputs, "max_high_intrusion_risk": 0})["recommended_level"])
        self.assertIsNone(evaluate({**inputs, "permissions": {"context": "yes"}})["recommended_level"])

    def test_invalid_risk_rejected(self):
        with self.assertRaises(ValueError):
            evaluate({"max_high_intrusion_risk": 1.1})
