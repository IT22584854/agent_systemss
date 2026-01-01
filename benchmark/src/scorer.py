import yaml

def compute_weighted_score(metrics, profile, config_path):
    with open(config_path) as f:
        config = yaml.safe_load(f)

    weights = config["weights"][profile]

    score = 0.0
    for k, w in weights.items():
        score += metrics.get(k, 0) * w

    return round(score, 3)
