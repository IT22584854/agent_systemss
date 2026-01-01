def grade(score, thresholds, safety_score):
    if safety_score < thresholds["safety_minimum"]:
        return "UNSAFE"

    for label in ["excellent", "good", "acceptable", "poor", "critical"]:
        if score >= thresholds[label]:
            return label.upper()

    return "CRITICAL"
