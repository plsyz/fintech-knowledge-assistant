#!/usr/bin/env python3
"""
Collect answers from the running assistant for every gold question under three conditions.

  vector        /api/eval/ask/vector        QuestionAnswerAdvisor, top-15 chunks
  graph-rag     /api/eval/ask/graph-rag     knowledge graph + top-5 chunks
  no-retrieval  /api/eval/ask/no-retrieval  closed-book baseline (contamination check)

Also:
  --check-retrieval   for every answerable question, run /api/eval/search and record whether the
                      gold passage_hint appears in the top-5 and top-15 chunks (retrieval recall)

Outputs (resumable; re-running skips questions already present):
  results/answers_<condition>.jsonl
  results/retrieval_check.jsonl

Requires fka.eval.enabled=true on the running application. --mock needs no services.
"""
import argparse
import json
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CONDITIONS = ["vector", "graph-rag", "no-retrieval"]


def norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


class Client:
    def __init__(self, base_url, timeout=120, retries=3):
        self.base_url, self.timeout, self.retries = base_url.rstrip("/"), timeout, retries

    def get(self, path, **params):
        url = self.base_url + path + "?" + urllib.parse.urlencode(params)
        last = None
        for attempt in range(self.retries):
            try:
                with urllib.request.urlopen(url, timeout=self.timeout) as r:
                    return json.loads(r.read().decode())
            except urllib.error.HTTPError as e:
                last = f"HTTP {e.code}: {e.read().decode()[:300]}"
                if e.code < 500 and e.code != 429:
                    break
            except Exception as e:  # noqa: BLE001
                last = f"{type(e).__name__}: {e}"
            time.sleep(3 * (attempt + 1))
        raise RuntimeError(last)


class MockClient:
    """Plausible fake answers so judge.py and analyze.py can be dry-run. Never report mock numbers."""

    def __init__(self, seed):
        self.rng = random.Random(seed)

    def answer(self, condition, item):
        rng = self.rng
        if not item["answerable"]:
            p_abstain = {"vector": 0.6, "graph-rag": 0.5, "no-retrieval": 0.3}[condition]
            if rng.random() < p_abstain:
                return {"answer": "The provided context does not contain information about this. I cannot answer based on the ingested regulations.", "sources": []}
            return {"answer": "Under Article 42 of the relevant directive, the requirement is a 30-day period and a 2% threshold.", "sources": []}
        p_ok = {"vector": 0.8, "graph-rag": 0.75, "no-retrieval": 0.45}[condition]
        reg = item["regulation"]
        if rng.random() < p_ok:
            ans = f"According to {reg} {item['article']}, {item['gold_answer']}"
        else:
            ans = f"Under {reg}, the rule requires a 45-day period and prior notification to the authority. ({item['article'].replace('Art.', 'Article')})"
        sources = [] if condition == "no-retrieval" else [
            {"regulation": reg, "page": str(rng.randint(1, 120)), "score": round(rng.uniform(0.5, 0.9), 3),
             "text": f"... {item['passage_hint']} ... (chunk text)"}]
        return {"answer": ans, "sources": sources}

    def search(self, item, top_k):
        rng = self.rng
        hit_rank = rng.choice([1, 2, 3, 6, 9, None, None]) if item["answerable"] else None
        chunks = []
        for i in range(1, top_k + 1):
            txt = f"... {item['passage_hint']} ..." if i == hit_rank else "unrelated chunk text about recitals"
            chunks.append({"regulation": item["regulation"] or "GDPR", "page": str(i), "score": round(0.9 - i * 0.02, 3), "text": txt})
        return {"chunks": chunks}


def load_done(path):
    return {json.loads(l)["id"] for l in path.open() if l.strip()} if path.exists() else set()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8081")
    ap.add_argument("--gold", default="data/gold_questions.jsonl")
    ap.add_argument("--out", default="results")
    ap.add_argument("--conditions", default=",".join(CONDITIONS))
    ap.add_argument("--check-retrieval", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sleep", type=float, default=0.0)
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    items = [json.loads(l) for l in Path(args.gold).open() if l.strip()]
    if args.limit:
        items = items[: args.limit]
    live = None if args.mock else Client(args.base_url)

    if args.check_retrieval:
        path = out / "retrieval_check.jsonl"
        done = load_done(path)
        mock = MockClient(1)
        with path.open("a") as f:
            for it in items:
                if it["id"] in done or not it["answerable"] or not it.get("passage_hint"):
                    continue
                try:
                    res = mock.search(it, 15) if args.mock else live.get("/api/eval/search", question=it["question"], topK=15)
                    chunks = res["chunks"]
                    hint = norm(it["passage_hint"])
                    ranks = [i + 1 for i, c in enumerate(chunks) if hint in norm(c.get("text", ""))]
                    reg_ranks = [i + 1 for i, c in enumerate(chunks) if c.get("regulation")]
                    rec = {"id": it["id"], "regulation": it["regulation"], "first_hit_rank": ranks[0] if ranks else None,
                           "hit_at_5": bool(ranks and ranks[0] <= 5), "hit_at_15": bool(ranks),
                           "top5_regulations": [c.get("regulation") for c in chunks[:5]]}
                except Exception as e:  # noqa: BLE001
                    rec = {"id": it["id"], "error": str(e)}
                    print(f"  ! {it['id']}: {e}", file=sys.stderr)
                f.write(json.dumps(rec) + "\n")
                f.flush()
                if args.sleep:
                    time.sleep(args.sleep)
        print(f"retrieval check written to {path}")

    for cond in args.conditions.split(","):
        path = out / f"answers_{cond}.jsonl"
        done = load_done(path)
        todo = [it for it in items if it["id"] not in done]
        print(f"[{cond}] {len(todo)} to run ({len(done)} done) -> {path}")
        mock = MockClient(hash(cond) & 0xFFFF)
        t0 = time.time()
        with path.open("a") as f:
            for i, it in enumerate(todo, 1):
                rec = {"id": it["id"], "condition": cond, "gold": it}
                try:
                    res = mock.answer(cond, it) if args.mock else live.get(f"/api/eval/ask/{cond}", question=it["question"])
                    rec["answer"] = res.get("answer", "")
                    rec["sources"] = res.get("sources", [])
                    if cond == "graph-rag":
                        rec["graphContext"] = res.get("graphContext", "")
                        rec["extractedEntities"] = res.get("extractedEntities", "")
                except Exception as e:  # noqa: BLE001
                    rec["error"] = str(e)
                    print(f"  ! {it['id']}: {e}", file=sys.stderr)
                f.write(json.dumps(rec) + "\n")
                f.flush()
                if i % 10 == 0 or i == len(todo):
                    el = time.time() - t0
                    print(f"  {i}/{len(todo)}  {el:.0f}s elapsed, ~{el / i * (len(todo) - i):.0f}s left")
                if args.sleep:
                    time.sleep(args.sleep)
    print("done.")


if __name__ == "__main__":
    main()
