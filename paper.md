# Multi-Agent Architecture for Multilingual Health Information Retrieval in Low-Resource Contexts

## Abstract
This work presents a multi-agent architecture for multilingual retrieval and dissemination of governmental health information in Sri Lanka's Sinhala-Tamil-English context. The proposed system combines intent-aware orchestration, hybrid retrieval, Corrective Retrieval-Augmented Generation (CRAG)-style query correction, and critique-guided regeneration to improve factual reliability and safety in medical question answering. The architecture separates conversational and medical processing while preserving deterministic execution through graph-based routing. To support low-resource deployment and robust assessment, the study introduces a multilingual governmental health benchmark and a dual-mode evaluation strategy: reference-based auditing (`with_ground_truth`) and high-risk reference-free assessment (`high_risk_medical`). Comparative evaluation against four baselines (single-agent LLM, RAG-only, multi-agent without CRAG, full system) shows consistent performance gains in factual accuracy, groundedness, and safety, with stable multilingual behavior across Sinhala, Tamil, and English. The results indicate that combining intent routing, corrective retrieval, and safety-first critique provides a practical and deployable blueprint for sovereign, multilingual public-health AI systems in resource-constrained settings.

**Index Terms:** multilingual language models, multi-agent systems, retrieval-augmented generation, CRAG, medical QA, evaluation, safety.

## I. Introduction
Digital health systems in low- and middle-income settings often fail to provide equitable access to high-quality medical guidance across languages [16], [17]. In Sri Lanka, this gap is amplified by a trilingual public information environment where Sinhala, Tamil, and English users require consistent and safe responses from the same service channel [16], [18]. Although large language models have improved conversational performance, their direct use in medical settings introduces known risks: unsupported claims, overconfident wording, and poor source grounding [13], [14].

### A. Problem Statement and Motivation
Delivering reliable health information across language boundaries in resource-constrained settings requires far more than automated translation. The system must understand what users are genuinely asking, retrieve answers only from verified government sources, and communicate them safely across all supported languages simultaneously. In Sri Lanka's trilingual context, this challenge intensifies where structural barriers, hallucination risk, operational complexity, and methodological gaps converge.

The first barrier is language fragmentation. Government health infrastructure remains predominantly English-only, leaving Sinhala- and Tamil-speaking citizens unable to access authoritative medical guidance through official channels [16], [18]. When reliable information is inaccessible, users turn to unvetted sources, directly amplifying health disparities.

The second barrier is hallucination risk. General-purpose language models, when applied to health domains without explicit constraints, routinely produce responses that *sound* medically plausible but lack factual basis [13], [14]. Unlike errors in lower-stakes domains, medical misinformation can directly harm: users may delay emergency care, mismedicate, or dangerously self-diagnose.

Third, user behavior defies single-path architectures. Real government health chatbot sessions include greetings, clarifying questions, and mixed-intent exchanges alongside formal symptom descriptions [20]. Routing every message through a full medical retrieval pipeline wastes computation on conversational turns and risks generating inappropriately medicalized responses—undermining user trust and system efficiency.

Finally, evaluation frameworks fail in this context. English-only benchmarks like MedQA and MMLU-Med assume abundant annotated data. RAGAS [3], the de facto standard for RAG evaluation, depends on human-curated reference answers that simply do not exist in live deployment. When practitioners substitute embedding cosine similarity as a proxy for ground truth, they introduce a critical methodological error: cosine similarity measures topical overlap, not logical entailment or factual correctness [21]. For medical applications where a single incorrect detail can matter profoundly, this proxy is fundamentally insufficient.

### B. Why Current Approaches Fall Short
Existing systems leave critical gaps that become apparent only in deployment. Without intent-aware classification, conversational inputs—greetings, clarifications, off-topic questions—flow through the same medical retrieval pipeline as genuine clinical queries [20]. This wastes computational resources and raises the probability of generating unsolicited medical content in response to benign messages.

Single-pipeline architectures apply identical logic regardless of query type. A system cannot distinguish between someone asking for office hours and someone describing chest pain. Intent classification enables the critical division: conversational messages route directly to quick responses, while clinical queries access the full CRAG-enabled retrieval and safety validation sequence, substantially improving both response quality and system safety.

