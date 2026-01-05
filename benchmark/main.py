from utils.markdown_loader import load_corpus
from src.metrics.factual_accuracy import factual_accuracy
from src.metrics.semantic_similarity import semantic_similarity
from src.metrics.safety import safety_score
from src.metrics.completeness import completeness
from src.metrics.source_attribution import source_attribution
from src.profile_selector import select_profile
from src.scorer import compute_weighted_score
from src.grader import grade
import yaml

# Incoming agent response
payload = {
    "question": "Where can I get emergency treatment for dengue?",
    "response": "You can visit a government hospital. According to the Ministry of Health...",
    "category": "emergency_services",
    "expected_points": ["hospital", "emergency", "government"],
    "has_ground_truth": True
}

corpus = load_corpus("data/corpus")

metrics = {
    "factual_accuracy": factual_accuracy(payload["response"], corpus),
    "semantic_similarity": semantic_similarity(payload["question"], payload["response"]),
    "safety": safety_score(payload["response"]),
    "completeness": completeness(payload["response"], payload["expected_points"]),
    "source_attribution": source_attribution(payload["response"])
}

profile = select_profile(payload["category"], payload["has_ground_truth"])

final_score = compute_weighted_score(
    metrics,
    profile,
    "config/evaluation_config.yaml"
)

with open("config/evaluation_config.yaml") as f:
    thresholds = yaml.safe_load(f)["thresholds"]

final_grade = grade(final_score, thresholds, metrics["safety"])

print("Profile:", profile)
print("Metrics:", metrics)
print("Final Score:", final_score)
print("Grade:", final_grade)
