# Evaluation status

ClinGraph now includes an offline evaluation runner in `evaluate.py`. It evaluates a versioned JSONL dataset against the same retriever/workflow used by the API and writes JSON results to `evaluations/results.json`.

## Planned evaluation layer

The dataset contains:

- user question;
- expected source IDs;
- reference answer or reference claims;
- retrieved contexts;
- generated answer;
- human review label.

The runner measures:

- **Ragas:** context precision, context recall, faithfulness, and answer relevancy.
- **DeepEval:** answer relevancy, faithfulness, contextual relevancy, citation coverage, tool-call accuracy, tool-call efficiency, and an agentic researcher/judge task score.

Run from the repository root with `python evaluations/evaluate.py`. Ragas and DeepEval are intentionally offline dependencies; they are not run during normal user requests.

## RAG corpus

At startup the AI service loads documents from `DATABASE_URL` when configured. If the database is empty or unavailable, it uses two demo documents embedded in `services/ai/app/main.py`. New evidence is added only by `/internal/v1/ingest/pubmed` or `/internal/v1/ingest/clinicaltrials`, which call PubMed/NCBI E-utilities and ClinicalTrials.gov API v2, persist metadata to Neon, and add embeddings to the local hybrid index/Pinecone when configured. Normal research requests do not crawl the web.
