import os
import yaml
import wandb
from src.retrieval import PineconeRetriever
from src.metrics.semantic_similarity import semantic_similarity
from src.metrics.factual_accuracy import factual_accuracy
from src.metrics.safety import safety_score
from src.metrics.latency import latency_score
from src.metrics.groundedness import groundedness_score
from src.metrics.external_detection import external_content_penalty
from src.scorer import WeightedScorer
from utils.supabase_db import store_evaluation
from dotenv import load_dotenv

load_dotenv()

# Initialize WandB once
wandb.login(key=os.getenv("WANDB_API_KEY"))

class EvaluationEngine:

    def __init__(self, config_path, index_name):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.retriever = PineconeRetriever(index_name)
        self.scorer = WeightedScorer(self.config)

    def evaluate(self, agent_response: dict, mode: str):
        question = agent_response["question"]
        answer = agent_response["answer"]
        start_ts = agent_response["start_timestamp"]
        end_ts = agent_response["end_timestamp"]

        # 1️⃣ Retrieve context
        retrieved_chunks, pinecone_scores, metadata = self.retriever.retrieve(question, top_k=5)

        metrics = {}

        # 2️⃣-7️⃣ Metric Calculations
        metrics["semantic_similarity"] = semantic_similarity(question, answer)
        metrics["factual_accuracy"] = factual_accuracy(answer, retrieved_chunks, pinecone_scores)
        metrics["groundedness"] = groundedness_score(answer, retrieved_chunks)
        metrics["safety"] = safety_score(str(answer), self.config)
        metrics["latency"] = latency_score(start_ts, end_ts)
        external_penalty = external_content_penalty(answer, retrieved_chunks)

        # 8️⃣ Weighted Score
        final_score = self.scorer.score(metrics, mode)
        final_score = max(0.0, final_score - external_penalty)
        rating = self._rating_label(final_score)

        # 9️⃣ Safety Gate
        if mode == "high_risk_medical":
            if metrics["safety"] < self.config["thresholds"]["safety_minimum"] or metrics["groundedness"] < 0.6:
                rating = "critical"
                final_score = 0.0

        # 🔟 Log to WandB FIRST 
        # (We do this first so we can close the connection with .finish())
        try:
            run = wandb.init(project="rag-evaluation", name="evaluation_run", reinit=True)
            wandb.log({**metrics, "external_penalty": external_penalty, "final_score": final_score, "rating": rating})
            run.finish() # This is crucial to release the network
        except Exception as e:
            print("W&B logging failed:", e)

        # 1️⃣1️⃣ Store in Supabase LAST
        # Prepare the row with absolute type safety
        db_row = {
            "question": str(question),
            "answer": str(answer),
            "semantic_similarity": float(metrics.get("semantic_similarity", 0)),
            "factual_accuracy": float(metrics.get("factual_accuracy", 0)),
            "groundedness": float(metrics.get("groundedness", 0)),
            "safety": float(metrics.get("safety", 0)),
            "latency": float(metrics.get("latency", 0)),
            "external_penalty": float(external_penalty),
            "final_score": float(final_score),
            "rating": str(rating)
        }

        store_evaluation(db_row)

        return {
            "status": "success",
            "metrics": metrics,
            "external_penalty": external_penalty,
            "retrieved_sources": metadata,
            "final_score": round(final_score, 4),
            "rating": rating
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