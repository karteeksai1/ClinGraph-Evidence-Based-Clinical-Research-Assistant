# Evaluation status

ClinGraph does not currently use Ragas or DeepEval. The application has retrieval and citation verification logic, but it does not yet calculate automated RAG quality metrics.

## Planned evaluation layer

Add a small, versioned evaluation dataset with:

- user question;
- expected source IDs;
- reference answer or reference claims;
- retrieved contexts;
- generated answer;
- human review label.

Then measure:

- **Ragas:** context precision, context recall, faithfulness, and answer relevancy.
- **DeepEval:** answer relevancy, faithfulness, contextual relevancy, and custom citation coverage.

These should run as offline evaluation commands against saved datasets, not during normal user requests. They are intentionally not dependencies of the runtime services yet.