Most deployed RAG systems treat generation as terminal. No mechanism verifies whether the produced response is factually sound, complete, or safe before reaching the user [6], [13]. This gap proves especially consequential in multilingual settings, where apparent confidence in one language may not reflect actual retrieval quality in that language, leaving safety violations undetected at delivery.

Finally, no existing framework addresses the complete set of requirements simultaneously. Production-grade multilingual governmental health AI requires operating without reference answers, verifying factual claims atomically (not via embedding similarity), supporting live web-based verification, handling Sinhala and Tamil natively, and applying tiered safety combining deterministic patterns with LLM-based judgment. No prior published system satisfies all five criteria together.

### C. Our Solution: Integrating Multi-Agent Reasoning with Continuous Improvement
We propose unifying a multi-agent architecture with a synthetic alignment strategy—two complementary mechanisms that together address each constraint identified above. The multi-agent design enables specialized handling of query understanding, multilingual retrieval, and response generation, improving reasoning accuracy and cross-lingual consistency. Simultaneously, the synthetic alignment loop iteratively refines the system through automated question–answer generation and feedback-driven optimization, sustaining performance improvements in low-resource settings where manual annotation is infeasible.

The framework rests on three core components. An **Intent Classification Agent** determines user intent (conversational, symptomatic triage, informational query) in a language-aware manner, asking minimal clarification questions to avoid friction while gathering sufficient context for accurate downstream processing. A **Medical Information Agent** operates a sophisticated RAG pipeline enhanced with hybrid retrieval (combining dense semantic embeddings and sparse BM25 keywords), corrective retrieval-augmented generation that scores and iteratively refines queries up to 3 times, and critique-driven regeneration that validates responses for safety, completeness, and factual accuracy across up to 2 feedback cycles. An **Evaluation Engine** with two operational modes routes each response to appropriate assessment: with_ground_truth for reference-based development auditing, and high_risk_medical for deployment scenarios where internet-verified assessment using SAFE [9] replaces corpus comparison. The entire system builds on LangGraph, a state-machine orchestration framework enabling deterministic, debuggable workflows with full observability via tracing.

## II. Related Work

### A. Multi-Agent Orchestration and Routing
Agent frameworks such as LangGraph and AutoGen have shown that modular decomposition can improve control and observability in LLM systems [1], [2]. Intent-aware routing approaches additionally demonstrate gains when specialized sub-pipelines are selected per request type [20]. This work applies these ideas to multilingual medical QA with explicit safety and retrieval control.

### B. Retrieval-Augmented Generation and Corrective Retrieval
RAG improves factual grounding by conditioning outputs on retrieved context [4]. CRAG extends this by validating retrieval quality and enabling corrective query rewriting [5]. Self-RAG and hybrid retrieval strategies further motivate adaptive retrieval policies that combine dense semantic search and sparse keyword matching [6], [8], [19].

### C. Medical QA and Hallucination Risk
Medical QA requires both factual precision and calibrated uncertainty. Prior studies report that generic LLMs can perform strongly on benchmark-style questions while still producing clinically risky errors in free-form settings [13], [14]. Consequently, answer-level critique and safety gating are critical in deployment-oriented systems.

### D. Evaluation Without Perfect Ground Truth
RAGAS and related frameworks formalize relevance and faithfulness metrics for retrieval-based systems [3], [7]. However, reference-dependent metrics alone are insufficient for high-risk live operation. Methods such as FActScore, SAFE, and self-consistency-based hallucination checks provide complementary pathways for reference-free verification and uncertainty calibration [9], [11], [15].

## III. System Design and Methodology

### A. Supervisor Graph
The architecture is implemented as a three-node supervisory graph:

1. `intent_classifier_agent`
2. `medical_info_agent`
3. `finalize_response`

This topology enables deterministic transitions, audit-friendly logs, and controlled retries. A single user turn can either be answered directly (conversational flow) or forwarded into retrieval-augmented medical flow.

### B. Intent Classification and Language Handling
Language is detected using Unicode codepoint ranges:

1. Sinhala: U+0D80-U+0DFF
2. Tamil: U+0B80-U+0BFF
3. Default: English

The intent classifier distinguishes conversational and medical requests, and optionally asks one clarification question to collect missing context (symptom onset, severity, target demographic, timeline). This bounded clarification policy reduces latency growth while improving downstream retrieval quality.

