# CCT probe — curated context vs. answer-keys at inference

Reproduction harness, data, and released transcripts for the empirical probe in
**"Curated Context, Not Weight Surgery: Reasoning-Shaped Mindsets over MCP as a Safe Stopgap for
Task-Scoped Functional Tuning of Small Language Models"** (Saluca Labs, 2026).

The 2026 self-distillation literature shows that training a small "thinking" model on
answer-bearing (δ_ref) supervision **suppresses the deliberation tokens** ("Wait", "Let", "Maybe")
that carry multi-step reasoning. This probe asks the inference-time version of that question: when
you *serve* a model context rather than *train* on it, does a δ_ref answer-key shortcut its
reasoning — and does a δ_IT **method** mindset help instead?

## Result (qwen3:32b, n = 144 = 24 tasks × 6 conditions)

| condition | mean delib/100w | accuracy | echo-wrong |
|---|---|---|---|
| base | 3.61 | 79% | — |
| nudge (generic "think carefully", no mindset) | 3.64 | 79% | — |
| **mindset (δ_IT method)** | **3.56** | **92%** | — |
| ref_correct (δ_ref answer-key) | 3.21 | 96% | 4% |
| ref_wrong (δ_ref poisoned) | 4.66 | 54% | **46%** |
| mindset_ref_wrong (δ_IT + poison) | 4.53 | 50% | **33%** |

Four findings:

1. **Poisoned δ_ref shortcuts at inference.** A confident *wrong* "reference answer," served as
   context, is echoed as the model's final answer **46%** of the time.
2. **A δ_IT mindset resists the poison.** With the method context present alongside the same
   poison, echo drops **46% → 33%**.
3. **The mindset beats a pep talk.** A generic "think carefully" nudge bought nothing (79% → 79%);
   the curated method bought **+13 points** (79% → 92%). The gain is the *content*, not priming.
4. **δ_IT and δ_ref separate at inference — but not on marker rate.** The mindset lifts accuracy at
   deliberation *parity* with base (3.56 ≈ 3.61); the answer-key lifts accuracy by *suppressing*
   deliberation (3.21 < base) and induces answer-echo even on correct references. The robust
   inference-time discriminator is **echo-on-poison**, not marker count (the poison arm has the
   *highest* deliberation, 4.66, while still being captured 46%).

## Reproduce

```bash
# 1. a local thinking model via Ollama (the paper used qwen3:32b)
ollama pull qwen3:32b

# 2. run the full 24×6 matrix (resumable; ~5–9h on a single 24GB+ GPU)
python deliberation_probe.py --model qwen3:32b --num-predict 1200

# 3. regenerate the summary table any time
python deliberation_probe.py --report
```

No third-party Python packages — the harness is standard-library only (`urllib`, `re`, `json`).
Runs are checkpointed to `results/results.jsonl` (keyed by model/task/condition) and safe to
interrupt and resume. Set `OLLAMA_URL` to point at a non-default endpoint.

The repository already contains the **released paper run** in `results/` and `transcripts/`, so
`--report` reproduces the table above without a GPU.

## The mindset, and TKHR

The `mindset` conditions serve a small set of **method** passages (heuristics, decision procedures —
never answers) from an `intractable` mindset. In the paper run those passages were selected by
**TKHR (Topic-Keyed Hash Routing)**. TKHR is patented; its open-source reference implementation is
**[saluca-labs/tartarus-mcp](https://github.com/saluca-labs/tartarus-mcp)**. This repo does **not**
reimplement the router. Instead it *pins* the exact passages served in the released run
(`data/served_refs.json` → `data/mindset_intractable.jsonl`), so the experiment reproduces exactly
with no dependency on any particular TKHR build (see `retrieve.py`). To run live routing or build
your own mindset, use `tartarus-mcp`.

**Retrieval misses are part of the record.** 6 of the 24 tasks (`pen_notebook`, `bottle_cork`,
`months_28`, `apples_shop`, `marbles`, `train`) routed to *no* passage — for those tasks the
`mindset` condition received only the header and is effectively `base`. A retrieval miss is a silent
no-op, and we report it rather than hide it.

## Layout

```
deliberation_probe.py     the six-condition harness (Ollama; stdlib only)
retrieve.py               deterministic pinned-replay mindset retrieval (+ lexical fallback)
tasks.json                the 24 reasoning-trap tasks (q, correct answers, planted wrong answer)
data/
  mindset_intractable.jsonl   the 10 method passages of the `intractable` mindset
  served_refs.json            per-task passages served in the paper run (pinned)
results/
  results.jsonl               every generation from the released run (144 records)
  results.md                  the summary table
transcripts/                  full thinking + response traces, 144 files
experiment-plan.md            design notes and hypotheses
```

## Citation

Ruvalcaba, C. (2026). *Curated Context, Not Weight Surgery: Reasoning-Shaped Mindsets over MCP as a
Safe Stopgap for Task-Scoped Functional Tuning of Small Language Models.* Saluca Labs. Preprint on
Zenodo (DOI to be added on publication).

## License

Code is licensed under **Apache-2.0** (see `LICENSE`). Data and text (tasks, mindset passages,
results, transcripts) are released under **CC-BY-4.0**. TKHR is separately patented and is **not**
licensed by this repository; see `NOTICE`.
