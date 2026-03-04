# from sklearn.metrics.pairwise import cosine_similarity
# from utils.embeddings import embed
# import numpy as np

# def factual_accuracy(response: str, corpus_chunks: list[str]) -> float:
#     """
#     corpus_chunks = list of retrieved ground truth passages
#     """
#     r = embed(response)

#     scores = []
#     for chunk in corpus_chunks:
#         c = embed(chunk)
#         score = cosine_similarity(r, c)[0][0]
#         scores.append(score)

#     return float(np.max(scores)) if scores else 0.0


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
