import os
from pinecone import Pinecone
from utils.embeddings import embed


class PineconeRetriever:

    def __init__(self, index_name):
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY not found in environment variables.")

        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)

    def retrieve(self, query, top_k=5):

        # Embed query
        query_vector = embed(query)

        # Query Pinecone
        results = self.index.query(
            vector=query_vector.tolist(),
            top_k=top_k,
            include_metadata=True
        )

        matches = results.get("matches", [])

        retrieved_texts = []
        scores = []
        metadata_list = []

        print("\n===== RAW PINECONE MATCHES =====\n")

        for i, match in enumerate(matches):

            score = match.get("score", 0)
            meta = match.get("metadata", {})

            print(f"\n--- Match {i} ---")
            print("Score:", score)
            print("Metadata keys:", list(meta.keys()))

            # 🔥 Try multiple possible text fields
            text = (
                meta.get("text") or
                meta.get("chunk") or
                meta.get("content") or
                ""
            )

            if not text:
                print("⚠ WARNING: No text field found in metadata.")

            retrieved_texts.append(text)
            scores.append(score)
            metadata_list.append(meta)

        return retrieved_texts, scores, metadata_list