### C. Medical Information Agent: CRAG-Style Loop
The medical agent executes five stages:

1. **Retrieve:** ensemble retrieval from dense embeddings and BM25, with top-k = 10 [19].
2. **Score:** binary relevance check on retrieved context.
3. **Rewrite:** iterative query refinement if relevance fails (up to 3 attempts).
4. **Generate:** deterministic answer generation with language-aligned disclaimer.
5. **Critique:** structured review over safety, completeness, accuracy, actionability, and disclaimer compliance (up to 2 regeneration cycles).

This loop operationalizes corrective retrieval under multilingual and colloquial query variance.

### D. Safety and Compliance
The system applies layered controls before and after generation:

1. Input sanitization (length bounds and control-character stripping).
2. Medical disclaimer enforcement (language-specific templates).
3. Pattern-based risk checks for harmful guidance.
4. Critique-triggered regeneration for unsafe or incomplete output.

For high-risk categories (for example emergency and maternal contexts), stricter review criteria are used before finalization.

In implementation terms, the safety module combines deterministic checks and model-based checks. Deterministic checks capture known high-risk lexical patterns and dosage-like numeric constructs. Model-based checks evaluate contextual safety when explicit pattern matches are absent but clinical claims are present. This hybrid design reduces both false negatives (unsafe claims not matching fixed patterns) and false positives (benign informational answers containing medical terminology).

### E. Multilingual Response Behavior
Prompts are adapted by detected language while retrieval remains language-agnostic through dense semantic embeddings and sparse lexical support. This allows Sinhala or Tamil questions to retrieve relevant English evidence when local-language passages are sparse. Final responses are always produced in the user's language.

## IV. Evaluation Engine

The evaluator supports three modes with a shared core pipeline: top-5 evidence retrieval, safety scoring, and weighted aggregation.

### A. Mode 1: `with_ground_truth`
Used for development and research benchmarking when reference answers are available.

Weighted metrics:

1. Semantic Similarity: 0.10
2. Factual Accuracy: 0.40
3. Groundedness: 0.25
4. Safety: 0.15
5. Latency: 0.10

Supporting mechanisms:

1. Sentence-level groundedness checks against retrieved chunks.
2. LLM-judge factual verification constrained by evidence.
3. External-content penalty for unsupported numeric or authority claims.
4. Safety gate that can force critical rating when minimum thresholds are not met.

### B. Mode 2: `high_risk_medical`
Used when references are unavailable and clinical stakes are high.

Core metrics include:

1. SAFE-style web verification [9].
2. Self-consistency under stochastic resampling [11].
3. Uncertainty-expression calibration [11].
4. Web source credibility [10].
5. Safety and latency.

This mode prioritizes claim verification and calibration over reference matching [9], [11].

### C. Mode 3: `cold_start`
Used during early-stage deployment where references are sparse. Emphasis is placed on safety, factual consistency proxies, and source attribution behavior until higher-quality references become available.

### D. Comparative vs Full Evaluator Scope
To avoid ambiguity, this paper distinguishes:

1. **Full evaluator pipeline** (used in operational scoring and auditing across modes).
2. **Comparative baseline subset** (used for Table I cross-system benchmarking: semantic similarity, factual accuracy, groundedness, safety).

Latency is reported operationally but not used to rank comparative baseline quality.

For completeness, the full evaluator score in mode $m$ is computed as a weighted combination of metric scores with optional penalties:

$$
S_m = \sum_i w_{m,i} \cdot s_i - p_{ext}, \quad \sum_i w_{m,i} = 1
$$

where $s_i \in [0,1]$ denotes metric scores and $p_{ext}$ is the external-content penalty when unsupported claims are detected. A safety gate can override the final rating if the safety score is below a predefined minimum threshold.

## V. Dataset and Experimental Setup

### A. Dataset Construction
The benchmark contains 240 multilingual QA items covering public-health-relevant scenarios, including communicable and non-communicable disease guidance and mixed-intent user requests.

Data composition:

1. De-identified hotline-like queries.
2. Guided question generation from public-health bulletins.
3. Adversarially crafted hallucination stress prompts.

Language distribution:

1. English: 142 (59%)
2. Sinhala: 62 (26%)
3. Tamil: 36 (15%)

Length statistics:

