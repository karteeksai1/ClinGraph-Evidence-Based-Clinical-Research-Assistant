import logging
import json

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
                    {"role": "system", "content": (
                        "You are a clinical research evidence synthesizer. Use only the supplied evidence. "
                        "Do not diagnose or prescribe. Every factual statement must include source IDs in square brackets. "
                        "Mention uncertainty and conflicting evidence when present."
                    )},
                    {"role": "user", "content": f"Question: {query}\n\nEvidence:\n{evidence}"},
                ],
            )
            return completion.choices[0].message.content
        except Exception:
            logger.exception("Groq synthesis failed; using grounded local synthesis")
            return None

    def judge(self, query: str, answer: str, results: list[dict]) -> dict | None:
        """Second-agent verification pass. Returns structured JSON when Groq is enabled."""
        if not self.enabled or not self.client:
            return None
        evidence = "\n".join(f"[{item['document_id']}] {item['excerpt']}" for item in results)
        try:
            completion = self.client.chat.completions.create(
                model=self.model, temperature=0, max_tokens=500,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a strict clinical evidence judge. Check whether the answer is supported only by the supplied excerpts and has citations. Return JSON with valid (boolean), score (0-1), issues (array of strings), and corrected_answer (string). Do not add medical advice."},
                    {"role": "user", "content": f"Question: {query}\nAnswer: {answer}\nEvidence:\n{evidence}"},
                ],
            )
            value = json.loads(completion.choices[0].message.content or "{}")
            return value if isinstance(value, dict) else None
        except Exception:
            logger.exception("Groq judge failed; using deterministic citation judge")
            return None
