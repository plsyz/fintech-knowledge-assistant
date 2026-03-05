# FinTech Knowledge Assistant

A production-aware RAG (Retrieval-Augmented Generation) system that answers EU payment and financial regulation questions using actual regulatory documents.

Built with **Spring Boot + Spring AI + PGVector**. Supports both **local Ollama models** and **Anthropic Claude API** for chat.

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
  +------------------+    +------------------+    +------------------+
  |  PostgreSQL +    |    |  Ollama (Local)  |    |  Anthropic API   |
  |  PGVector        |    |  - nomic-embed   |    |  - Claude Haiku  |
  |  (Vector Store)  |    |  Port 11434      |    |  (Cloud Chat)    |
  |  Port 5433       |    +------------------+    +------------------+
  +------------------+
```

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | Spring Boot 3.5.x | REST API, DI, configuration |
| AI Framework | Spring AI 1.1.2 | Embedding, vector store, chat client, RAG advisor |
| Chat Model | Claude Haiku (Anthropic API) or llama3.2:3b (Ollama) | Answer generation from context |
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

### Download Links (EUR-Lex)

All regulations are freely available from the official EU law portal. Download the PDFs and place them in `docs/regulations/`:

| Regulation | Download |
|-----------|----------|
| PSD2 Directive | [EUR-Lex 2015/2366](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32015L2366) |
| PSD2 RTS on SCA | [EUR-Lex 2018/389](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32018R0389) |
| SEPA Regulation | [EUR-Lex 260/2012](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32012R0260) |
| MiCA | [EUR-Lex 2023/1114](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32023R1114) |
| DORA | [EUR-Lex 2022/2554](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32022R2554) |
| EMD2 | [EUR-Lex 2009/110/EC](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32009L0110) |
| AMLD5 | [EUR-Lex 2018/843](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32018L0843) |
| AMLD6 | [EUR-Lex 2018/1673](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32018L1673) |
| GDPR | [EUR-Lex 2016/679](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32016R0679) |
| IFR | [EUR-Lex 2015/751](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32015R0751) |

> The PSD2 Quick Guide is a third-party overview by Latham & Watkins, not an official EU document.

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

### 2. Configure the Chat Model

The application supports two chat model backends. Ollama embeddings are always used for vector search regardless of which chat model you choose.

#### Option A: Anthropic Claude API (Recommended — faster)

Create a `.env` file in the project root (this file is gitignored):

```bash
ANTHROPIC_API_KEY=your-api-key-here
```

Then run:

```bash
source .env && ./mvnw spring-boot:run
```

#### Option B: Local Ollama (free, no API key needed)

To switch back to the local Ollama model, make these changes:

1. In `FintechKnowledgeAssistantApplication.java`, remove the `OllamaChatAutoConfiguration` exclusion:
   ```java
   @SpringBootApplication  // remove the (exclude = {...}) part
   ```

2. In `application.yaml`, replace the Anthropic + Ollama config with:
   ```yaml
   spring.ai:
     ollama:
       base-url: http://localhost:11434
       chat:
         options:
           model: llama3.2:3b
           temperature: 0.3
       embedding:
         options:
           model: nomic-embed-text
   ```

3. Remove or comment out the `spring.ai.anthropic` section.

> **Note:** The local Ollama model runs on CPU and is significantly slower (~1-3 min per query on most machines). The Anthropic API returns answers in 2-5 seconds.
>
> For detailed step-by-step switching instructions, see [SWITCHING-CHAT-MODELS.md](SWITCHING-CHAT-MODELS.md).

### 3. Run the Application

```bash
# With Anthropic (load .env first)
source .env && ./mvnw spring-boot:run

# With Ollama (no .env needed)
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
| Chat LLM | Claude Haiku (API) / llama3.2:3b (local) | API is fast (~3s); local is free but slow on CPU |
| Embedding | nomic-embed-text (local Ollama) | 768-dim, high quality, always runs locally |
| Vector Store | PGVector | Familiar SQL, metadata filtering, Spring AI integration |
| Chunk Size | 300 tokens | Balance precision vs context for dense regulatory text |
| Top-K | 10 | Enough context for comprehensive regulatory answers |
| Temperature | 0.3 | Factual and deterministic for regulatory Q&A |
| Similarity Threshold | 0.2 | Permissive — lets the LLM judge relevance from more candidates |


## License

This project is for educational and portfolio purposes.
