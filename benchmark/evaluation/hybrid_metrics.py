from standardized_metrics import standardized_scores
from custom_metrics import custom_score

def hybrid_score(reference, prediction):
    std = standardized_scores(reference, prediction)
    custom = custom_score(reference, prediction)

    final = (
        0.3 * std["standardized_score"] +
        0.7 * custom["custom_score"]
    )

    return {
        "hybrid_score": final,
        **std,
        **custom
    }
