# Copilot instructions for research-project-y4-data-science

## Quick summary
- Purpose: evaluation/benchmark suite for LLM question-answering in health domains (vaccination, maternal health, etc.). The main working area is `benchmark/` which contains the evaluation code, sample scripts, and configuration.

## Architecture & important components 🔧
- `benchmark/` — core evaluation project (config, scripts, requirements, data). See `benchmark/src/config.py` and `benchmark/config.yaml`.
- `benchmark/src/config.py` — central config loader (uses `python-dotenv`) and exposes convenience methods: `get_weights(mode)`, `get_thresholds()`, `get_llm_config()`, `get_safety_config()`.
- `benchmark/config.yaml` — canonical evaluation weights, thresholds, language list, categories, and safety rules. Example modes: **cold_start**, **with_ground_truth**, **high_risk_medical**.
- `benchmark/scripts/markdown_loader..py` — parser for markdown corpora. Note: file name contains a double-dot (`markdown_loader..py`) which is a repo quirk. It splits text by `\n---\n` and expects `### Question` / `### Answer` headings and an optional `## <category>` heading.
- Data layout: `benchmark/data/{test_cases,ground_truth,results}` — these directories are created at runtime by `Config`.

## Environment & setup ⚙️
- Use Python 3.10+ (project depends on modern packages in `benchmark/requirements.txt`).
- Typical setup:
  - cd `benchmark`
  - python -m venv .venv
  - .venv\Scripts\activate (Windows)
  - pip install -r requirements.txt
- Environment variables (use `benchmark/.env`):
  - `ANTHROPIC_API_KEY` — optional (Anthropic API client usage is referenced in requirements)
  - `OPENAI_API_KEY` — optional
- Quick smoke-checks:
  - `python -c "from benchmark.src.config import config; print(config.get_weights('with_ground_truth'))"`
  - `python -c "from benchmark.src.config import config; print(config.get_thresholds())"`

## Patterns & conventions to follow
- Config-first: Most runtime behavior is controlled via `benchmark/config.yaml`; prefer updating YAML over hardcoding values.
- Data format for corpora: blocks separated by `---`, with `### Question` and `### Answer`. The loader infers `category` from the first `## <category>` header.
- Safety & evaluation: Safety rules and required disclaimers live under `safety` in `config.yaml` — use those for evaluating outputs (see `harmful_patterns` and `required_disclaimers`).
- API clients: Code expects API keys via env vars; `python-dotenv` is loaded in `Config` so `.env` in `benchmark/` works for local dev.

## Integration points & external deps
- LLMs: Anthropics and OpenAI (keys via env). Example model string (commented): `claude-sonnet-4-20250514`.
- Sentence-transformers / HuggingFace caches: check `.gitignore` for cache/model directories (models may be large and cached locally).
- Translation: `deep-translator` is in requirements for multilingual support (languages in config: `en`, `si`, `ta`).

## Developer workflows & testing 🧪
- No test suite or CI detected (requirements include `pytest` but `tests/` is absent). If adding tests, place them under `benchmark/tests/` and run from repo root or `benchmark` with `pytest -q`.
- Running benchmarks is currently manual; look for small reusable scripts in `benchmark/scripts/`.

## Known quirks & TODOs ⚠️
- `markdown_loader..py` filename contains an extra dot; this can complicate `import`-style usage — prefer invoking as a script or renaming the file.
- Top-level `README.md` is minimal; there is no CI/automation config present.

## How to help (for agent contributors) 💡
- Use `benchmark/config.yaml` and `benchmark/src/config.py` as the single source of truth for evaluation behavior.
- When adding examples or tests, follow the markdown corpora format and place ground-truth files under `benchmark/data/ground_truth`.
- Before proposing changes to APIs or file naming, flag potential breaking changes (e.g., renaming `markdown_loader..py`) so maintainers can approve.

---
If anything here is unclear or you want more detail (examples of eval scripts, a suggested test scaffold, or CI instructions), tell me which part to expand and I will iterate.