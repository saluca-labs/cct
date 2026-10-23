# AGENTS.md

Instructions for AI coding agents working in this repository.

## What this is

The reproduction harness, pinned inputs and released run (144 generations of qwen3:32b) for the
CCT probe in the preprint "Curated Context, Not Weight Surgery". It is a research record with a
standard-library harness, not a library.

## Read in this order

1. `README.md`: the "How it works" diagram, the corrected results table and the Correction notes.
2. `deliberation_probe.py`: prompts per condition, the Ollama call, scoring, `--report`.
3. `retrieve.py`: the pinned replay of the served mindset passages.
4. `results/results.jsonl`: one record per generation, including `done_reason`.
5. `experiment-plan.md`: the design and the pre-registered hypotheses.

## What you can and cannot see

- You can see the whole harness, the tasks, the served passages and every generation and
  transcript of the released run.
- You cannot see TKHR, the router that chose the served passages. It is patent pending, not in
  this repo and not licensed by it; the open reference implementation is saluca-labs/tartarus-mcp.
  `retrieve.py` replays what it chose and does not route.
- The preprint and the post-mortem are on Zenodo, not in this repo.

## The only numbers to trust

- Deliberation and accuracy per condition: `python deliberation_probe.py --report`, computed from
  `results/results.jsonl`.
- Generations that hit the 1,200-token limit (20/24 `ref_wrong`, 14/24 `mindset_ref_wrong`):
  `done_reason` in `results/results.jsonl` (the one-line count is in the README).
- Retrieval misses (6 of 24 tasks): `python retrieve.py`, from `data/served_refs.json`.
- Not the echo-wrong column or the H1'/PROTECTIVE verdicts that `--report` and
  `results/results.md` still print. They are withdrawn (paper v0.3).

## Quickstart

```bash
python deliberation_probe.py --report
```

## Setup

Python 3 (tested with 3.12.10), standard library only. A live run also needs Ollama serving a thinking
model at `http://localhost:11434` (override with `OLLAMA_URL`, the full `/api/generate` URL).

## Test

There is no test suite. The check that the scorer and report still work on the released data:

```bash
python retrieve.py
python deliberation_probe.py --report
git diff --exit-code results/results.md
```

Passing looks like `OK: 24 pinned tasks resolve ...`, the summary table printed for `qwen3:32b`
(n=144), and no diff.

## Conventions

- Standard library only; do not add dependencies.
- No em-dashes in docs.
- If the call path in `deliberation_probe.py` or `retrieve.py` changes, update the README diagram
  in the same change.
- If a doc changes, regenerate `llms-full.txt` in the same change or delete it.

## Do not

- Edit `results/results.jsonl`, `transcripts/`, `data/` or `tasks.json`: they are the released
  paper run (CC-BY-4.0) and the pinned inputs that make it reproducible.
- Run a live `--model` inside this checkout unless you mean to add records: the harness appends
  to `results/results.jsonl` and writes into `transcripts/`. Use a copy.
- Quote the echo-wrong figures (46%, 33%, 4%) as results. They are withdrawn; see the README
  Correction.
- Reimplement TKHR here. It is patent pending and not licensed by this repository (see `NOTICE`).
- Commit secrets, hostnames, internal paths or personal emails.

## Done means

`python deliberation_probe.py --report` runs and leaves `results/results.md` unchanged, and the
README still matches what the code on `main` does.
