class WeightedScorer:
    def __init__(self, config: dict):
        self.config = config

    def score(self, metric_scores: dict, mode: str) -> float:
        weights = self.config["weights"][mode]

        total_score = 0.0

        for metric_name, weight in weights.items():
            metric_value = metric_scores.get(metric_name, 0.0)
            total_score += metric_value * weight

        return round(total_score, 4)