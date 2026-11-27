"""Generate reference plots using the published aggregate evaluation only."""
import json
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "results/primary287_v1.json").read_text())
fig, (left, right) = plt.subplots(1, 2, figsize=(9, 3.8), layout="constrained")
levels = list(data["by_level"])
for label in ("intrusiveness_score", "discomfort_score", "relevance_score"):
    left.plot(levels, [data["by_level"][k]["means"][label] for k in levels],
              "o-", label=label.removesuffix("_score"))
left.set(ylim=(1, 7), ylabel="Observed mean rating", xlabel="Conceptual level")
left.legend()
right.plot([0, 1], [0, 1], "--", color="gray")
for model in ("level_mean", "logistic", "forest"):
    bins = data["grouped"]["targets"]["high_intrusion_ge5"][model]["reliability"]
    right.scatter([b["pred"] for b in bins], [b["observed"] for b in bins],
                  s=[10 + b["n"] for b in bins], label=model.replace("_", " "))
right.set(xlim=(0, 1), ylim=(0, 1), xlabel="Mean predicted probability",
          ylabel="Observed high-intrusion frequency")
right.legend()
fig.savefig(ROOT / "output/49C_V2/49C_Primary_Survey_Figures.png", dpi=180)
