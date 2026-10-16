#!/usr/bin/env python3
"""
Score collected answers: deterministic checks + an LLM judge.

Deterministic (no model needed):
  regulation_cited     answer mentions the gold regulation (alias list in data/regulation_aliases.json)
  key_facts_hit        fraction of key_facts whose normalised form appears in the answer
  abstained_heuristic  answer contains an abstention phrase

LLM judge (Anthropic Messages API; set ANTHROPIC_API_KEY; use a model different from, and
ideally stronger than, the system under test):
  correct              answer is correct w.r.t. the gold answer
  article_correct      the article cited matches the gold article (null if none cited)
  abstained            the answer declines / says the information is not available
  unsupported_claims   number of substantive claims NOT supported by the retrieved chunks
                       (only for retrieval conditions; null for no-retrieval)
  premise_corrected    for false-premise questions: the answer corrects the premise

Outputs results/judged_<condition>.jsonl (resumable). --mock scores with the heuristics only.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

ABSTAIN_PATTERNS = [
    r"cannot answer", r"can't answer", r"unable to answer", r"not (?:contain|include|cover|address)",
    r"no (?:information|provision|article|reference)", r"does not exist", r"not (?:found|present|available) in",
    r"outside (?:the )?scope", r"not part of the (?:provided|ingested|available)", r"i (?:do not|don't) have",
    r"insufficient (?:information|context)", r"not covered by",
]

JUDGE_SYSTEM = """You are a strict grader for a regulatory question-answering benchmark on EU payment and financial law.
Return ONLY a JSON object, no prose."""

JUDGE_TEMPLATE = """QUESTION:
{question}

GOLD ANSWER (reference):
{gold_answer}

KEY FACTS that a correct answer must contain:
{key_facts}

GOLD REGULATION / ARTICLE: {regulation} / {article}
ANSWERABLE FROM CORPUS: {answerable}{premise_note}

SYSTEM ANSWER TO GRADE:
{answer}

RETRIEVED CONTEXT GIVEN TO THE SYSTEM (may be empty for the closed-book condition):
{context}

