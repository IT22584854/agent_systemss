def chunk_docs(docs, chunk_size=800, overlap=100):
    chunks = []

    for doc in docs:
        text = doc["text"]
        start = 0
        chunk_id = 0

        while start < len(text):
            end = start + chunk_size
            piece = text[start:end]

            chunks.append({
                "source_id": doc["id"],
                "chunk_id": f"{doc['id']}_chunk_{chunk_id}",
                "text": piece
            })

            start = end - overlap
            chunk_id += 1

    return chunks