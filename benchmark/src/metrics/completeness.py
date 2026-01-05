def completeness(response, expected_points):
    if not expected_points:
        return 1.0
    hits = sum(1 for p in expected_points if p.lower() in response.lower())
    return hits / len(expected_points)
