# Switching Chat Models: Ollama ↔ Anthropic Claude API

This guide explains how to switch the chat model backend between a **local Ollama model** and the **Anthropic Claude API**.

> **Important:** Only the **chat model** changes. The **embedding model** (nomic-embed-text via Ollama) always stays local — your vector store and document embeddings are unaffected by this switch.

---

## Current Default: Anthropic Claude API

The app is currently configured to use **Claude Haiku 4.5** via the Anthropic API for chat. This gives ~2-5 second response times.

---

## How to Switch to Anthropic Claude API (from Ollama)

### Step 1: Get an API Key

Sign up at [console.anthropic.com](https://console.anthropic.com) and create an API key.

### Step 2: Create a `.env` File

Create a `.env` file in the project root (it's already gitignored — your key will never be committed):

```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx-your-key-here
```

### Step 3: Update `pom.xml`

Add the Anthropic starter dependency (keep the Ollama one for embeddings):

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-model-anthropic</artifactId>
</dependency>
```

### Step 4: Update `application.yaml`

Replace the `spring.ai` section:

```yaml
spring:
  ai:
    anthropic:
      api-key: ${ANTHROPIC_API_KEY}
      chat:
        options:
          model: claude-haiku-4-5-20251001
          temperature: 0.3
          max-tokens: 1024
    ollama:
      base-url: http://localhost:11434
      chat:
        enabled: false       # Disable Ollama chat, keep embeddings only
      embedding:
        options:
          model: nomic-embed-text
```

### Step 5: Exclude Ollama Chat Auto-Configuration

In `FintechKnowledgeAssistantApplication.java`, exclude the Ollama chat bean to prevent a "two ChatModel beans found" conflict:

```java
import org.springframework.ai.model.ollama.autoconfigure.OllamaChatAutoConfiguration;

@SpringBootApplication(exclude = { OllamaChatAutoConfiguration.class })
public class FintechKnowledgeAssistantApplication {
    // ...
}
```

### Step 6: Run

```bash
source .env && ./mvnw spring-boot:run
```

---

## How to Switch Back to Local Ollama (from Anthropic)

### Step 1: Update `application.yaml`

Replace the `spring.ai` section:

```yaml
spring:
  ai:
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

Remove the entire `spring.ai.anthropic` block.

### Step 2: Remove the Exclusion

In `FintechKnowledgeAssistantApplication.java`, revert to the simple annotation:

```java
@SpringBootApplication   // no exclude needed
public class FintechKnowledgeAssistantApplication {
    // ...
}
```

### Step 3: (Optional) Remove Anthropic Dependency

You can remove this from `pom.xml` if you no longer need it:

```xml
<!-- Remove this -->
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-model-anthropic</artifactId>
</dependency>
```

### Step 4: Run

No `.env` needed for Ollama:

```bash
./mvnw spring-boot:run
```

---

## RAG Search Parameter Tuning (Important!)

When we switched from Ollama to Anthropic, the RAG pipeline returned empty results — the LLM kept saying "no documents were provided." The fix involved tuning two parameters in `RagRetrievalService.java`:

### What Changed and Why

| Parameter | Old Value (Ollama) | New Value (Anthropic) | Why |
|-----------|-------------------|----------------------|-----|
| `topK` | 5 | **10** | Claude Haiku is smarter at filtering irrelevant context, so giving it more chunks produces better answers |
| `similarityThreshold` | 0.7 | **0.2** | `nomic-embed-text` cosine similarity scores tend to be lower than you'd expect — 0.7 was filtering out almost everything |

### Where to Change

In `src/main/java/com/fka/retrieval/RagRetrievalService.java`:

```java
.searchRequest(SearchRequest.builder()
        .topK(10)             // Number of chunks to retrieve
        .similarityThreshold(0.2) // Minimum cosine similarity score
        .build())
```

### Recommended Values by Model

| Setting | Ollama (llama3.2:3b) | Anthropic Claude |
|---------|---------------------|-----------------|
| `topK` | 5-7 (small context window on 3B model) | 10-15 (handles large context well) |
| `similarityThreshold` | 0.2 | 0.2 |
| `max-tokens` | N/A (controlled by model) | 1024 (set in application.yaml) |

> **Key lesson:** If the LLM says "no context/documents provided" but you know data is ingested, the problem is almost always `similarityThreshold` being too high. Start low (0.2) and increase only if you're getting too many irrelevant results.

---

## Comparison

| Aspect | Ollama (Local) | Anthropic Claude API |
|--------|---------------|---------------------|
| **Speed** | ~1-3 min/query (CPU) | ~2-5 sec/query |
| **Cost** | Free | Pay per token |
| **Privacy** | All data stays local | Queries sent to Anthropic |
| **Setup** | Pull model via Docker | API key in `.env` |
| **Quality** | Good for simple queries | Better reasoning, formatting |
| **GPU** | Much faster with GPU | N/A (cloud) |

---

## Troubleshooting

### "expected single matching bean but found 2: anthropicChatModel, ollamaChatModel"

You have both starters but didn't exclude the Ollama chat config. Add the `@SpringBootApplication(exclude = { OllamaChatAutoConfiguration.class })` annotation. See Step 5 above.

### "Could not resolve placeholder 'ANTHROPIC_API_KEY'"

The `.env` file wasn't loaded. Make sure to run `source .env` before starting the app, or set the variable directly:

```bash
export ANTHROPIC_API_KEY=sk-ant-xxxxx
./mvnw spring-boot:run
```

### Responses say "no context documents were supplied" or "not enough information"

This was the #1 issue we hit during the switch. The root cause: `similarityThreshold` was set to `0.7`, which filtered out nearly all chunks because `nomic-embed-text` cosine scores are naturally lower.

**Fix:** In `RagRetrievalService.java`, make sure:
```java
.topK(10)
.similarityThreshold(0.2)
```

You can verify data exists by querying the database directly:
```bash
docker exec fka-postgres psql -U fka_user fka_vectorstore -c "SELECT COUNT(*) FROM vector_store;"
```

If the count is > 0 but the LLM still says "no documents," the threshold is the problem.

### Responses are slow even with Anthropic API

Make sure Ollama chat is disabled (`chat.enabled: false` in yaml) and the `OllamaChatAutoConfiguration` is excluded. If both chat models are active, Spring may route to the wrong one.

### Application starts but queries return 404

The correct endpoints are:
- `GET /api/rag/ask?question=...`
- `GET /api/rag/ask/filtered?question=...&regulation=...`

(Not `/api/query` — that doesn't exist.)
