"""Évaluation de la recherche : Recall@k et MRR sur les 60 questions annotées,
plus un test de refus sur des questions hors sujet.

Usage : python -m eval.evaluate [--dense auto|e5|lsa]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.rag import ExtractiveGenerator, build_retrievers, load_chunks

HERE = Path(__file__).parent
KS = (1, 3, 5)
OFF_TOPIC = [
    "Quelle est la couleur du logo du groupe ?",
    "Qui a gagné la Coupe du monde 2018 ?",
    "Comment faire une pâte à crêpes ?",
    "Quel temps fera-t-il demain à Paris ?",
    "Quelle est la capitale de l'Australie ?",
    "Comment configurer mon imprimante ?",
]


def gold_rank(hits, doc, section, depth=10):
    for r, (c, _) in enumerate(hits[:depth], 1):
        if c.doc == doc and c.section == section:
            return r
    return None


def evaluate(retrievers, questions):
    rows, per_q = [], {}
    for key, ret in retrievers.items():
        ranks = []
        for q in questions:
            r = gold_rank(ret.search(q["question"], 10), q["doc"], q["section"])
            ranks.append(r)
            per_q.setdefault(q["id"], {"question": q["question"]})[key] = r
        n = len(ranks)
        row = {"retriever": ret.name, "key": key}
        for k in KS:
            row[f"recall@{k}"] = sum(1 for r in ranks if r and r <= k) / n
        row["mrr@10"] = sum(1 / r for r in ranks if r) / n
        rows.append(row)
    return rows, per_q


def refusal_test(retriever, chunks):
    gen = ExtractiveGenerator(chunks)
    refused = [q for q in OFF_TOPIC if gen.answer(q, retriever.search(q, 3)).startswith("Je ne trouve pas")]
    return len(refused), len(OFF_TOPIC)


def plot(rows, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    metrics = ["recall@1", "recall@3", "recall@5", "mrr@10"]
    labels = ["Recall@1", "Recall@3", "Recall@5", "MRR@10"]
    colors = ["#9aa3c2", "#5b6aa8", "#B08A3E", "#1E2761"]
    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=150)
    w = 0.8 / len(rows)
    for i, row in enumerate(rows):
        xs = [m + (i - (len(rows) - 1) / 2) * w for m in range(len(metrics))]
        vals = [row[m] * 100 for m in metrics]
        bars = ax.bar(xs, vals, w * 0.92, label=row["retriever"], color=colors[i % len(colors)])
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{v:.0f}", ha="center", fontsize=8, color="#333")
    ax.set_xticks(range(len(metrics)), labels)
    ax.set_ylim(0, 110)
    ax.set_ylabel("%")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="upper left", ncol=2)
    ax.set_title("CareerBot RH : qualité de la recherche sur 60 questions", fontsize=11, loc="left")
    fig.tight_layout()
    fig.savefig(path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dense", default="auto", choices=["auto", "e5", "lsa"])
    a = ap.parse_args()
    chunks = load_chunks()
    questions = [json.loads(l) for l in (HERE / "questions.jsonl").open(encoding="utf-8")]
    rets = build_retrievers(chunks, a.dense)
    rows, per_q = evaluate(rets, questions)
    ref, tot = refusal_test(rets["hybrid"], chunks)
    out = {"n_questions": len(questions), "n_chunks": len(chunks), "results": rows,
           "refusal_off_topic": {"refused": ref, "total": tot}, "per_question": per_q}
    (HERE / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    plot(rows, HERE / "results.png")
    print(f"{len(questions)} questions · {len(chunks)} chunks\n")
    print(f"{'Retriever':32} {'R@1':>6} {'R@3':>6} {'R@5':>6} {'MRR@10':>7}")
    for r in rows:
        print(f"{r['retriever']:32} {r['recall@1']:6.1%} {r['recall@3']:6.1%} {r['recall@5']:6.1%} {r['mrr@10']:7.3f}")
    print(f"\nRefus correct des questions hors sujet : {ref}/{tot}")
    misses = [(i, v["question"]) for i, v in per_q.items() if not v.get("hybrid") or v["hybrid"] > 3]
    print(f"\nQuestions où l'hybride ne met pas la bonne section dans le top 3 ({len(misses)}) :")
    for i, q in misses:
        print(f"  #{i} {q}")
