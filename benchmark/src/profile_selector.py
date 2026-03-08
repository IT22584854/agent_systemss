def select_profile(category, has_ground_truth):
    if category in ["emergency_services", "maternal_health"]:
        return "high_risk_medical"
    if has_ground_truth:
        return "with_ground_truth"
    return "cold_start"