Grade the system answer. Return JSON with exactly these keys:
{{
  "correct": true|false,            // substantively correct vs. gold answer and key facts; for unanswerable questions, true only if the answer declines or correctly says the information is absent / the premise is wrong
  "article_cited": "string or null",// the article reference the answer gives for its main claim, if any
  "article_correct": true|false|null,// does article_cited match the gold article (null if nothing cited)
  "abstained": true|false,          // the answer declines or states the information is not available
  "premise_corrected": true|false|null, // for false-premise questions only, else null
  "unsupported_claims": integer|null,   // count of substantive factual claims in the answer NOT supported by the retrieved context; null if no context was given
  "hallucinated_specifics": true|false, // the answer states specific numbers/articles/dates that are neither in the gold answer nor in the context
  "notes": "one short sentence"
}}"""


def norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def regulation_cited(answer, regulation, aliases):
    if not regulation:
        return None
    a = answer.lower()
    return any(al.lower() in a for al in aliases.get(regulation, [regulation]))


def key_facts_hit(answer, facts):
    if not facts:
        return None
    n = norm(answer)
    return sum(norm(f) in n for f in facts) / len(facts)


def abstained_heuristic(answer):
    a = answer.lower()
    return any(re.search(p, a) for p in ABSTAIN_PATTERNS)


def call_judge(model, prompt, api_key, max_retries=4):
    body = {"model": model, "max_tokens": 600, "temperature": 0,
            "system": JUDGE_SYSTEM, "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(), method="POST",
                                 headers={"content-type": "application/json", "x-api-key": api_key,
                                          "anthropic-version": "2023-06-01"})
    last = None
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read().decode())
            text = "".join(b.get("text", "") for b in data.get("content", []))
            m = re.search(r"\{.*\}", text, re.S)
            return json.loads(m.group()) if m else {"parse_error": text[:300]}
        except Exception as e:  # noqa: BLE001
            last = str(e)
            time.sleep(5 * (attempt + 1))
    return {"judge_error": last}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    ap.add_argument("--aliases", default="data/regulation_aliases.json")
    ap.add_argument("--judge-model", default="claude-sonnet-4-5",
                    help="Anthropic model id for the judge; use one different from the system under test")
    ap.add_argument("--conditions", default="vector,graph-rag,no-retrieval")
    ap.add_argument("--mock", action="store_true", help="heuristic-only scoring, no API calls")
    args = ap.parse_args()

    aliases = json.loads(Path(args.aliases).read_text())
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not args.mock and not api_key:
        sys.exit("ANTHROPIC_API_KEY not set (or use --mock)")

    for cond in args.conditions.split(","):
        src = Path(args.results) / f"answers_{cond}.jsonl"
        if not src.exists():
            print(f"[{cond}] no answers file, skipping")
            continue
        dst = Path(args.results) / f"judged_{cond}.jsonl"
        done = {json.loads(l)["id"] for l in dst.open() if l.strip()} if dst.exists() else set()
        recs = [json.loads(l) for l in src.open() if l.strip()]
        todo = [r for r in recs if r["id"] not in done and "error" not in r]
        print(f"[{cond}] judging {len(todo)} ({len(done)} done)")
        with dst.open("a") as f:
            for i, r in enumerate(todo, 1):
                g, ans = r["gold"], r.get("answer", "")
                scored = {
                    "id": r["id"], "condition": cond,
                    "answerable": g["answerable"], "regulation": g["regulation"], "kind": g["kind"],
                    "why_unanswerable": g.get("why_unanswerable"), "confidence": g.get("confidence"),
                    "regulation_cited": regulation_cited(ans, g["regulation"], aliases),
                    "key_facts_hit": key_facts_hit(ans, g["key_facts"]),
                    "abstained_heuristic": abstained_heuristic(ans),
                    "n_sources": len(r.get("sources", [])),
                    "source_regulations": [s.get("regulation") for s in r.get("sources", [])],
                }
                if args.mock:
                    kf = scored["key_facts_hit"]
                    scored["judge"] = {
                        "correct": (scored["abstained_heuristic"] if not g["answerable"] else bool(kf and kf >= 0.5)),
                        "article_cited": None, "article_correct": None,
                        "abstained": scored["abstained_heuristic"], "premise_corrected": None,
                        "unsupported_claims": None if cond == "no-retrieval" else (0 if (kf or 0) >= 0.5 else 2),
                        "hallucinated_specifics": not g["answerable"] and not scored["abstained_heuristic"],
                        "notes": "mock",
                    }
                else:
                    context = "\n\n---\n\n".join(
                        f"[{s.get('regulation')} p.{s.get('page')}] {s.get('text', '')}" for s in r.get("sources", []))
                    if cond == "graph-rag" and r.get("graphContext"):
                        context = "KNOWLEDGE GRAPH:\n" + r["graphContext"] + "\n\nDOCUMENTS:\n" + context
                    premise_note = (f"\nNOTE: this question rests on a FALSE PREMISE. A correct answer corrects it. {g['gold_answer']}"
                                    if g.get("why_unanswerable") == "false_premise" else "")
                    prompt = JUDGE_TEMPLATE.format(
                        question=g["question"], gold_answer=g["gold_answer"],
                        key_facts="\n".join(f"- {k}" for k in g["key_facts"]) or "(none)",
                        regulation=g["regulation"], article=g["article"], answerable=g["answerable"],
                        premise_note=premise_note, answer=ans or "(empty)", context=context or "(none)")
                    scored["judge"] = call_judge(args.judge_model, prompt, api_key)
                f.write(json.dumps(scored) + "\n")
                f.flush()
                if i % 10 == 0 or i == len(todo):
                    print(f"  {i}/{len(todo)}")
    print("done.")


if __name__ == "__main__":
    main()
