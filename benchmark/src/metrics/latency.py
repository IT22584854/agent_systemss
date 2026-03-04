def latency_score(start_timestamp: float,
                  end_timestamp: float,
                  max_acceptable_latency: float = 5.0) -> float:
    """
    Lower latency = higher score.
    """

    latency = end_timestamp - start_timestamp

    if latency <= 0:
        return 0.0

    if latency >= max_acceptable_latency:
        return 0.0

    return 1.0 - (latency / max_acceptable_latency)