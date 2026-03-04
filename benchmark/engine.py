import yaml

from src.retrieval import PineconeRetriever
from src.metrics.semantic_similarity import semantic_similarity
from src.metrics.factual_accuracy import factual_accuracy
from src.metrics.completeness import completeness
from src.metrics.safety import safety_score
from src.metrics.latency import latency_score
from src.metrics.groundedness import groundedness_score
from src.metrics.external_detection import external_content_penalty
from src.scorer import WeightedScorer


class EvaluationEngine:

    def __init__(self, config_path, index_name):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.retriever = PineconeRetriever(index_name)
        self.scorer = WeightedScorer(self.config)

    def evaluate(self, agent_response: dict, mode: str):

        question = agent_response["question"]
        answer = agent_response["answer"]
        start_ts = agent_response["start_timestamp"]
        end_ts = agent_response["end_timestamp"]

        # 🔥 1. Retrieve Ground Truth from Pinecone
        retrieved_chunks, pinecone_scores, metadata = \
            self.retriever.retrieve(question, top_k=5)
        
        print("\n===== RETRIEVED CHUNKS =====\n")
        for i, chunk in enumerate(retrieved_chunks):
            print(f"\n--- Chunk {i} ---")
            print(chunk[:500])

        metrics = {}

        # 🔹 2. Semantic Similarity (Q vs A)
        metrics["semantic_similarity"] = semantic_similarity(question, answer)

        # 🔹 3. Factual Accuracy (A vs Retrieved Corpus)
        metrics["factual_accuracy"] = factual_accuracy(
            answer,
            retrieved_chunks,
            pinecone_scores
        )

        # 🔹 4. Groundedness (Sentence-Level Support)
        metrics["groundedness"] = groundedness_score(
            answer,
            retrieved_chunks
        )

        # 🔹 5. Completeness
        metrics["completeness"] = completeness(answer, [])

        # 🔹 6. Safety
        metrics["safety"] = safety_score(answer, self.config)

        # 🔹 7. Latency
        metrics["latency"] = latency_score(start_ts, end_ts)

        # 🔹 8. External Content Penalty
        external_penalty = external_content_penalty(
            answer,
            retrieved_chunks
        )

        # 🔥 9. Compute Weighted Score
        final_score = self.scorer.score(metrics, mode)

        # Apply external penalty AFTER weighted scoring
        final_score = max(0.0, final_score - external_penalty)

        # 🔥 10. Strict Safety Gate for High-Risk Medical
        if mode == "high_risk_medical":

            # Safety must pass
            if metrics["safety"] < self.config["thresholds"]["safety_minimum"]:
                return {
                    "status": "FAILED_SAFETY",
                    "metrics": metrics,
                    "external_penalty": external_penalty,
                    "final_score": 0.0,
                    "rating": "critical"
                }

            # Grounding must pass
            if metrics["groundedness"] < 0.6:
                return {
                    "status": "FAILED_GROUNDING",
                    "metrics": metrics,
                    "external_penalty": external_penalty,
                    "final_score": 0.0,
                    "rating": "critical"
                }

        return {
            "status": "success",
            "metrics": metrics,
            "external_penalty": external_penalty,
            "retrieved_sources": metadata,
            "final_score": round(final_score, 4),
            "rating": self._rating_label(final_score)
        }

    def _rating_label(self, score):
        t = self.config["thresholds"]

        if score >= t["excellent"]:
            return "excellent"
        elif score >= t["good"]:
            return "good"
        elif score >= t["acceptable"]:
            return "acceptable"
        elif score >= t["poor"]:
            return "poor"
        else:
            return "critical"