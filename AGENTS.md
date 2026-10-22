# AGENTS.md

Instructions for AI coding agents working in this repository.

## Setup

Python 3 (tested with 3.12.10), standard library only. A live run also needs Ollama serving a thinking
model at `http://localhost:11434` (override with `OLLAMA_URL`, the full `/api/generate` URL).

## Test

There is no test suite. The check that the scorer and report still work on the released data:

```bash
python deliberation_probe.py --report
git diff --exit-code results/results.md
```

Passing looks like the summary table printed for `qwen3:32b` (n=144) and no diff.

## Conventions

- Standard library only; do not add dependencies.
- No em-dashes in docs.
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
