from sklearn.metrics.pairwise import cosine_similarity
from utils.embeddings import embed

def factual_accuracy(response, corpus):
    r = embed(response)
    c = embed(corpus)
    return float(cosine_similarity(r, c).max())
