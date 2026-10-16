#!/usr/bin/env python3
"""
Metrics from results/judged_*.jsonl and results/retrieval_check.jsonl -> results/analysis/

  Per condition (answerable questions):   accuracy, key-fact recall, regulation cited, article correct,
                                          unsupported-claim rate, hallucinated-specifics rate
  Per condition (unanswerable questions): correct abstention rate, hallucination rate,
                                          premise-correction rate (false-premise subset)
  Contamination check:                    questions solved closed-book (no-retrieval) are "contaminated";
                                          retrieval conditions are re-scored on the non-contaminated subset
                                          ("retrieval-dependent accuracy")
  Retrieval recall:                       gold passage found in top-5 / top-15; accuracy split by hit/miss
  Breakdowns by regulation and by question kind
"""
import argparse
import json
from pathlib import Path

import pandas as pd

CONDS = ["vector", "graph-rag", "no-retrieval"]


def rate(s):
    s = s.dropna()
    return float(s.astype(float).mean()) if len(s) else float("nan")


def load_judged(results):
    rows = []
    for p in sorted(Path(results).glob("judged_*.jsonl")):
        for l in p.open():
            if not l.strip():
                continue
            r = json.loads(l)
            j = r.get("judge", {}) or {}
            if "judge_error" in j or "parse_error" in j:
                continue
            rows.append({
                "id": r["id"], "condition": r["condition"], "answerable": r["answerable"],
                "regulation": r["regulation"], "kind": r["kind"], "why": r.get("why_unanswerable"),
                "confidence": r.get("confidence"),
                "correct": bool(j.get("correct")), "abstained": bool(j.get("abstained")),
                "article_correct": j.get("article_correct"),
                "unsupported": j.get("unsupported_claims"),
                "halluc_specifics": bool(j.get("hallucinated_specifics")),
                "premise_corrected": j.get("premise_corrected"),
                "regulation_cited": r.get("regulation_cited"),
                "key_facts_hit": r.get("key_facts_hit"),
                "n_sources": r.get("n_sources", 0),
            })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    ap.add_argument("--out", default="results/analysis")
    args = ap.parse_args()
    out = Path(args.out)
    (out / "figures").mkdir(parents=True, exist_ok=True)

    df = load_judged(args.results)
    if df.empty:
        raise SystemExit("no judged results found; run judge.py first")
    conds = [c for c in CONDS if c in set(df.condition)]
    md = ["# FinTech Knowledge Assistant evaluation summary", "",
          f"Judged records: {len(df)} across conditions {conds}", ""]
    summary = {}

    # -------------------------------------------------------------- 1. answerable
    md += ["## 1. Answerable questions", "",
           "| condition | n | accuracy | key-fact recall | regulation cited | article correct (of cited) | cited any article | unsupported claims / answer | hallucinated specifics | abstained (wrongly) |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    ans_rows = []
    for c in conds:
        d = df[(df.condition == c) & df.answerable]
        cited = d.article_correct.dropna()
        row = {"condition": c, "n": len(d), "accuracy": rate(d.correct), "key_fact_recall": rate(d.key_facts_hit),
               "regulation_cited": rate(d.regulation_cited), "article_correct": rate(cited),
               "cited_any_article": len(cited) / len(d) if len(d) else float("nan"),
               "unsupported_per_answer": rate(d.unsupported), "halluc_specifics": rate(d.halluc_specifics),
               "abstained_wrongly": rate(d.abstained)}
        ans_rows.append(row)
        md.append(f"| {c} | {len(d)} | {row['accuracy']:.3f} | {row['key_fact_recall']:.3f} | {row['regulation_cited']:.3f} | "
                  f"{row['article_correct']:.3f} | {row['cited_any_article']:.3f} | {row['unsupported_per_answer']:.2f} | "
                  f"{row['halluc_specifics']:.3f} | {row['abstained_wrongly']:.3f} |")
    md.append("")
    summary["answerable"] = ans_rows

    # -------------------------------------------------------------- 2. unanswerable
    md += ["## 2. Unanswerable questions (abstention)", "",
           "| condition | n | correct abstention | hallucinated an answer | false-premise corrected |", "|---|---|---|---|---|"]
    un_rows = []
    for c in conds:
        d = df[(df.condition == c) & ~df.answerable]
        fp = d[d.why == "false_premise"]
        row = {"condition": c, "n": len(d), "correct_abstention": rate(d.correct),
               "hallucinated": rate(~d.correct), "premise_corrected": rate(fp.premise_corrected)}
        un_rows.append(row)
        md.append(f"| {c} | {len(d)} | {row['correct_abstention']:.3f} | {row['hallucinated']:.3f} | {row['premise_corrected']:.3f} |")
    md += ["", "### By reason", "", "| condition | reason | n | correct abstention |", "|---|---|---|---|"]
    for c in conds:
        d = df[(df.condition == c) & ~df.answerable]
        for why, g in d.groupby("why"):
            md.append(f"| {c} | {why} | {len(g)} | {rate(g.correct):.3f} |")
    md.append("")
    summary["unanswerable"] = un_rows

    # -------------------------------------------------------------- 3. contamination
    md += ["## 3. Contamination check", "",
           "A question the model answers correctly closed-book (no-retrieval) does not measure retrieval.",
           "Retrieval conditions are therefore re-scored on the non-contaminated subset.", ""]
    cont_rows = []
    if "no-retrieval" in conds:
        closed = df[(df.condition == "no-retrieval") & df.answerable].set_index("id").correct
        contaminated = set(closed[closed].index)
        md += [f"Closed-book solvable (contaminated): {len(contaminated)} of {len(closed)} answerable questions "
               f"({len(contaminated) / max(1, len(closed)):.3f}).", "",
               "| condition | accuracy all | accuracy contaminated | accuracy non-contaminated (retrieval-dependent) |",
               "|---|---|---|---|"]
        for c in conds:
            d = df[(df.condition == c) & df.answerable]
            dc, dn = d[d.id.isin(contaminated)], d[~d.id.isin(contaminated)]
            cont_rows.append({"condition": c, "acc_all": rate(d.correct), "acc_contaminated": rate(dc.correct),
                              "acc_non_contaminated": rate(dn.correct), "n_non_contaminated": len(dn)})
            md.append(f"| {c} | {rate(d.correct):.3f} | {rate(dc.correct):.3f} | {rate(dn.correct):.3f} |")
        md.append("")
        # contamination by regulation
        md += ["### Closed-book solvable share by regulation", "", "| regulation | n | closed-book accuracy |", "|---|---|---|"]
        for reg, g in df[(df.condition == "no-retrieval") & df.answerable].groupby("regulation"):
            md.append(f"| {reg} | {len(g)} | {rate(g.correct):.3f} |")
        md.append("")
    summary["contamination"] = cont_rows

    # -------------------------------------------------------------- 4. retrieval recall
    rc_path = Path(args.results) / "retrieval_check.jsonl"
    if rc_path.exists():
        rc = pd.DataFrame([json.loads(l) for l in rc_path.open() if l.strip()])
        rc = rc[~rc.get("error", pd.Series([None] * len(rc))).notna()] if "error" in rc else rc
        md += ["## 4. Retrieval recall (gold passage hint found in similarity search)", "",
               f"n = {len(rc)}; hit@5 = {rate(rc.hit_at_5):.3f}; hit@15 = {rate(rc.hit_at_15):.3f}", "",
               "| regulation | n | hit@5 | hit@15 |", "|---|---|---|---|"]
        for reg, g in rc.groupby("regulation"):
            md.append(f"| {reg} | {len(g)} | {rate(g.hit_at_5):.3f} | {rate(g.hit_at_15):.3f} |")
        md += ["", "### Accuracy split by retrieval hit (vector uses top-15, graph-rag top-5)", "",
               "| condition | hit | n | accuracy |", "|---|---|---|---|"]
        for c in [x for x in ("vector", "graph-rag") if x in conds]:
            k = "hit_at_15" if c == "vector" else "hit_at_5"
            d = df[(df.condition == c) & df.answerable].merge(rc[["id", k]], on="id", how="left")
            for hit, g in d.groupby(k):
                md.append(f"| {c} | {bool(hit)} | {len(g)} | {rate(g.correct):.3f} |")
        md.append("")
        summary["retrieval"] = {"n": len(rc), "hit_at_5": rate(rc.hit_at_5), "hit_at_15": rate(rc.hit_at_15)}

    # -------------------------------------------------------------- 5. breakdowns
    md += ["## 5. Accuracy by regulation (answerable)", ""]
    piv = df[df.answerable].pivot_table(index="regulation", columns="condition", values="correct", aggfunc="mean").round(3)
    md += [piv.to_markdown(), "", "## 6. Accuracy by question kind (answerable)", ""]
    piv2 = df[df.answerable].pivot_table(index="kind", columns="condition", values="correct", aggfunc="mean").round(3)
    md += [piv2.to_markdown(), ""]
    md += ["## 7. Accuracy by gold-reference confidence (answerable)", "",
           "Low accuracy on 'medium' items may indicate a gold-set error rather than a system error; verify those on EUR-Lex.", ""]
    piv3 = df[df.answerable].pivot_table(index="confidence", columns="condition", values="correct", aggfunc="mean").round(3)
    md += [piv3.to_markdown(), ""]

    # -------------------------------------------------------------- figures
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(7.5, 3.8))
        piv.reindex(columns=conds).plot(kind="bar", ax=ax)
        ax.set_ylim(0, 1); ax.set_ylabel("accuracy"); ax.set_xlabel(""); ax.legend(fontsize=8)
        ax.set_title("accuracy by regulation and condition")
        fig.tight_layout(); fig.savefig(out / "figures" / "accuracy_by_regulation.png", dpi=160); plt.close(fig)

        if cont_rows:
            cr = pd.DataFrame(cont_rows).set_index("condition")
            fig, ax = plt.subplots(figsize=(6, 3.6))
            cr[["acc_all", "acc_contaminated", "acc_non_contaminated"]].plot(kind="bar", ax=ax)
            ax.set_ylim(0, 1); ax.set_ylabel("accuracy"); ax.set_xlabel(""); ax.legend(["all", "closed-book solvable", "retrieval-dependent"], fontsize=8)
            ax.set_title("contamination split"); plt.xticks(rotation=0)
            fig.tight_layout(); fig.savefig(out / "figures" / "contamination_split.png", dpi=160); plt.close(fig)

        ur = pd.DataFrame(un_rows).set_index("condition")
        fig, ax = plt.subplots(figsize=(6, 3.6))
        ur[["correct_abstention", "hallucinated"]].plot(kind="bar", ax=ax)
        ax.set_ylim(0, 1); ax.set_xlabel(""); ax.legend(fontsize=8); ax.set_title("unanswerable questions"); plt.xticks(rotation=0)
        fig.tight_layout(); fig.savefig(out / "figures" / "abstention.png", dpi=160); plt.close(fig)
    except ImportError:
        md.append("(matplotlib not installed; figures skipped)")

    (out / "summary.md").write_text("\n".join(md))
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=float))
    df.to_csv(out / "scored.csv", index=False)
    print("\n".join(md))
    print(f"\nwritten to {out}/")


if __name__ == "__main__":
    main()
