# ClinGraph — Evidence-Based Clinical Research Assistant

ClinGraph is a clinical research assistant that helps users discover, connect, compare, and summarize medical evidence while preserving source-level citations and provenance.

## Initial requirements

### Product goals

- Help researchers find relevant clinical studies, papers, trials, and guidelines.
- Answer research questions using retrieved evidence rather than unsupported model memory.
- Show the source passage, publication metadata, and citation behind every important claim.
- Connect clinical concepts such as conditions, interventions, outcomes, studies, and patient populations.
- Surface contradictory findings, limitations, and evidence quality.
- Keep research assistance separate from diagnosis or personalized treatment advice.

### MVP functional requirements

1. Users can submit natural-language clinical research questions.
2. Users can search biomedical literature using hybrid BM25 and dense-vector retrieval.
3. The system can ingest metadata and abstracts from PubMed/Europe PMC and trial data from ClinicalTrials.gov.
4. The system can parse documents into searchable chunks and generate embeddings.
5. The system can retrieve and rank evidence using hybrid search:
   - BM25 lexical relevance scoring;
   - dense-vector semantic similarity;
   - metadata filters such as date, study type, condition, and intervention.
6. The system can generate a structured answer with:
   - concise conclusion;
   - supporting findings;
   - limitations and conflicting evidence;
   - inline citations;
   - linked source documents.
7. Users can inspect retrieved sources, metadata, evidence excerpts, and citation links.
8. The system records source provenance, retrieval context, and answer-generation audit data.

### Non-functional requirements

- **Traceability:** Each generated claim must map to one or more source passages.
- **Reliability:** Failed ingestion and processing jobs must be retryable and observable.
- **Security:** Use authentication, role-based access control, encryption in transit and at rest, and audit logs.
- **Privacy:** Do not use patient-identifiable information in the MVP. Add de-identification before accepting clinical records.
- **Performance:** Return initial search results within a few seconds for a normal query; stream longer synthesis responses when possible.
- **Extensibility:** Support additional sources, ontologies, rerankers, and language models without changing the core API.
- **Safety:** Clearly label the product as a research assistant, not a diagnostic or treatment system.

### MVP boundaries

The first release should focus on literature and trial research. It should not make patient-specific diagnoses, recommend treatment, replace clinician judgment, or ingest protected health information.

## Architecture

```text
                         +--------------------+
                         |   Web Application   |
                         | Search | Research | Sources |
                         +----------+---------+
                                    |
                         +----------v---------+
                         | Backend API Service |
                         | Auth | API | Proxy  |
                         +----------+---------+
                                    |
              +---------------------v---------------------+
              |              AI Service                  |
              | Query planning | Retrieval | Synthesis    |
              | Citation validation | Confidence scoring |
              +----------+-------------+-------------+----+
                         |             |             |
                  +------v-----+ +-----v------+ +----v----------+
                  | BM25       | | Dense      | | Metadata    |
                  | Search     | | Search     | | Database    |
                  | BM25 local | | Pinecone   | | Neon        |
                  +------+-----+ +-----+------+ +----+----------+
                         |             |             |
                         +-------------v-------------+
                          Evidence & Citation Layer
                         +-------------+-------------+
                                       |
                         +-------------v-------------+
                         | Neon PostgreSQL            |
                         | Documents | Sources | Audit |
                         | Metadata | Citations       |
                         +-------------+-------------+
                                       |
                         +-------------v-------------+
                         | Local Embeddings + Groq   |
                         | Sentence Transformers     |
                         | Grounded synthesis        |
                         +-------------+-------------+
                                       |
       +-------------------------------v------------------------------+
       | External Evidence Sources                                    |
       | PubMed | Europe PMC | ClinicalTrials.gov | Guidelines        |
       +--------------------------------------------------------------+
```

### Main components

- **Web application:** Next.js + Tailwind interface for research questions, evidence summaries, and source inspection.
- **Backend service:** FastAPI public API and service boundary. Authentication and production authorization are intentionally deferred for this personal project.
- **AI service:** LangGraph workflow that decomposes questions, coordinates retrieval, synthesizes answers, and validates citations.
- **Metadata database:** Neon PostgreSQL stores evidence document metadata and source provenance through SQLAlchemy.
- **Hybrid search:** Combine local BM25 lexical scores with dense-vector similarity from Pinecone. If Pinecone is unavailable, local cosine similarity is used.
- **Embedding layer:** Sentence Transformers runs `all-MiniLM-L6-v2` locally and produces 384-dimensional vectors.
- **LLM layer:** Groq performs grounded answer synthesis; a deterministic local synthesis fallback keeps development possible without a Groq key.
- **Evidence connectors:** PubMed/NCBI and ClinicalTrials.gov are selected as the initial sources.
- **Redis:** Reserved for cache and queue integration; background ingestion is synchronous in the current MVP.

### Query flow

```text
User question
    -> query planning and medical entity extraction
    -> BM25 search + Pinecone dense-vector search
    -> evidence filtering and reranking
    -> claim extraction
    -> answer synthesis
    -> citation and contradiction verification
    -> answer with source-level citations
```

### Initial technology recommendation

For this personal project, use Next.js with Tailwind, FastAPI, local Sentence Transformers, Groq, Pinecone, Neon PostgreSQL, Redis, and PubMed/ClinicalTrials.gov connectors. No Docker, deployment platform, graph database, object storage, observability stack, or production authentication is included at this stage.

### Suggested repository structure

```text
clinGraph/
├── services/
│   ├── frontend/       # Next.js web application
│   ├── backend/        # Public FastAPI API and service boundary
│   └── ai/             # LangGraph, retrieval, synthesis, ingestion
├── packages/
│   └── contracts/      # Shared API contract
├── Makefile
├── .env.example
└── README.md
```

### Clinical safety principles

- The LLM synthesizes retrieved evidence; it is not the source of truth.
- Every material claim must link to a source passage.
- Show publication date, study type, sample size, and evidence quality where available.
- Preserve and display conflicting findings instead of silently resolving them.
- Log searches, retrieved sources, prompts, model versions, and generated answers.
- Add human review workflows before supporting any patient-specific or clinical-decision use case.

## Local development

The services are independently runnable from separate terminal windows:

```bash
# Install dependencies once
make install

# Terminal 1: AI service on :8001
make ai

# Terminal 2: Backend API on :8000
make backend

# Terminal 3: Next.js UI on :3000
make frontend
```

The frontend calls only the backend. The backend owns the public API and forwards research, search, and ingestion requests to the AI service. The AI service owns LangGraph, local embeddings, Groq synthesis, BM25+dense retrieval, Pinecone vector persistence, Neon metadata persistence, Redis configuration, source connectors, and evidence synthesis. Dense embeddings run locally through Sentence Transformers using `sentence-transformers/all-MiniLM-L6-v2`; no Hugging Face API key is required. Pinecone and Neon gracefully fall back to local in-memory behavior when their connection settings are absent or unavailable.
