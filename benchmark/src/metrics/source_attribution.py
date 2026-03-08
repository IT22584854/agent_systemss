def source_attribution(response):
    indicators = ["ministry of health", "who", "epidemiology unit", "government"]
    response = response.lower()
    return 1.0 if any(i in response for i in indicators) else 0.0
