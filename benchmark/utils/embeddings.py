from FlagEmbedding import BGEM3FlagModel
import numpy as np

# Initialize model once
model = BGEM3FlagModel(
    'BAAI/bge-m3',
    use_fp16=True  
)

def embed_texts(texts, batch_size=16):
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]

        embeddings = model.encode(
            batch,
            batch_size=batch_size,
            max_length=512
        )["dense_vecs"]

        all_embeddings.append(embeddings)

        print(f"Embedded {i + len(batch)} / {len(texts)}")

    return np.vstack(all_embeddings)


def embed(text):
    """
    Compatible single-text embedding function
    used by evaluation metrics.
    """
    if isinstance(text, str):
        text = [text]

    embedding = model.encode(
        text,
        batch_size=1,
        max_length=512
    )["dense_vecs"]

    return np.array(embedding)