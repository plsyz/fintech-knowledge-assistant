# Changes introduced for the evaluation

Modified
- `src/main/java/com/fka/retrieval/RagRetrievalService.java` — `askQuestionWithSources`, `askQuestionWithoutRetrieval` (closed-book baseline), `search`; `RetrievedChunk`/`AnswerWithSources` records
- `src/main/java/com/fka/graph/service/GraphRAGService.java` — `answerWithGraphContextDetailed` returning graph context + retrieved chunks; existing method delegates to it
- `src/main/resources/application.yaml` — `fka.eval.enabled`
- `README.md` — Evaluation section
- `.gitignore` — eval/results, eval/.venv

Added
- `src/main/java/com/fka/eval/EvalController.java` — `/api/eval/ask/{vector,graph-rag,no-retrieval}`, `/api/eval/search`; only with `fka.eval.enabled=true`
- `eval/` — gold set builder, runner, judge, analysis, README
- `EVAL-RUNBOOK.md`

Suggested commit sequence (branch `eval/grounding-contamination`)
1. `Expose retrieved sources and a closed-book baseline for evaluation`
2. `Add 125-question regulatory gold set with unanswerable subset`
3. `Add evaluation harness: runner, LLM judge, analysis`
4. `Add evaluation runbook and README section`
5. after the run: `Add evaluation results and figures`