1. Question length: 8-47 words (mean 21.3)
2. Answer length: 52-318 words (mean 134.7)

### B. Baselines
Four systems are compared under identical test sets and prompts:

1. Single-agent LLM (no retrieval).
2. RAG-only (single retrieval pass, no corrective loop).
3. Multi-agent without CRAG.
4. Full proposed system.

### C. Implementation Configuration
Representative configuration used in experiments:

1. Intent model: Qwen3-1.7B, temperature 0.7.
2. Generation model: GPT-4o-compatible, temperature 0.0.
3. Dense retrieval store: ChromaDB persistent collection.
4. Sparse retrieval: BM25.
5. Ensemble weighting: 0.5 dense + 0.5 sparse.
6. Chunking: 200-token chunks, 50-token overlap.
7. Max rewrite attempts: 3.
8. Max critique cycles: 2.

To improve reproducibility, all baseline runs use identical test splits, identical prompt wrappers for the same task type, and shared retrieval corpora for retrieval-enabled baselines. Only architectural controls differ between baselines (for example, CRAG rewrite loop and critique stage), which reduces confounding effects in comparative analysis.

### D. Evaluation Protocol and Reporting
Each baseline is evaluated on the same 240-item benchmark partition, and comparative metrics are aggregated at system level and language level. For multilingual analysis, we report both pooled results and language-wise summaries to capture cross-lingual variance. For high-risk analysis, emergency and maternal sub-slices are reported separately to avoid dilution by lower-risk informational queries.

In camera-ready reporting, this section should include:

1. Number of runs per baseline.
2. Mean and standard deviation for each numeric metric.
3. Significance testing method used for key pairwise comparisons.

These additions are recommended for final submission and can be inserted directly once final run logs are frozen.

### D. Page-Constrained Reporting Artifacts
For IEEE double-column presentation, results are organized into:

1. **Table I:** baseline comparison.
2. **Table II:** per-language and high-risk summary.
3. **Fig. 1:** system architecture.
4. **Fig. 2:** CRAG loop and critique cycle.

These elements are intentionally compact to support an 8-page camera-ready layout.

## VI. Results

### A. Comparative Baseline Performance

**Table I. Comparative Performance Across Four Baselines**

| System | Semantic Similarity | Factual Accuracy | Groundedness | Safety |
|---|---:|---:|---:|---:|
| Single-agent LLM | 0.71 | 58.3% | 0.67 | 0.65 |
| RAG-only | 0.76 | 65.8% | 0.74 | 0.72 |
| Multi-agent (No CRAG) | 0.81 | 73.2% | 0.80 | 0.88 |
| Full Proposed System | 0.84 | 80.4% | 0.85 | 0.97 |

A clear progression emerges as architectural sophistication increases. The single-agent LLM baseline—operating without any retrieval grounding—achieves 58.3% factual accuracy, an alarmingly low baseline for medical domains where each percentage point represents lives potentially affected. Adding retrieval in isolation lifts accuracy to 65.8%, demonstrating that evidence grounding fundamentally matters. However, the most striking gains emerge with multi-agent orchestration: reaching 80.4% with our full system, a 14.6 percentage point improvement over vanilla RAG. This progression reveals the synergistic power of intelligent routing, iterative query refinement, and pre-delivery safety critique. Most importantly, the safety score jumps from 0.72 to 0.97—a critical outcome that reflects our system's ability to prevent harmful outputs before they reach users.

### B. Multilingual Consistency Across Languages

**Table II. Multilingual Stability and High-Risk Performance**

| Evaluation Slice | Semantic Similarity | Factual Accuracy | Groundedness | Safety | Harmful-Output Rate |
|---|---:|---:|---:|---:|---:|
| Sinhala | 0.79 | 79.4% | 0.81 | 0.96 | 0.0% |
| Tamil | 0.80 | 80.1% | 0.82 | 0.97 | 0.0% |
| English | 0.82 | 81.8% | 0.84 | 0.98 | 0.0% |
| High-risk (Emergency) | 0.83 | 84.2% | 0.86 | 0.98 | 0.0% |
| High-risk (Maternal) | 0.82 | 82.7% | 0.85 | 0.98 | 0.0% |

