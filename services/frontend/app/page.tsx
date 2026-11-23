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
    setLoading(true);
    setError("");
    try { setResult(await askResearchQuestion(query)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Request failed"); }
    finally { setLoading(false); }
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_right,_#1b3552,_#0b1020_45%)] px-5 py-18 text-slate-100">
      <div className="mx-auto max-w-4xl">
        <header>
          <p className="text-xs font-bold tracking-[0.2em] text-emerald-300">CLINGRAPH</p>
          <h1 className="mt-6 max-w-3xl text-6xl font-semibold leading-[0.95] tracking-tight sm:text-8xl">Evidence, connected.</h1>
          <p className="mt-5 max-w-2xl text-xl leading-8 text-slate-400">Ask a clinical research question and inspect the sources behind the answer.</p>
        </header>
        <form onSubmit={submit} className="mt-10 rounded-2xl border border-slate-700 bg-slate-900/85 p-5 shadow-2xl">
          <textarea value={query} onChange={(event) => setQuery(event.target.value)} placeholder="What does the evidence say about…" rows={4} className="w-full resize-y border-0 bg-transparent text-lg text-slate-100 outline-none placeholder:text-slate-500" />
          <button disabled={loading} className="mt-4 rounded-full bg-emerald-300 px-5 py-3 font-extrabold text-emerald-950 transition hover:bg-emerald-200 disabled:cursor-wait disabled:opacity-50">{loading ? "Researching…" : "Research"}</button>
        </form>
        {error && <p className="mt-5 text-red-300">{error}</p>}
        {result && <section className="mt-8 rounded-2xl border border-slate-700 bg-slate-900/85 p-5 shadow-2xl">
          <div className="flex flex-wrap items-center justify-between gap-4"><h2 className="text-2xl font-semibold">Research summary</h2><span className="text-xs text-slate-400">{result.confidence}</span></div>
          <p className="mt-5 whitespace-pre-wrap leading-7 text-slate-300">{result.answer}</p>
          <h3 className="mt-8 text-lg font-semibold">Sources</h3>
          {result.results.map((source) => <article key={source.document_id} className="border-t border-slate-700 py-5">
            <div className="flex flex-wrap justify-between gap-3"><strong>{source.title}</strong><small className="text-slate-500">{source.source} · hybrid {source.hybrid_score.toFixed(2)}</small></div>
            <p className="mt-3 leading-6 text-slate-400">{source.excerpt}</p>
            {source.url && <a href={source.url} target="_blank" rel="noreferrer" className="text-sm text-emerald-300 hover:text-emerald-200">Open source →</a>}
          </article>)}
        </section>}
      </div>
    </main>
  );
}
