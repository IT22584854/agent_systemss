def completeness(response: str, expected_points: list[str]) -> float:
    if not expected_points:
        return 1.0

    hits = sum(
        1 for point in expected_points
        if point.lower() in response.lower()
    )

    return hits / len(expected_points)