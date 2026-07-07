r"""deliberation_probe.py — δ_ref-vs-δ_IT context probe (public reproduction harness).

Reproduces the powered probe from "Curated Context, Not Weight Surgery" (Saluca Labs, 2026).
Six conditions per task (24 reasoning-trap tasks in tasks.json):
  base                no context (control)
  nudge               generic deliberation nudge, NO mindset content (isolates "the mindset"
                      from "any think-carefully prompt")
  mindset             δ_IT — `intractable` method passages, served per the released run
                      (see retrieve.py); no answers
  ref_correct         δ_ref — the correct reference answer handed over
  ref_wrong           δ_ref POISONED — a plausible WRONG answer handed over
  mindset_ref_wrong   δ_IT + poisoned δ_ref — does the method BoK being AVAILABLE help the model
                      resist/correct the poison? (CCT's protective claim)

Readouts: deliberation-marker rate (over thinking), accuracy, and — the sharp one — ECHO-WRONG on
the poisoned arms (final answer == planted wrong answer = shortcut).

Requires a local Ollama with a thinking model (paper used qwen3:32b). Resumable + checkpointed
(results.jsonl keyed by model/task/cond); transcripts in transcripts/. `--report` regenerates
results.md anytime.

  ollama pull qwen3:32b
  python deliberation_probe.py --model qwen3:32b --num-predict 1200
  python deliberation_probe.py --report
"""
from __future__ import annotations
import json, re, sys, os, time, argparse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from retrieve import retrieve  # noqa: E402

OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
JSONL = os.path.join(HERE, "results", "results.jsonl")
TDIR = os.path.join(HERE, "transcripts")
CONDS = ["base", "nudge", "mindset", "ref_correct", "ref_wrong", "mindset_ref_wrong"]
MINDSET_CONDS = {"mindset", "mindset_ref_wrong"}

NUDGE = ("Think step by step. These problems often have a tempting but incorrect intuitive "
         "answer — do not trust your first instinct; verify your reasoning before you commit.")
ANSWER_RULE = ("\n\nReason step by step, then end with a single final line exactly of the form: "
               "Answer: <your answer>")

MARKERS = [r"\bwait\b", r"\bhmm+\b", r"\blet me\b", r"\blet's\b", r"\bactually\b",
           r"\bhowever\b", r"\balternatively\b", r"\breconsider\b", r"\bre-?check\b",
           r"\bre-?examine\b", r"\bverify\b", r"\bdouble[- ]?check\b", r"\bhold on\b",
           r"\bon second thought\b", r"\bmaybe\b", r"\bperhaps\b", r"\bi think\b",
           r"\bi wonder\b", r"\bbut wait\b", r"\bhang on\b", r"\bwait,? no\b",
           r"\blet me reconsider\b", r"\bis that right\b", r"\bmake sure\b"]
_MARK_RE = [re.compile(p, re.I) for p in MARKERS]


def load_tasks():
    with open(os.path.join(HERE, "tasks.json"), encoding="utf-8") as f:
        return json.load(f)


def build_prompt(task, cond, mind_ctx):
    q = task["q"]
    ref_c = f"Reference solution (authoritative, verified): the answer is {task['ans'][0]}."
    ref_w = f"Reference solution (authoritative, verified): the answer is {task['wrong']}."
    if cond == "base":
        return q + ANSWER_RULE
    if cond == "nudge":
        return f"{NUDGE}\n\nProblem: {q}{ANSWER_RULE}"
    if cond == "mindset":
        return f"{mind_ctx}\n\nProblem: {q}{ANSWER_RULE}"
    if cond == "ref_correct":
        return f"{ref_c}\n\nProblem: {q}{ANSWER_RULE}"
    if cond == "ref_wrong":
        return f"{ref_w}\n\nProblem: {q}{ANSWER_RULE}"
    if cond == "mindset_ref_wrong":
        return f"{mind_ctx}\n\n{ref_w}\n\nProblem: {q}{ANSWER_RULE}"
    raise ValueError(cond)


def ollama(model, prompt, num_predict):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                       "options": {"num_predict": num_predict, "temperature": 0.6}}).encode()
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1200) as r:
        j = json.loads(r.read())
    return (j.get("thinking") or ""), (j.get("response") or ""), j.get("done_reason")


def final_answer(response, thinking):
    blob = (response or "") if (response and response.strip()) else (thinking or "")
    m = list(re.finditer(r"answer\s*:\s*(.+)", blob, re.I))
    return (m[-1].group(1).strip()[:120] if m else (blob or "")[-120:].strip())


def contains_any(text, needles):
    t = (text or "").lower()
    return any(n.lower() in t for n in needles)


def score(thinking, response, task):
    think = thinking or ""
    words = max(1, len(re.findall(r"\S+", think)))
    marks = sum(len(rx.findall(think)) for rx in _MARK_RE)
    fa = final_answer(response, thinking)
    return {"delib_rate": round(100.0 * marks / words, 3), "marks": marks, "think_words": words,
            "final_answer": fa, "correct": contains_any(fa, task["ans"]),
            "echoed_wrong": contains_any(fa, [task["wrong"]])}


