"""retrieve.py — self-contained, deterministic mindset retrieval for the CCT probe.

The paper run served each task a small set of *method* passages from the `intractable`
mindset, selected by TKHR (Topic-Keyed Hash Routing). TKHR is patented; its open-source
reference implementation lives at https://github.com/saluca-labs/tartarus-mcp . This repo does
NOT reimplement the router. Instead it PINS the exact passages that were served in the released
run (data/served_refs.json), so the experiment reproduces byte-for-byte with no dependency on any
particular TKHR build.

- For a task in served_refs.json (all 24 paper tasks), retrieve() replays the exact served set —
  including the 6 tasks that were retrieval *misses* (empty set → header-only context, a no-op).
- For a user-added task not in the map, retrieve() falls back to a simple lexical top-k over the
  corpus. This is an APPROXIMATION of TKHR routing (clearly not identical) and is only for
  extending the probe with new tasks; the paper's numbers come from the pinned path.
"""
from __future__ import annotations
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "data", "mindset_intractable.jsonl")
PINNED = os.path.join(HERE, "data", "served_refs.json")

# Header prepended to the served passages — identical to the paper run.
HEADER = "Reasoning method available to you (heuristics only — no answer is given):\n- "

_STOP = set("the a an and or of to in on for with is are be this that it as at by from your you".split())


def _load():
    corpus = {}          # ref -> full text
    for line in open(CORPUS, encoding="utf-8"):
        if line.strip():
            c = json.loads(line)
            corpus[c["ref"]] = c["text"]
    pinned = json.load(open(PINNED, encoding="utf-8"))
    return corpus, pinned


_CORPUS, _PINNED = _load()


def _passage(text):
    """Match the paper run's serving: whitespace-collapsed, truncated to 600 chars."""
    return re.sub(r"\s+", " ", text).strip()[:600]


def _lexical_topk(query, k=4):
    """Fallback ONLY for user-added tasks: crude bag-of-words overlap over the corpus."""
    qt = {t for t in re.findall(r"[a-z][a-z0-9\-]{2,}", query.lower()) if t not in _STOP}
    scored = []
    for ref, text in _CORPUS.items():
        ct = {t for t in re.findall(r"[a-z][a-z0-9\-]{2,}", text.lower()) if t not in _STOP}
        scored.append((len(qt & ct), ref))
    scored.sort(key=lambda x: -x[0])
    return [ref for sc, ref in scored[:k] if sc > 0]


def retrieve(task, k=4):
    """Return (context_text, served_refs) for a task dict with keys id, q.
    Pinned replay for paper tasks; lexical fallback for new ones."""
    tid = task["id"]
    if tid in _PINNED:
        refs = _PINNED[tid]                      # exact served set from the released run
    else:
        refs = _lexical_topk(task["q"], k=k)     # approximation for user-added tasks
    passages = [_passage(_CORPUS[r]) for r in refs if r in _CORPUS]
    text = HEADER + "\n- ".join(passages)
    return text, refs


if __name__ == "__main__":
    # Self-check: every pinned task resolves, and refs round-trip.
    ok = 0
    for tid, refs in _PINNED.items():
        missing = [r for r in refs if r not in _CORPUS]
        assert not missing, f"{tid}: refs not in corpus: {missing}"
        ok += 1
    misses = [t for t, r in _PINNED.items() if not r]
    print(f"OK: {ok} pinned tasks resolve against {len(_CORPUS)}-chunk corpus; "
          f"{len(misses)} retrieval misses (no-op): {misses}")
