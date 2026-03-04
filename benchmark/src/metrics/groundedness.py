from sklearn.metrics.pairwise import cosine_similarity
from utils.embeddings import embed
import numpy as np
import re


def split_sentences(text):
    # Lightweight sentence split
    return [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]


def groundedness_score(answer, retrieved_chunks, threshold=0.55):

    if not retrieved_chunks:
        return 0.0

    sentences = split_sentences(answer)

    if not sentences:
        return 0.0

    chunk_vectors = embed(retrieved_chunks)

    grounded_count = 0

    for sentence in sentences:
        sentence_vector = embed(sentence)

        similarities = cosine_similarity(sentence_vector, chunk_vectors)[0]
        max_sim = float(np.max(similarities))

        # Sentence considered grounded if similarity above threshold
        if max_sim >= threshold:
            grounded_count += 1

    # Proportional grounding score
    return grounded_count / len(sentences)