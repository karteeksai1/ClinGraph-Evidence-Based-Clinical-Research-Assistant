"""Offline RAGAS + DeepEval evaluation for ClinGraph.

Usage: python evaluations/evaluate.py
Optional integrations are imported lazily so the API does not require an
evaluation provider or network access at request time.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "ai"))

from app.retrieval import Document, HybridRetriever  # noqa: E402
from app.workflow import ClinicalResearchWorkflow  # noqa: E402


class TinyEmbedder:
    def embed_query(self, text):
        return tuple(float(hash(token) % 101) for token in text.lower().split())[:32]

    embed_document = embed_query


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
        from ragas.metrics import AnswerRelevancy, ContextPrecision, ContextRecall, Faithfulness

        dataset = EvaluationDataset.from_list([
            {"user_input": row["question"], "response": row["answer"],
             "retrieved_contexts": row["contexts"], "reference": row["reference_answer"]}
            for row in rows
        ])
        scored = evaluate(dataset, metrics=[ContextPrecision(), ContextRecall(), Faithfulness(), AnswerRelevancy()])
        result["ragas"] = dict(scored)
    except Exception as exc:
        result["ragas"] = {"status": "not_run", "reason": str(exc)}

    try:
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
