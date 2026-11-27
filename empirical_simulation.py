"""Dependency-free empirical population lookup and constrained scenario comparison."""
import json
from pathlib import Path

from synthetic_simulation import number
from threshold_engine import LEVELS

ARTIFACT = Path(__file__).parent / "results/primary287_population_v2.json"
SOURCES = ("Generic", "Context and location", "Browsing history", "Purchase history",
           "Context, location, browsing and purchase history")
REQUIRED = ((), ("context", "location"), ("behavior",), ("history",),
            ("context", "behavior", "history", "location"))


def evaluate(payload):
    if not isinstance(payload, dict):
        raise ValueError("Send an object")
    model = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    ceiling = number(payload.get("threshold", 4), "Discomfort ceiling", 1, 7)
    minimum = number(payload.get("minimum_relevance", 3), "Minimum relevance", 1, 7)
    risk_limit = payload.get("max_high_intrusion_risk")
    if risk_limit is not None:
        risk_limit = number(risk_limit, "Maximum high-intrusion share", 0, 1)
    permissions = payload.get("permissions", {})
    if not isinstance(permissions, dict) or any(v not in ("yes", "no", "unknown") for v in permissions.values()):
        raise ValueError("Invalid permission")
    costs = payload.get("costs", [None] * 5)
    if not isinstance(costs, list) or len(costs) != 5:
        raise ValueError("Five cost estimates required")
    headroom = payload.get("headroom")
    if headroom is not None:
        headroom = number(headroom, "Headroom")
    in_scope = payload.get("comparable_survey_scenario") is True
    rows = []
    for i, name in enumerate(LEVELS):
        level = f"L{i}"
        evidence = model["levels"][level]
        ratings = evidence["rating_median"]
        spans = evidence["family_rating_median_range"]
        risk = evidence["mean"]["high_intrusion_ge5"]
        risk_range = evidence["family_range"]["high_intrusion_ge5"]
        reasons = [f"Confirm {source} data possession and permission"
                   for source in REQUIRED[i] if permissions.get(source) != "yes"]
        cost = costs[i]
        if cost is None:
            reasons.append("Cost estimate missing")
        else:
            cost = number(cost, "Incremental cost")
            if headroom is None:
                reasons.append("Budget headroom missing")
            elif cost > headroom:
                reasons.append("Cost exceeds headroom")
        business_eligible = not reasons
        if not in_scope:
            reasons.append("Confirm that the comparison is limited to the survey-style scenario")
        if risk_limit is None:
            reasons.append("Set a maximum observed high-intrusion share")
        elif risk_range[1] > risk_limit:
            reasons.append("A surveyed family exceeds the high-intrusion limit")
        if spans["discomfort_score"][1] > ceiling or spans["relevance_score"][0] < minimum:
            reasons.append("Surveyed families do not all meet the rating limits")
        rows.append({"level":level,"name":name,"source":SOURCES[i],"cost":cost,
                     "eligible":not reasons,"business_eligible":business_eligible,"reasons":reasons,
                     "n":evidence["n"],"families":evidence["families"],
                     "intrusion":ratings["intrusiveness_score"],"discomfort":ratings["discomfort_score"],
                     "relevance":ratings["relevance_score"],"high_intrusion_rate":risk,
                     "high_intrusion_range":risk_range,"rating_range":spans})
    choice = next((r["level"] for r in rows if r["eligible"]), None)
    return {"source":model["source"],"levels":rows,"recommended_level":choice,
            "reason":("Lowest level meeting the limits across the surveyed families and the declared campaign constraints."
                      if choice else "No survey-based choice meets the stated scope, rating, risk, permission and budget conditions."),
            "real_threshold_status":"insufficient_evidence"}
