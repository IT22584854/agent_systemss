from sklearn.metrics.pairwise import cosine_similarity
from utils.embeddings import embed
import numpy as np

def factual_accuracy(response, retrieved_chunks, pinecone_scores):

    if not retrieved_chunks:
        return 0.0

    r_vec = embed(response)

    similarities = []

    for chunk in retrieved_chunks:
        c_vec = embed(chunk)
        sim = cosine_similarity(r_vec, c_vec)[0][0]
        similarities.append(sim)

    semantic_max = float(np.max(similarities))
    pinecone_max = float(np.max(pinecone_scores))

    return 0.7 * semantic_max + 0.3 * pinecone_max
