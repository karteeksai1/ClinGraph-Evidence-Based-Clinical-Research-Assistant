"use client";

import { FormEvent, useState } from "react";
import { askResearchQuestion, ResearchResponse } from "../lib/api";

const examples = [
  "What are the latest evidence-based interventions for hypertension?",
  "What outcomes are reported for GLP-1 therapies in type 2 diabetes?",
  "Compare clinical trials for immune checkpoint inhibitors."
];

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
    <main className="min-h-screen overflow-hidden bg-[#f8f7ff] py-0 text-[#17152d]">
      <div className="pointer-events-none fixed -left-24 -top-24 h-72 w-72 rounded-full bg-pink-200/60 blur-3xl" />
      <div className="pointer-events-none fixed -right-24 top-24 h-96 w-96 rounded-full bg-blue-200/60 blur-3xl" />

      <nav className="relative mx-auto flex max-w-7xl items-center justify-between px-6 py-6 lg:px-10">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-pink-500 to-blue-500 text-lg font-black text-white shadow-lg shadow-pink-200">C</div>
          <div><p className="text-sm font-black tracking-[0.18em] text-[#17152d]">CLINGRAPH</p><p className="text-xs text-slate-500">Evidence intelligence</p></div>
        </div>
        <div className="hidden items-center gap-8 text-sm font-semibold text-slate-500 sm:flex"><span className="text-[#17152d]">Research</span><span>Sources</span><span>About</span></div>
        <span className="rounded-full border border-blue-200 bg-white/70 px-3 py-1.5 text-xs font-bold text-blue-600">Personal workspace</span>
      </nav>

      <div className="relative mx-auto grid max-w-7xl gap-8 px-6 pb-20 pt-10 lg:grid-cols-[1fr_360px] lg:px-10 lg:pt-20">
        <section>
          <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-pink-200 bg-white/70 px-3 py-1.5 text-xs font-bold text-pink-600 shadow-sm"><span className="h-2 w-2 rounded-full bg-pink-500" /> Grounded clinical research</div>
          <h1 className="max-w-3xl text-5xl font-black leading-[0.98] tracking-[-0.055em] text-[#17152d] sm:text-7xl">Find the signal<br /><span className="bg-gradient-to-r from-pink-500 via-fuchsia-500 to-blue-600 bg-clip-text text-transparent">inside the evidence.</span></h1>
          <p className="mt-7 max-w-2xl text-lg leading-8 text-slate-600">Ask a clinical research question. ClinGraph searches biomedical literature and clinical trials, then keeps every conclusion tied to its sources.</p>

          <form onSubmit={submit} className="mt-10 rounded-[28px] border border-white bg-white/85 p-3 shadow-[0_24px_80px_rgba(88,72,160,0.15)] backdrop-blur">
            <textarea value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ask about a condition, intervention, outcome, or trial…" rows={4} className="w-full resize-none rounded-2xl bg-transparent px-4 py-3 text-lg text-[#17152d] outline-none placeholder:text-slate-400" />
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 px-3 pt-3"><span className="text-xs font-medium text-slate-400">Answers are research support, not medical advice.</span><button disabled={loading} className="rounded-2xl bg-gradient-to-r from-pink-500 to-blue-500 px-6 py-3 font-extrabold text-white shadow-lg shadow-blue-200 transition hover:-translate-y-0.5 disabled:cursor-wait disabled:opacity-50">{loading ? "Searching evidence…" : "Start research →"}</button></div>
          </form>

          <div className="mt-6 flex flex-wrap gap-2">{examples.map((example) => <button key={example} onClick={() => setQuery(example)} className="rounded-full border border-slate-200 bg-white/65 px-3 py-2 text-left text-xs font-semibold text-slate-500 transition hover:border-pink-300 hover:text-pink-600">{example}</button>)}</div>

          {error && <p className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p>}

          {result && <section className="mt-10 rounded-[28px] border border-white bg-white/90 p-6 shadow-[0_24px_80px_rgba(88,72,160,0.12)]">
            <div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-[0.16em] text-blue-500">Research brief</p><h2 className="mt-2 text-2xl font-black tracking-tight">Evidence summary</h2></div><span className="rounded-full bg-blue-50 px-3 py-1.5 text-xs font-bold text-blue-600">{result.confidence}</span></div>
            <p className="mt-6 whitespace-pre-wrap border-l-4 border-pink-300 pl-4 text-[15px] leading-8 text-slate-700">{result.answer}</p>
            <div className="mt-8 flex items-center justify-between"><h3 className="text-sm font-black uppercase tracking-[0.14em] text-slate-500">Retrieved sources</h3><span className="text-xs font-semibold text-slate-400">{result.results.length} sources</span></div>
            <div className="mt-3 space-y-3">{result.results.map((source, index) => <article key={source.document_id} className="rounded-2xl border border-slate-100 bg-gradient-to-r from-white to-blue-50/40 p-4 transition hover:border-pink-200">
              <div className="flex gap-3"><span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-pink-100 text-xs font-black text-pink-600">{String(index + 1).padStart(2, "0")}</span><div className="min-w-0 flex-1"><div className="flex flex-wrap justify-between gap-2"><strong className="text-sm leading-6 text-[#17152d]">{source.title}</strong><span className="text-[11px] font-bold uppercase tracking-wide text-blue-500">{source.source}</span></div><p className="mt-2 text-sm leading-6 text-slate-500">{source.excerpt}</p><div className="mt-3 flex items-center justify-between"><span className="text-[11px] font-semibold text-slate-400">Hybrid relevance {source.hybrid_score.toFixed(2)}</span>{source.url && <a href={source.url} target="_blank" rel="noreferrer" className="text-xs font-bold text-pink-600 hover:text-blue-600">Open source ↗</a>}</div></div></div>
            </article>)}</div>
          </section>}
        </section>

        <aside className="space-y-4 lg:pt-24">
          <div className="rounded-[28px] border border-white bg-white/75 p-6 shadow-[0_20px_60px_rgba(88,72,160,0.1)] backdrop-blur"><p className="text-xs font-black uppercase tracking-[0.16em] text-pink-500">How it works</p><div className="mt-5 space-y-5"><Step number="01" title="Ask" text="Describe the clinical question in plain language." color="pink" /><Step number="02" title="Retrieve" text="Blend BM25 relevance with local dense embeddings." color="blue" /><Step number="03" title="Ground" text="Review source excerpts and citations before trusting a conclusion." color="violet" /></div></div>
          <div className="rounded-[28px] bg-gradient-to-br from-[#20204d] to-[#353b89] p-6 text-white shadow-[0_20px_60px_rgba(47,49,125,0.25)]"><p className="text-xs font-black uppercase tracking-[0.16em] text-pink-200">Connected sources</p><div className="mt-5 space-y-3 text-sm"><SourcePill name="PubMed" detail="Biomedical literature" /><SourcePill name="ClinicalTrials.gov" detail="Registered studies" /><SourcePill name="Pinecone" detail="Dense evidence retrieval" /></div></div>
        </aside>
      </div>
    </main>
  );
}

function Step({ number, title, text, color }: { number: string; title: string; text: string; color: "pink" | "blue" | "violet" }) {
  const styles = { pink: "bg-pink-100 text-pink-600", blue: "bg-blue-100 text-blue-600", violet: "bg-violet-100 text-violet-600" };
  return <div className="flex gap-3"><span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-[10px] font-black ${styles[color]}`}>{number}</span><div><p className="font-extrabold text-[#17152d]">{title}</p><p className="mt-1 text-sm leading-6 text-slate-500">{text}</p></div></div>;
}

function SourcePill({ name, detail }: { name: string; detail: string }) {
  return <div className="flex items-center justify-between rounded-2xl bg-white/10 px-3 py-3"><span className="font-bold">{name}</span><span className="text-xs text-blue-100">{detail}</span></div>;
}
