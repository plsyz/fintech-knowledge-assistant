# Knowledge-assistant evaluation runbook

End-to-end procedure for producing the results in `eval/`. Run this **after** stopping the
`finstream-ai` stack (`docker compose down` there), since both projects publish the same ports.

## 0. Requirements

| Item | Check |
|---|---|
| Docker Desktop with ≥ 6 GB RAM | `docker info \| grep -i memory` |
| JDK 17+, Maven 3.9+ | `java -version` |
| Python 3.10+ | `python3 --version` |
| `ANTHROPIC_API_KEY` in `.env` | `cat .env` |
| The 11 regulation PDFs ingested (2,404 chunks) | see step 2 |

Budget: 125 questions × 3 conditions = 375 answer calls (+125 entity-extraction calls in
graph-rag) with Haiku 4.5, plus 375 judge calls with a stronger model ≈ **USD 5–10**.
Wall time ≈ 30–45 min.

## 1. Infrastructure

```bash
cd fintech-knowledge-assistant
docker compose up -d
docker compose ps
docker exec fka-ollama ollama pull nomic-embed-text
curl -s http://localhost:11434/api/tags
docker exec fka-postgres pg_isready -U fka_user
```

## 2. Corpus check (and re-ingest if the volume is empty)

```bash
docker exec fka-postgres psql -U fka_user -d fka_vectorstore \
  -c "select metadata->>'regulation' as regulation, count(*) from vector_store group by 1 order by 1;"
```

Expected ≈ 2,404 rows across the 11 regulations. **Note the exact `regulation` tags printed**:
the gold set uses `PSD2, SCA-RTS, SEPA, MICA, DORA, EMD2, AMLD5, AMLD6, GDPR, IFR`. If the
ingested tags differ (e.g. `PSD2_RTS` instead of `SCA-RTS`), add them to
`eval/data/regulation_aliases.json` under the matching canonical id, and set `regulation`
in `eval/build_gold_set.py`'s `REG_ALIASES` accordingly, so that "regulation cited" and the
retrieval check match.

If the table is empty, download the PDFs from the EUR-Lex links in `README.md` into
`docs/regulations/` and ingest with the canonical tags, for example:

```bash
export $(cat .env | xargs) && ./mvnw spring-boot:run &   # app must be running for ingestion
for pair in "psd2.pdf:PSD2" "psd2-rts-sca.pdf:SCA-RTS" "sepa-260-2012.pdf:SEPA" "mica.pdf:MICA" \
            "dora.pdf:DORA" "emd2.pdf:EMD2" "amld5.pdf:AMLD5" "amld6.pdf:AMLD6" "gdpr.pdf:GDPR" "ifr.pdf:IFR"; do
  f=${pair%%:*}; tag=${pair##*:}
  curl -s -X POST http://localhost:8081/api/ingest/pdf -F "file=@docs/regulations/$f" -F "regulation=$tag"; echo
done
```

Ingestion embeds every chunk through Ollama on CPU: expect 10–30 minutes for the full corpus.

## 3. Application (eval endpoints on)

```bash
export $(cat .env | xargs)
export FKA_EVAL_ENABLED=true
./mvnw spring-boot:run
```

Then:

```bash
curl -s "http://localhost:8081/api/eval/search?question=contactless%20payment%20exemption&topK=3" | head -c 600
curl -s "http://localhost:8081/api/eval/ask/no-retrieval?question=What%20is%20the%20GDPR%20breach%20notification%20deadline" | head -c 400
```

A `404` means `FKA_EVAL_ENABLED` was not exported before starting the app.

## 4. Gold set, retrieval check, answers, judging

```bash
cd eval
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python build_gold_set.py                 # prints the medium-confidence items to verify on EUR-Lex
python run_eval.py --check-retrieval     # which gold passages the corpus actually surfaces
```

Open `results/retrieval_check.jsonl`: items with `"hit_at_15": false` either have a hint phrased
differently from the PDF text or a genuinely weak retrieval case — inspect a few via
`/api/eval/search` and adjust `passage_hint` in `build_gold_set.py` only where the phrasing is the
problem (do not tune hints to make retrieval look better; record such edits in the report).

```bash
python run_eval.py --limit 5             # smoke test, all three conditions
export ANTHROPIC_API_KEY=...             # same key is fine; the judge model differs from the model under test
python judge.py --judge-model claude-sonnet-4-5
python analyze.py
rm -rf results/answers_* results/judged_*   # discard smoke run (keep retrieval_check.jsonl)
python run_eval.py                       # full: vector, graph-rag, no-retrieval
python judge.py --judge-model claude-sonnet-4-5
python analyze.py
```

The judge model must differ from the model under test (Haiku 4.5 in `application.yaml`).
If the model id is rejected, pass any current Sonnet/Opus id via `--judge-model`.

## 5. What to look at first

* §3 contamination: share of questions solved closed-book, and retrieval-dependent accuracy.
* §2 abstention on the 20 unanswerable questions, by reason (false-premise questions are the hardest).
* §1 unsupported-claim and hallucinated-specifics rates, vector vs. graph-rag.
* §4 retrieval recall and the accuracy split by retrieval hit.
* §7 accuracy on `medium`-confidence gold items — verify those references before concluding anything.

## 6. Shut down

```bash
# Ctrl-C the Spring Boot app
docker compose down          # never use -v here: the ingested corpus lives in the volume
```
