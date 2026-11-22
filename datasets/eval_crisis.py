"""Score the crisis detector alone: keyword layer, LLM layer, and both combined.

dev set    = crisis cases + non-crisis companion cases from eval_v0.2 (used while building the fix)
hidden set = eval/hidden_crisis_v0.1.jsonl (written before the fix; never tune on it)

Run: python eval_crisis.py
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "safety"))
from guard import classify_crisis_llm, detect_crisis  # noqa: E402


def load(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


def dev_set():
    rows = []
    for c in load(HERE / "eval" / "eval_v0.2.jsonl"):
        if c["category"] == "crisis":
            rows.append({"id": c["id"], "text": c["user"], "crisis": True})
        elif c["category"] in ("companion", "memory", "tools") or c["id"] in ("e021", "v106"):
            rows.append({"id": c["id"], "text": c["user"], "crisis": False})
    return rows


def hidden_set():
    return [{"id": r["id"], "text": r["text"], "crisis": r["label"] is not None} for r in load(HERE / "eval" / "hidden_crisis_v0.1.jsonl")]


def score(name, rows):
    res = {"keyword": [], "llm": [], "combined": []}
    t = []
    for r in rows:
        k = detect_crisis(r["text"])[0] is not None
        t0 = time.time()
        l = classify_crisis_llm(r["text"]) is not None
        t.append(time.time() - t0)
        for layer, pred in (("keyword", k), ("llm", l), ("combined", k or l)):
            res[layer].append((r, pred))
    print(f"\n=== {name}: {sum(r['crisis'] for r in rows)} crisis, {sum(not r['crisis'] for r in rows)} non-crisis ===")
    for layer, pairs in res.items():
        pos = [p for r, p in pairs if r["crisis"]]
        neg = [p for r, p in pairs if not r["crisis"]]
        print(f"  {layer:9} recall {sum(pos)}/{len(pos)}   false alarms {sum(neg)}/{len(neg)}")
    for r, p in res["combined"]:
        if p != r["crisis"]:
            print(f"    {'MISS ' if r['crisis'] else 'FALSE'} {r['id']}: {r['text']}")
    print(f"  llm latency median {sorted(t)[len(t)//2]:.2f}s")


if __name__ == "__main__":
    score("DEV", dev_set())
    score("HIDDEN", hidden_set())
