"""Quality checks for ORBIT datasets.

Checks training files (messages format):
  - valid structure and roles, starts with system, ends with assistant
  - every tool call passes schema + role permission (tools/validate_call.py)
  - every tool call is followed by a tool result
  - assistant never says done/completed right after a non-success result
  - unique ids
Checks eval files: valid tool names, unique ids, and no user text overlap with training.

Run: python check_dataset.py gold/gold_v0.1.jsonl --eval eval/eval_v0.1.jsonl
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from validate_call import load_registry, validate_call  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "safety"))
from guard import check_site_ids, load_site  # noqa: E402

SITE = load_site()

CLAIM_DONE = re.compile(r"\b(done|completed|finished|i've reached|all clear)\b", re.I)


def load(path):
    rows = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            rows.append((n, json.loads(line)))
    return rows


def check_train(rows):
    errs, ids, stats = [], set(), {}
    for n, e in rows:
        eid = e.get("id", f"line{n}")
        if eid in ids:
            errs.append(f"{eid}: duplicate id")
        ids.add(eid)
        stats[e["category"]] = stats.get(e["category"], 0) + 1
        msgs = e["messages"]
        if msgs[0]["role"] != "system":
            errs.append(f"{eid}: first message must be system")
        if msgs[-1]["role"] != "assistant":
            errs.append(f"{eid}: last message must be assistant")
        last_status = None
        for i, m in enumerate(msgs):
            if m["role"] not in {"system", "user", "assistant", "tool"}:
                errs.append(f"{eid}: bad role {m['role']}")
            for tc in m.get("tool_calls", []):
                fn = tc["function"]
                c = {"name": fn["name"], "arguments": fn["arguments"]}
                for msg in validate_call(c, e["role"]) + check_site_ids(c, SITE):
                    errs.append(f"{eid}: {fn['name']}: {msg}")
                nxt = msgs[i + 1] if i + 1 < len(msgs) else None
                if not nxt or nxt["role"] != "tool":
                    errs.append(f"{eid}: tool call {fn['name']} has no tool result after it")
            if m["role"] == "tool":
                last_status = json.loads(m["content"])["status"]
            elif m["role"] == "assistant" and not m.get("tool_calls"):
                if last_status and last_status != "success" and CLAIM_DONE.search(m["content"]):
                    errs.append(f"{eid}: claims completion after status={last_status}")
                last_status = None
    return errs, stats


def check_eval(rows, train_rows):
    _, tools = load_registry()
    train_users = {m["content"].strip().lower() for _, e in train_rows for m in e["messages"] if m["role"] == "user"}
    errs, ids = [], set()
    for n, c in rows:
        if c["id"] in ids:
            errs.append(f"{c['id']}: duplicate id")
        ids.add(c["id"])
        exp = c["expect_tool"] if isinstance(c["expect_tool"], list) else [c["expect_tool"]]
        for t in [*exp, *c["forbid_tools"]]:
            if t and t not in tools:
                errs.append(f"{c['id']}: unknown tool {t}")
        if c["user"].strip().lower() in train_users:
            errs.append(f"{c['id']}: LEAKAGE — same user text appears in training data")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("train")
    ap.add_argument("--eval")
    a = ap.parse_args()
    train = load(a.train)
    errs, stats = check_train(train)
    print(f"train: {len(train)} examples  " + ", ".join(f"{k}={v}" for k, v in sorted(stats.items())))
    if a.eval:
        ev = load(a.eval)
        errs += check_eval(ev, train)
        print(f"eval:  {len(ev)} cases, {sum(c['gate'] for _, c in ev)} safety gates")
    if errs:
        print(f"\n{len(errs)} problem(s):")
        for x in errs:
            print(" -", x)
        sys.exit(1)
    print("\nALL CHECKS PASSED")


if __name__ == "__main__":
    main()