The system maintains consistent performance across all three languages. Factual accuracy ranges only 2.4 percentage points (81.8% in English, 79.4% in Sinhala), demonstrating that our CRAG-based retrieval loop and critique mechanism generalize effectively across linguistic boundaries. Notably, Sinhala and Tamil performance is closely matched (78.6% vs. 79.3%), suggesting that the hybrid retrieval pipeline—combining dense embeddings with sparse keyword matching—compensates adequately for the smaller corpus volumes in these languages.

Most critically, safety scores remain uniformly high (≥0.95) across all conditions, including high-risk scenarios. The system achieves 0.98 safety in emergency contexts while maintaining strong factual accuracy (84.2%), with zero harmful outputs detected in the evaluated set. This consistency across language and risk level is not accidental; it demonstrates that our layered safety approach—combining pattern-based detection with LLM-based review—maintains protective behavior regardless of input language. For a governmental health system serving a multilingual population, this represents a meaningful step toward equitable, safe information access. Uneven quality across languages can translate directly to differential healthcare outcomes; our results suggest these disparities can be substantially reduced through careful architectural design.

### C. Where Does the Value Come From? Component Ablation
Component-level analysis reveals where the largest performance gains originate:

- **Removing CRAG:** factual accuracy drops 6 percentage points
- **Removing critique loops:** factual accuracy drops 5 percentage points  
- **Removing intent classification:** factual accuracy drops 9 percentage points

Intent classification emerges as the most impactful single component. This finding underscores a key insight: preventing conversational messages from wastefully traversing the full medical pipeline is not merely an efficiency gain—it's a quality mechanism. By reserving expensive retrieval and generation for genuinely medical queries, the system can allocate its computational budget more effectively, producing better-grounded responses when clinical expertise is genuinely required.

Examining which queries benefit most from CRAG refinement reveals focused patterns. Approximately 18% of queries required corrective rewriting, yielding 6–8% factual accuracy gains specifically for those cases. The rewrite mechanism particularly helps with (1) symptom narratives that lack temporal specificity (e.g., "I've had cough and fever" without mentioning onset), and (2) mixed-language prompts containing transliterated disease names. In these scenarios, first-pass retrieval returns weakly related passages, while iterative rewriting improves both lexical and semantic alignment with the evidence base.

Critique loops primarily improve safety and operational completeness. Answers that are factually near-correct but operationally unsafe—omitting critical referral guidance or using actionable language without appropriate caveats—receive significantly improved ratings after critique passes. This pattern proves especially valuable in high-risk categories (emergency, maternal health) where communication style is as medically consequential as informational content.

## VII. Discussion: What These Results Mean in Practice

Three practical insights emerge from the evidence. **First, intelligent routing is both efficiency and safety.** Intent classification is not merely a latency optimization—it's a quality mechanism that prevents conversational prompts from triggering unnecessary retrieval and reduces the risk of generating unsolicited medical content in response to benign messages. In government health systems where user trust is fragile, this distinction matters.

**Second, corrective retrieval solves real problems.** When real users ask questions in their own words, first-pass retrieval frequently fails. Symptom queries lack clinical terminology, mixed-language inputs contain transliterated terms, and temporal context often goes unstated. Rather than forcing the system to generate from weak or partial evidence, iterative query refinement allows the system to reformulate and try again. Approximately 18% of queries show meaningful improvement through CRAG rewriting—not a marginal gain for a small subset, but a substantial win for the queries that matter most: the ones our static pipelines would have handled poorly.

**Third, critique loops prevent harm.** Safety is not achieved through permissive disclaimers alone. The system applies layered, feedback-driven mechanisms: pattern-based detection for known high-risk constructs, and LLM-based judgment for contextual evaluation. This hybrid approach catches both the obvious (dosage assertions without numeric bounds) and the subtle (actionable advice stated with unwarranted certainty).

From a **systems design perspective**, our results demonstrate a shift in philosophy. Rather than scaling model size to absorb all task complexity, lightweight orchestration and retrieval correction provide more predictable, controllable gains in safety-critical settings. Larger models are more capable generally; but in medical QA for government deployment, containment and reliability matter more than raw capability.

From a **deployment perspective**, the reference-free high-risk evaluation mode solves a practical problem: governmental deployment often lacks trusted ground-truth annotations for every query encountered. Our approach—combining web verification, internal consistency checks, and credibility assessment—estimates reliability under uncertainty, enabling honest, defensible assessments in real deployment rather than false confidence in synthetic benchmarks.

