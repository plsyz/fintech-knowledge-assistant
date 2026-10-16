# Knowledge-assistant evaluation harness

Measures how well the assistant grounds regulatory answers in the ingested corpus, whether it
abstains when the answer is not there, and how much of its accuracy is actually attributable
to retrieval rather than to the base model's parametric knowledge (contamination check).

```
eval/
├── build_gold_set.py     125 questions: 105 answerable (regulation + article + key facts), 20 unanswerable
├── run_eval.py           collects answers for 3 conditions + retrieval-recall check (resumable; --mock)
├── judge.py              deterministic checks + LLM judge -> results/judged_<condition>.jsonl
├── analyze.py            metrics, tables, figures -> results/analysis/
├── requirements.txt
└── data/                 gold_questions.jsonl, regulation_aliases.json
```

## Conditions

| Condition | Endpoint | What the model sees |
|---|---|---|
| `vector` | `/api/eval/ask/vector` | top-15 chunks via `QuestionAnswerAdvisor` (the `/api/rag/ask` path) |
| `graph-rag` | `/api/eval/ask/graph-rag` | knowledge-graph context + top-5 chunks (the `/api/graph-rag/ask` path) |
| `no-retrieval` | `/api/eval/ask/no-retrieval` | nothing — same model and system prompt, closed book |

The closed-book condition is the contamination check: a question the base model answers
correctly with no context does not measure retrieval, so the retrieval conditions are
re-scored on the subset the closed-book model gets wrong (retrieval-dependent accuracy).

## Gold set

* 105 answerable questions across the 11 ingested regulations (PSD2, SCA RTS, SEPA, MiCA, DORA,
  EMD2, AMLD5, AMLD6, GDPR, IFR; the PSD2 quick guide is not targeted). Each has the regulation,
  the article, a reference answer, key facts that must appear, and a `passage_hint` used for the
  retrieval-recall check.
* 20 unanswerable questions: regulation not in the corpus (PSD3, IPR, AI Act, TFR, UK/US law...),
  fabricated articles, facts outside the law text, and false premises.
* Article references carry a `confidence` flag. Items marked `medium` must be verified against
  the PDFs before results are reported (`build_gold_set.py` prints the list). The retrieval check
  also flags hints that do not appear in the corpus.

The `regulation` tags in the gold set must match the `regulation` metadata used at ingest;
edit `data/regulation_aliases.json` if different tags were used.

## Running

```bash
cd eval
pip install -r requirements.txt
python build_gold_set.py
python run_eval.py --check-retrieval               # retrieval recall for gold passages
python run_eval.py                                 # vector, graph-rag, no-retrieval
export ANTHROPIC_API_KEY=...                       # judge model: different from the system under test
python judge.py --judge-model claude-sonnet-4-5
python analyze.py
```

Runs are resumable. `--mock` on `run_eval.py` and `judge.py` exercises the harness without any
services (mock numbers are not results).

## Outputs

* `results/analysis/summary.md`, `summary.json`, `scored.csv`
* `results/analysis/figures/`: `accuracy_by_regulation.png`, `contamination_split.png`, `abstention.png`
