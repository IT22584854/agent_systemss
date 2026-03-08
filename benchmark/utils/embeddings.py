# from sentence_transformers import SentenceTransformer

# _model = SentenceTransformer("all-MiniLM-L6-v2")

# def embed(texts):
#     return _model.encode(texts, convert_to_tensor=True)

from FlagEmbedding import BGEM3FlagModel

_model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)

def embed(texts):

    if isinstance(texts, str):
        texts = [texts]
        
    embeddings = _model.encode(
        texts, 
        batch_size=12, 
        max_length=8192,
        return_dense=True, 
        return_sparse=False, 
        return_colbert_vecs=False
    )
    
    
    return embeddings['dense_vecs']
