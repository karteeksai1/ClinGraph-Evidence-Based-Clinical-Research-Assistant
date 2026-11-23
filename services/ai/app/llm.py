import logging

logger = logging.getLogger(__name__)


class GroqSynthesizer:
    def __init__(self, api_key: str, model: str):
        self.enabled = bool(api_key)
        self.model = model
        self.client = None
        if self.enabled:
            from groq import Groq

            self.client = Groq(api_key=api_key)

    def synthesize(self, query: str, results: list[dict]) -> str | None:
        if not self.enabled or not self.client or not results:
            return None
        evidence = "\n".join(
            f"[{item['document_id']}] {item['title']} — {item['excerpt']}"
            for item in results
        )
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                temperature=0.1,
                max_tokens=900,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a clinical research evidence synthesizer. "
                            "Use only the supplied evidence. Do not diagnose or prescribe. "
                            "Every factual statement must include one or more source IDs in square brackets. "
                            "Mention uncertainty and conflicting evidence when present."
                        ),
                    },
                    {"role": "user", "content": f"Question: {query}\n\nEvidence:\n{evidence}"},
                ],
            )
            return completion.choices[0].message.content
        except Exception:
            logger.exception("Groq synthesis failed; using grounded local synthesis")
            return None
