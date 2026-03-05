# FinTech Knowledge Assistant

A production-aware RAG (Retrieval-Augmented Generation) system that answers EU payment and financial regulation questions using actual regulatory documents.

Built with **Spring Boot + Spring AI + Ollama + PGVector**.

## What It Does

Upload EU regulation PDFs, and the system will:
- Chunk documents into ~300-token pieces with metadata
- Embed each chunk into 768-dimensional vectors using a local AI model
- Store embeddings in PostgreSQL with PGVector extension
- Answer questions by finding the most relevant chunks and feeding them to a local LLM
- Filter answers by regulation name (e.g., only search PSD2 documents)

## Architecture

```
+--------------------------------------------------+
|             Spring Boot Application               |
|                                                    |
|  +----------------+    +------------------------+ |
|  | Ingestion      |    | RAG Query              | |
|  | Controller     |    | Controller             | |
|  | POST /ingest   |    | GET /rag/ask           | |
|  +-------+--------+    | GET /rag/ask/filtered  | |
|          |             +----------+-------------+ |
|          v                        |               |
|  +----------------+               v               |
|  | Document       |    +------------------------+ |
|  | Ingestion      |    | RAG Retrieval          | |
|  | Service        |    | Service                | |
|  +-------+--------+    +----------+-------------+ |
|          |                        |               |
+----------|------------------------|--------------+
           |                        |
           v                        v
  +------------------+    +------------------+
  |  PostgreSQL +    |    |  Ollama (Local)  |
  |  PGVector        |    |  - llama3.2:3b   |
  |  (Vector Store)  |    |  - nomic-embed   |
  |  Port 5433       |    |  Port 11434      |
  +------------------+    +------------------+
```

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | Spring Boot 3.5.x | REST API, DI, configuration |
| AI Framework | Spring AI 1.1.2 | Embedding, vector store, chat client, RAG advisor |
| Chat Model | llama3.2:3b (via Ollama) | Answer generation from context |
| Embedding Model | nomic-embed-text (via Ollama) | Text to 768-dim vector conversion |
| Vector Store | PostgreSQL + PGVector | Vector similarity search + metadata filtering |
| Index Type | HNSW | Fast approximate nearest neighbor search |

## Regulations Ingested

| Regulation | Chunks | Description |
|-----------|--------|-------------|
| PSD2 Directive (2015/2366) | 379 | Payment Services Directive 2 |
| PSD2 RTS on SCA (2018/389) | 86 | Strong Customer Authentication requirements |
| PSD2 Quick Guide | 11 | Latham & Watkins overview |
| SEPA Regulation (260/2012) | 83 | Single Euro Payments Area |
| MiCA (2023/1114) | 751 | Markets in Crypto-Assets |
| DORA (2022/2554) | 371 | Digital Operational Resilience Act |
| EMD2 (2009/110/EC) | 57 | E-Money Directive |
| AMLD5 (2018/843) | 144 | 5th Anti-Money Laundering Directive |
| AMLD6 (2018/1673) | 42 | 6th Anti-Money Laundering Directive |
| GDPR (2016/679) | 404 | General Data Protection Regulation |
| IFR (2015/751) | 76 | Interchange Fee Regulation |
| **Total** | **2,404** | **11 EU regulations** |

## Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Java JDK | 17 or 21 | `java -version` |
| Maven | 3.9+ | `mvn -version` |
| Docker + Compose | Latest | `docker --version` |

## Quick Start

### 1. Start Infrastructure

```bash
docker compose up -d
docker exec fka-ollama ollama pull llama3.2:3b
docker exec fka-ollama ollama pull nomic-embed-text
```

### 2. Run the Application

```bash
./mvnw spring-boot:run
```

### 3. Ingest a PDF

```bash
curl -X POST http://localhost:8080/api/ingest/pdf \
  -F "file=@docs/regulations/your-document.pdf" \
  -F "regulation=REGULATION_NAME"
```

### 4. Ask Questions

```bash
# Search all documents
curl "http://localhost:8080/api/rag/ask?question=What%20is%20PSD2?"

# Search specific regulation only
curl "http://localhost:8080/api/rag/ask/filtered?question=What%20is%20SCA?&regulation=PSD2"
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ingest/pdf` | Upload and ingest a PDF (multipart: file + regulation name) |
| GET | `/api/rag/ask?question=X` | Ask a question across all documents |
| GET | `/api/rag/ask/filtered?question=X&regulation=Y` | Ask within a specific regulation |

## Project Structure

```
fintech-knowledge-assistant/
├── docker-compose.yml                          # Ollama + PostgreSQL
├── docs/regulations/                           # EU regulation PDFs
├── pom.xml
├── src/main/java/com/fka/
│   ├── FintechKnowledgeAssistantApplication.java
│   ├── config/                                 # Spring AI beans
│   ├── ingestion/
│   │   ├── DocumentIngestionService.java       # PDF → chunks → vectors
│   │   └── IngestionController.java            # POST /api/ingest
│   └── retrieval/
│       ├── RagRetrievalService.java            # Question → answer (RAG)
│       └── RagQueryController.java             # GET /api/rag
├── src/main/resources/
│   ├── application.yaml                        # All configuration
│   └── prompts/
│       └── system-prompt.st                    # LLM system prompt
└── backups/                                    # Database backups
```

## Key Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| LLM | llama3.2:3b (local) | Free, fits 16GB RAM, no API costs |
| Embedding | nomic-embed-text | 768-dim, high quality, runs locally |
| Vector Store | PGVector | Familiar SQL, metadata filtering, Spring AI integration |
| Chunk Size | 300 tokens | Balance precision vs context for dense regulatory text |
| Top-K | 5 | Enough context without overwhelming 3B model |
| Temperature | 0.3 | Factual and deterministic for regulatory Q&A |
| Similarity Threshold | 0.7 | Filters irrelevant chunks |


## License

This project is for educational and portfolio purposes.
