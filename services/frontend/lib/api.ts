export type SearchResult = {
  document_id: string;
  title: string;
  excerpt: string;
  source: string;
  url?: string;
  publication_date?: string;
  bm25_score: number;
  dense_score: number;
  hybrid_score: number;
};

export type ResearchResponse = {
  query: string;
  answer: string;
  claims: string[];
  citations: string[];
  confidence: string;
  results: SearchResult[];
};

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export async function askResearchQuestion(query: string): Promise<ResearchResponse> {
  const response = await fetch(`${backendUrl}/api/v1/research`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, limit: 10 })
  });
  if (!response.ok) throw new Error("The research service is unavailable.");
  return response.json();
}