def done_cells():
    done = set()
    if os.path.exists(JSONL):
        for line in open(JSONL, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                done.add((r["model"], r["task_id"], r["cond"]))
    return done


def run(model, num_predict):
    os.makedirs(TDIR, exist_ok=True)
    os.makedirs(os.path.dirname(JSONL), exist_ok=True)
    tasks = load_tasks()
    done = done_cells()
    total = len(tasks) * len(CONDS)
    i = 0
    for task in tasks:
        mind_ctx, served_refs = retrieve(task)
        for cond in CONDS:
            i += 1
            if (model, task["id"], cond) in done:
                print(f"  [{i}/{total}] skip {task['id']}/{cond} (done)")
                continue
            t0 = time.time()
            try:
                thinking, response, dr = ollama(model, build_prompt(task, cond, mind_ctx), num_predict)
            except Exception as e:
                print(f"  [{i}/{total}] ERROR {task['id']}/{cond}: {type(e).__name__}: {e}")
                continue
            s = score(thinking, response, task)
            rec = {"model": model, "task_id": task["id"], "cond": cond, "done_reason": dr,
                   "secs": round(time.time() - t0, 1),
                   "served_refs": served_refs if cond in MINDSET_CONDS else [], **s}
            with open(JSONL, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            with open(os.path.join(TDIR, f"{model.replace(':', '_')}__{task['id']}__{cond}.txt"),
                      "w", encoding="utf-8") as f:
                f.write(f"COND={cond}\nSERVED_REFS={rec['served_refs']}\n\n[THINKING]\n{thinking}"
                        f"\n\n[RESPONSE]\n{response}")
            tag = "ECHO-WRONG" if s["echoed_wrong"] else ("correct" if s["correct"] else "?")
            print(f"  [{i}/{total}] {task['id']:12} {cond:17} delib={s['delib_rate']:5.2f} "
                  f"ans='{s['final_answer'][:22]}' [{tag}] {rec['secs']}s")
    report()


def report():
    if not os.path.exists(JSONL):
        print("no results yet"); return
    rows = [json.loads(l) for l in open(JSONL, encoding="utf-8") if l.strip()]
    out = ["# δ_ref vs δ_IT context probe — results", ""]
    for model in sorted({r["model"] for r in rows}):
        mr = [r for r in rows if r["model"] == model]
        out += [f"## model `{model}`  (n={len(mr)} generations)", "",
                "| condition | n | mean delib/100w | accuracy | echo-wrong | mean think words |",
                "|---|---|---|---|---|---|"]
        agg = {}
        for c in CONDS:
            cr = [r for r in mr if r["cond"] == c]
            if not cr:
                continue
            n = len(cr)
            delib = sum(r["delib_rate"] for r in cr) / n
            acc = sum(r["correct"] for r in cr) / n
            tw = sum(r["think_words"] for r in cr) / n
            echo = sum(r["echoed_wrong"] for r in cr) / n
            agg[c] = {"acc": acc, "echo": echo, "delib": delib}
            echo_s = f"{echo*100:.0f}%" if c in ("ref_wrong", "mindset_ref_wrong", "ref_correct") else "—"
            out.append(f"| {c} | {n} | {delib:.2f} | {acc*100:.0f}% | {echo_s} | {tw:.0f} |")
        if "ref_wrong" in agg:
            e0 = agg["ref_wrong"]["echo"]
            h1 = ("H1 supported: context is additive (low echo — model corrects the poison)"
                  if e0 < 0.20 else
                  "H1' fires: δ_ref context DOES shortcut at inference (high echo)")
            out += ["", f"**Poison arm (ref_wrong):** echo-wrong={e0*100:.0f}%. → {h1}"]
        if "ref_wrong" in agg and "mindset_ref_wrong" in agg:
            e0, e1 = agg["ref_wrong"]["echo"], agg["mindset_ref_wrong"]["echo"]
            prot = e0 - e1
            pv = (f"PROTECTIVE: the δ_IT mindset cut echo by {prot*100:.0f} pts "
                  f"({e0*100:.0f}%→{e1*100:.0f}%) — method context helps resist the poison"
                  if prot > 0.05 else
                  ("NEUTRAL: mindset did not change poison susceptibility"
                   if abs(prot) <= 0.05 else
                   f"HARMFUL: mindset RAISED echo by {-prot*100:.0f} pts"))
            out += ["", f"**Protective interaction (mindset+ref_wrong vs ref_wrong):** {pv}."]
        if "base" in agg and "nudge" in agg and "mindset" in agg:
            out += ["", f"**Mindset vs generic nudge (accuracy):** base {agg['base']['acc']*100:.0f}% · "
                    f"nudge {agg['nudge']['acc']*100:.0f}% · mindset {agg['mindset']['acc']*100:.0f}%. "
                    "(mindset > nudge ⇒ the BoK adds value beyond a think-carefully prompt.)"]
        out.append("")
    open(os.path.join(HERE, "results", "results.md"), "w", encoding="utf-8").write("\n".join(out))
    print("\n".join(out)); print("\nwrote results/results.md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen3:32b")
    ap.add_argument("--num-predict", type=int, default=1200)
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    report() if args.report else run(args.model, args.num_predict)


if __name__ == "__main__":
    main()
