import json
import pandas as pd
import matplotlib.pyplot as plt

from standardized_metrics import standardized_scores
from custom_metrics import custom_score
from hybrid_metrics import hybrid_score

# Load test cases
with open("data/test_cases.json") as f:
    cases = json.load(f)

results = []

# Evaluate each case
for case in cases:
    ref = case["reference"]
    pred = case["prediction"]

    std = standardized_scores(ref, pred)
    custom = custom_score(ref, pred)
    hybrid = hybrid_score(ref, pred)

    results.append({
        "id": case["id"],
        "bleu": std["bleu"],
        "rougeL": std["rougeL"],
        "standardized_score": std["standardized_score"],
        "custom_score": custom["custom_score"],
        "hybrid_score": hybrid["hybrid_score"],
        "safety": custom["safety"]
    })

# Save results
df = pd.DataFrame(results)
df.to_csv("metric_comparison.csv", index=False)
print(df)

# ===== Optional Plot =====
# Visual comparison of metric scores
df.set_index("id")[["standardized_score", "custom_score", "hybrid_score"]].plot(
    kind="bar",
    title="Metric Comparison for Medical QA",
    figsize=(8,5),
    ylim=(0,1)  # all scores are normalized between 0-1
)
plt.ylabel("Score")
plt.xlabel("Question ID")
plt.tight_layout()
plt.show()
