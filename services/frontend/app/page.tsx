"use client";

import { FormEvent, useState } from "react";
import { askResearchQuestion, ResearchResponse } from "../lib/api";

export default function Home() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<ResearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;
    setLoading(true); setError("");
    try { setResult(await askResearchQuestion(query)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Request failed"); }
    finally { setLoading(false); }
  }

  return (
    <main className="shell">
      <header><p className="eyebrow">CLINGRAPH</p><h1>Evidence, connected.</h1><p className="subtitle">Ask a clinical research question and inspect the sources behind the answer.</p></header>
      <form onSubmit={submit} className="searchBox">
        <textarea value={query} onChange={(event) => setQuery(event.target.value)} placeholder="What does the evidence say about..." rows={4} />
        <button disabled={loading}>{loading ? "Researching…" : "Research"}</button>
      </form>
      {error && <p className="error">{error}</p>}
      {result && <section className="results">
        <div className="resultHeader"><h2>Research summary</h2><span>{result.confidence}</span></div>
        <p className="answer">{result.answer}</p>
        <h3>Sources</h3>
        {result.results.map((source) => <article key={source.document_id} className="source">
          <div><strong>{source.title}</strong><small>{source.source} · hybrid score {source.hybrid_score.toFixed(2)}</small></div>
          <p>{source.excerpt}</p>
          {source.url && <a href={source.url} target="_blank" rel="noreferrer">Open source →</a>}
        </article>)}
      </section>}
    </main>
  );
}