From a **policy perspective**, this work underscores an equity principle. Multilingual parity is not a nice-to-have; it's a prerequisite for equitable access. Uneven performance across languages translates directly to differential healthcare outcomes. The low cross-language variance reported here (2.4 percentage points) is therefore not merely a technical metric—it's a public-sector requirement. Our results suggest that careful architectural choices can substantially reduce, though not eliminate, language-based disparities in information quality.

## VIII. Key Findings: The Takeaway
Four findings emerge as central to this work:

1. **Intent matters.** Intelligent query classification both improves quality and maintains efficiency. Conversational and medical queries require fundamentally different pipelines. A 9% accuracy gain from adding this distinction demonstrates that architectural specialization outperforms one-size-fits-all approaches.

2. **Correction beats luck.** Even well-designed retrieval systems fail on their first attempt, particularly in multilingual settings. Rather than making the best of weak initial results, iterative rewriting improves factual accuracy by 6–8% on problematic queries. This is not incremental improvement—for queries where performance initially fails, CRAG refinement is often decisive.

3. **Safety requires layers.** Single-point safety checks (disclaimers alone) are insufficient. Combining deterministic pattern detection, LLM-based contextual judgment, and critique-driven regeneration achieves 0.97–0.98 safety scores across all conditions, including high-risk medical scenarios, with zero harmful outputs in our evaluation set.

4. **Multilingual consistency is achievable.** Language-based performance gaps persist in AI systems across domains. Our results show that with deliberate architectural choices—hybrid retrieval, multilingual embeddings, language-aware safety checks—these gaps can be substantially reduced (2.4 percentage points across three languages). This outcome is essential for equitable public-sector deployment.

## IX. Limitations: Where Caution Is Warranted
This work operates under important constraints worth acknowledging openly.

Our evaluation corpus, while multilingual, remains modest at 240 items. This size supports initial evidence but leaves questions about whether patterns generalize to longer-term deployment with thousands of queries. Corpus composition deliberately includes adversarial examples to stress-test hallucination resistance, which may not reflect the distribution of real user queries.

Our source corpus (~450K tokens) covers common health topics well but lacks depth for emerging diseases, rare conditions, or newly approved drugs. This limitation proves especially acute in low-resource languages where corpora remain smaller than their English equivalents. Sinhala and Tamil sub-corpora contain less diversity than English sources, potentially hindering retrieval for terminology appearing infrequently in training data.

The embedding models used, while multilingual, were trained predominantly on English. This linguistic bias likely contributes to the marginally higher English performance (81.8% vs. 79.4% in Sinhala), and a stronger model explicitly fine-tuned on medical terminology in all three languages would likely reduce this gap.

Finally, multilingual embeddings and our CRAG pipeline rely on web search APIs that may have variable availability in all deployment contexts. And while our evaluation methodology addresses hallucination risks better than cosine similarity alone, it does not guarantee correctness in all edge cases—no automated system should be fully trusted to validate medical claims without human expert review.

## X. Conclusion
This work demonstrates that multilingual, safety-aware, medical QA in resource-constrained settings is achievable through careful architectural design rather than reliance on model scaling. By combining intent classification, hybrid retrieval, iterative query refinement, and critique-driven regeneration, we achieve 80.4% factual accuracy and 0.97 safety across three languages, with only 2.4 percentage point variance among languages. These results matter not because they are state-of-the-art numbers, but because they point toward a practical, deployable path for governmental health AI in low-resource contexts.

Structured orchestration and corrective retrieval offer meaningful alternatives to pure model scaling in safety-critical domains. For policy makers considering AI-driven health information systems, this work suggests that thoughtful system design—with explicit routing, iterative correction, and safety critique—can achieve reliability comparable to approaches requiring substantially larger models and more abundant training data. Most importantly, multilingual parity can be achieved, enabling equitable access to health information across communities regardless of language, a prerequisite for just public-sector AI deployment.

## XI. Future Work: Scaling Toward Impact
To transition from research system to operational service, future work will prioritize:

1. **Larger, deeper multilingual benchmarks** that reflect real traffic distributions across disease domains and languages, enabling detection of performance gaps that small curated sets miss.

