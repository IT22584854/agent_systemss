from sklearn.metrics.pairwise import cosine_similarity
from utils.embeddings import embed

def semantic_similarity(question, response):
    q = embed(question)
    r = embed(response)
    return float(cosine_similarity(q, r)[0][0])
