import re


def external_content_penalty(answer, retrieved_chunks):
    """
    Penalizes if answer contains content not appearing
    in any retrieved chunk.
    """

    corpus_text = " ".join(retrieved_chunks).lower()
    answer_lower = answer.lower()

    penalty = 0.0

    # Check numeric claims
    numbers = re.findall(r'\d+', answer_lower)

    for num in numbers:
        if num not in corpus_text:
            penalty += 0.05

    # Check suspicious keywords
    suspicious_sources = ["who", "cdc", "global data", "un report"]

    for word in suspicious_sources:
        if word in answer_lower and word not in corpus_text:
            penalty += 0.1

    return min(penalty, 0.3)