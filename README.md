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
7. Users can inspect the evidence graph for relationships between studies, interventions, conditions, outcomes, and claims.
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
                         | Search | Chat | Graph|
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
                  | BM25       | | Dense      | | Knowledge     |
                  | Search     | | Search     | | Graph         |
                  | OpenSearch | | pgvector   | | Neo4j         |
                  +------+-----+ +-----+------+ +----+----------+
                         |             |             |
                         +-------------v-------------+
                          Evidence & Citation Layer
                         +-------------+-------------+
                                       |
                         +-------------v-------------+
                         | PostgreSQL                |
                         | Sources | Claims | Studies |
                         | Citations | Users | Audits |
                         +-------------+-------------+
                                       |
                         +-------------v-------------+
                         | Document Processing        |
                         | PDF/XML | Chunking | NER    |
                         | Embeddings | Entity links  |
                         +-------------+-------------+
                                       |
       +-------------------------------v------------------------------+
       | External Evidence Sources                                    |
       | PubMed | Europe PMC | ClinicalTrials.gov | Guidelines        |
       +--------------------------------------------------------------+
```

### Main components

- **Web application:** React/Next.js interface for search, conversational research, study comparison, citations, and graph exploration.
- **Backend service:** FastAPI public API providing authentication, authorization, rate limiting, request validation, and the frontend-facing contract.
- **AI service:** LangGraph workflow that decomposes questions, coordinates retrieval, synthesizes answers, and validates citations.
- **Evidence database:** PostgreSQL stores users, sources, studies, claims, citations, entities, processing status, and audit records.
- **Hybrid search:** Combine BM25 lexical scores from OpenSearch/Elasticsearch with dense-vector similarity from PostgreSQL `pgvector`. Apply metadata filters before weighted score fusion and reranking.
- **Knowledge graph:** Neo4j stores relationships such as `Study evaluates Intervention`, `Study reports Outcome`, and `Paper supports Claim`.
- **Document pipeline:** Downloads source documents, extracts text and tables, chunks content, detects entities, generates embeddings, and links evidence to canonical records.
- **Object storage:** S3-compatible storage for PDFs, XML, extracted tables, and processing artifacts.
- **Background processing:** Celery/RQ with Redis for the MVP, or Temporal when workflows require durable orchestration and compensation.
- **LLM layer:** Use separate model tasks for query planning, information extraction, synthesis, and citation/contradiction verification.

### Query flow

```text
User question
    -> query planning and medical entity extraction
    -> BM25 search + dense-vector search + graph traversal
    -> evidence filtering and reranking
    -> claim extraction
    -> answer synthesis
    -> citation and contradiction verification
    -> answer with source-level citations
```

### Initial technology recommendation

For the MVP, use Next.js, FastAPI, PostgreSQL with `pgvector`, Redis-based background jobs, S3-compatible object storage, and PubMed/ClinicalTrials.gov connectors. Use OpenSearch for BM25 retrieval and add Neo4j when graph use cases justify the operational complexity.

### Suggested repository structure

```text
clinGraph/
├── services/
│   ├── frontend/       # Next.js web application
│   ├── backend/        # Public FastAPI API and service boundary
│   └── ai/             # LangGraph, retrieval, synthesis, ingestion
├── packages/
│   └── contracts/      # Shared API contract
├── docker-compose.yml
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

The services are independently runnable:

```bash
# Run all three services
docker compose up --build

# Or run them separately
make ai        # AI service on :8001
make backend   # Backend API on :8000
make frontend  # Next.js UI on :3000
```

The frontend calls only the backend. The backend owns the public API and forwards research, search, and ingestion requests to the AI service. The AI service owns LangGraph, BM25+dense retrieval, source connectors, and evidence synthesis. Dense embeddings run locally through Sentence Transformers using `sentence-transformers/all-MiniLM-L6-v2`; no Hugging Face API key is required. The current corpus is in memory; replace it with Pinecone and Neon persistence when deploying at scale.