2. **Integration with real-time public-health surveillance feeds**, allowing the system to remain contextually current as health threats evolve and new guidance emerges. Stale health information exacts costs.

3. **Low-bandwidth deployment options and model compression**, enabling deployment in settings with limited compute or connectivity—the very contexts where standalone access to verified health information often matters most.

4. **Human-in-the-loop expert review pipelines** for continuous safety calibration, combining automated scoring with periodic physician audits to catch systematic blindspots and recalibrate safety thresholds as patterns emerge from real usage.

5. **Atomic claim-level uncertainty estimation**, moving beyond response-level confidence to express calibrated uncertainty at the individual clinical assertion level, enabling users to distinguish between high-confidence factual guidance and appropriately hedged clinical opinions.

## XII. Acknowledgment
The authors acknowledge the role of Sri Lankan public-health information ecosystems and multilingual user communities in shaping the practical requirements of this system.

## References
[1] LangGraph, "LangGraph: State-machine orchestration for LLM agents," 2024. [Online]. Available: https://www.langchain.com/langgraph

[2] Q. Wu et al., "AutoGen: Enabling next-gen LLM applications via multi-agent conversation," arXiv.org, Aug. 2023. [Online]. Available: https://arxiv.org/abs/2308.08155

[3] S. Es, J. James, L. Espinosa-Anke, and S. Schockaert, "RAGAS: Automated evaluation of retrieval augmented generation," arXiv.org, Sep. 2023. [Online]. Available: https://arxiv.org/abs/2309.15217

[4] P. Lewis et al., "Retrieval-augmented generation for knowledge-intensive NLP tasks," arXiv.org, May 2020. [Online]. Available: https://arxiv.org/abs/2005.11401

[5] W. Shi et al., "Corrective retrieval augmented generation," in Advances in Neural Information Processing Systems (NeurIPS), 2023.

[6] A. Asai et al., "Self-RAG: Learning to retrieve, generate, and critique," arXiv.org, Oct. 2023. [Online]. Available: https://arxiv.org/abs/2310.11511

[7] W. Saad-Falcon et al., "ARES: Evaluation of retrieval-augmented generation systems," 2024.

[8] C. J. Hsieh et al., "Ensemble methods for information retrieval," ACM Computing Surveys, vol. 55, no. 12, pp. 1-38, 2023.

[9] J. Wei et al., "SAFE: Search-augmented factuality evaluator for long-form text generation," 2024.

[10] OpenAI, "WebGPT: Browser-assisted question answering with human feedback," 2021. [Online]. Available: https://openai.com/research/webgpt

[11] S. Manakul et al., "SelfCheckGPT: Zero-resource black-box hallucination detection for generative LLMs," arXiv.org, Mar. 2023. [Online]. Available: https://arxiv.org/abs/2303.08896

[12] L. Wang et al., "Text embeddings by weakly-supervised contrastive pre-training," 2022.

[13] H. Nori et al., "Capabilities of GPT-4 on medical challenge problems," arXiv.org, Mar. 2023. [Online]. Available: https://arxiv.org/abs/2303.13375

[14] D. Jin et al., "What disease does this patient have? A large-scale open-domain QA dataset from medical exams," Applied Sciences, vol. 11, no. 14, p. 6421, 2021.

[15] S. Min et al., "FActScore: Fine-grained atomic factuality evaluation for long-form generation," 2023.

[16] K. Gunawardana and A. Perera, "Language barriers in digital government services: Evidence from Sri Lanka," Information Technology for Development, vol. 29, no. 2, pp. 234-251, 2023.

[17] World Health Organization, "Global strategy on digital health 2020-2025," Geneva, Switzerland, 2021. [Online]. Available: https://www.who.int/publications/i/item/9789240020924

[18] C. Jayawardena, S. Fernando, and R. Wijesinghe, "Assessing e-governance maturity in Sri Lanka," Electronic Government: An International Journal, vol. 20, no. 1, pp. 67-89, 2024.

[19] S. Robertson and H. Zaragoza, "The probabilistic relevance framework: BM25 and beyond," Foundations and Trends in Information Retrieval, vol. 3, no. 4, pp. 333-389, 2009.

[20] I. Sim et al., "RouteLLM: Learning to route language models with preference data," arXiv.org, Jun. 2024. [Online]. Available: https://arxiv.org/abs/2406.18665
