"""Offline RAGAS + DeepEval evaluation for ClinGraph.

Usage: python evaluations/evaluate.py
Optional integrations are imported lazily so the API does not require an
evaluation provider or network access at request time.
"""

import json
import os
import sys
import warnings
from pathlib import Path

# DeepEval currently passes a Sentry option removed by some Sentry SDK
# versions. Evaluation is local by default, so disable its telemetry before
# importing DeepEval; users can explicitly opt in outside this script.
os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "ai"))

from app.retrieval import Document, HybridRetriever  # noqa: E402
from app.workflow import ClinicalResearchWorkflow  # noqa: E402


class TinyEmbedder:
    def embed_query(self, text):
        return tuple(float(hash(token) % 101) for token in text.lower().split())[:32]

    embed_document = embed_query


class RagasEmbeddingAdapter:
    """Expose the interface expected by RAGAS 0.4's compatibility metrics."""

    def __init__(self, embedder):
        self.embedder = embedder

    def embed_query(self, text):
        return list(self.embedder.embed_query(text))

    def embed_documents(self, texts):
        return [list(self.embedder.embed_document(text)) for text in texts]


def load_cases():
    with (ROOT / "evaluations" / "dataset.jsonl").open() as handle:
        return [json.loads(line) for line in handle if line.strip()]


def provider_metrics(rows):
    """Run RAGAS and DeepEval when their optional evaluation stacks are installed.

    Both libraries may require an LLM provider configured in the environment;
    failures are returned as status objects instead of breaking deterministic
    retrieval/tool metrics.
    """
    result = {}
    try:
        from ragas import EvaluationDataset, evaluate
        from ragas.llms import llm_factory
        # Ragas 0.4's compatibility metric classes are still the objects
        # accepted by evaluate(); the newer collections classes are for the
        # experiment API and are rejected by the legacy evaluate() function.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from ragas.metrics import AnswerRelevancy, ContextPrecision, ContextRecall, Faithfulness

        from app.config import get_settings
        settings = get_settings()
        if not settings.groq_api_key and not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("Set GROQ_API_KEY or OPENAI_API_KEY to run LLM-backed RAGAS metrics")
        if settings.groq_api_key:
            from openai import OpenAI
            # Groq exposes an OpenAI-compatible endpoint; RAGAS specifically
            # validates that the client is an openai.OpenAI instance.
            groq_openai_client = OpenAI(
                api_key=settings.groq_api_key,
                base_url="https://api.groq.com/openai/v1",
            )
            ragas_llm = llm_factory(settings.groq_model, provider="openai", client=groq_openai_client)
        else:
            ragas_llm = llm_factory(os.getenv("RAGAS_MODEL", "gpt-4o-mini"), provider="openai")
        from app.retrieval import HashEmbedder, LocalEmbedder
        try:
            evaluation_embedder = LocalEmbedder(
                model_name=settings.embedding_model,
                device=settings.embedding_device,
                local_files_only=True,
            )
        except Exception:
            evaluation_embedder = HashEmbedder()
        ragas_embeddings = RagasEmbeddingAdapter(evaluation_embedder)
        dataset = EvaluationDataset.from_list([
            {"user_input": row["question"], "response": row["answer"],
             "retrieved_contexts": row["contexts"], "reference": row["reference_answer"]}
            for row in rows
        ])
        scored = evaluate(dataset, metrics=[ContextPrecision(llm=ragas_llm), ContextRecall(llm=ragas_llm), Faithfulness(llm=ragas_llm), AnswerRelevancy(llm=ragas_llm, embeddings=ragas_embeddings)])
        result["ragas"] = dict(scored)
    except Exception as exc:
        result["ragas"] = {"status": "not_run", "reason": str(exc)}

    try:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("Set OPENAI_API_KEY to run DeepEval's built-in LLM metrics; deterministic tool metrics already ran")
        from deepeval import evaluate
        from deepeval.metrics import AnswerRelevancyMetric, ContextualRelevancyMetric, FaithfulnessMetric
        from deepeval.test_case import LLMTestCase

        test_cases = [LLMTestCase(input=row["question"], actual_output=row["answer"],
                                  retrieval_context=row["contexts"], expected_output=row["reference_answer"])
                      for row in rows]
        report = evaluate(test_cases, [AnswerRelevancyMetric(), FaithfulnessMetric(), ContextualRelevancyMetric()])
        result["deepeval"] = {"status": "completed", "report": str(report)}
    except Exception as exc:
        result["deepeval"] = {"status": "not_run", "reason": str(exc)}
    return result


def main():
    docs = [
        Document("demo-001", "Evidence synthesis for hypertension interventions", "hypertension blood pressure intervention clinical trial evidence"),
        Document("demo-002", "Clinical outcomes in type 2 diabetes", "type 2 diabetes clinical outcomes glucose intervention evidence"),
    ]
    retriever = HybridRetriever(docs, embedder=TinyEmbedder())
    workflow = ClinicalResearchWorkflow(retriever)
    rows = []
    for case in load_cases():
        state = workflow.invoke(case["question"], limit=5)
        ids = [item["document_id"] for item in state.get("results", [])]
        calls = state.get("tool_calls", [])
        expected = set(case.get("expected_source_ids", []))
        rows.append({
            "question": case["question"], "answer": state.get("answer", ""),
            "contexts": [item["excerpt"] for item in state.get("results", [])],
            "reference_answer": case.get("reference_answer", ""),
            "retrieved_ids": ids, "judge": state.get("judge", {}),
            "tool_call_accuracy": float(bool(expected.intersection(ids))) if expected else 1.0,
            "tool_call_efficiency": 1.0 / max(len(calls), 1),
            "agentic_task_success": float(bool(state.get("judge", {}).get("valid", False))),
        })
    output = {"cases": rows, "mean_tool_call_accuracy": sum(r["tool_call_accuracy"] for r in rows) / len(rows),
              "mean_tool_call_efficiency": sum(r["tool_call_efficiency"] for r in rows) / len(rows),
              "mean_agentic_task_success": sum(r["agentic_task_success"] for r in rows) / len(rows),
              "provider_metrics": provider_metrics(rows),
              "note": "Tool-call accuracy/efficiency and researcher→judge task success are deterministic. RAGAS/DeepEval metrics require their configured evaluation LLM."}
    (ROOT / "evaluations" / "results.json").write_text(json.dumps(output, indent=2))
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
