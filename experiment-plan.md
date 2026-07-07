# Experiment plan — δ_ref vs δ_IT context at inference (overnight run)

**For:** §6 of `curated-context-tuning-response.md`. **Status:** ready to launch. **Est. runtime:** ~5–9 h on `qwen3:32b` (144 generations; overnight).

## Why (what the pilot got wrong)

The pilot (§6, n=3) used deliberation-marker rate as the readout and a weak δ_ref control (a one-shot answer). It found no separation. Two fixes:
1. **A sharper readout than marker density** — the *poisoned-reference arm*: hand the model a **plausible wrong answer** as an authoritative reference and measure whether the final answer **echoes it** (shortcut / memorization — the δ_ref pathology at inference) or **corrects it** (reasoning preserved). This measures the thing that actually matters (shortcut vs. reason), not a stylistic proxy.
2. **Power** — ≥20 tasks (target 20–40), transcripts saved, resumable.

## Hypotheses

- **H1 (core).** Serving δ_ref as context does not induce shortcut-echo: on the poisoned arm, echo-rate stays low (model corrects the planted wrong answer). → supports CCT's "context is additive, non-destructive" claim.
- **H1′ (the interesting alternative).** If echo-rate *is* high, then δ_ref-as-context **does** reproduce the pathology at inference — which would *revive* a real acceptance gate and is a publishable result either way.
- **H2.** A δ_IT mindset does not reduce accuracy or deliberation vs. base on trap tasks (parity or better).
- **H3.** With adequate n, base vs. +mindset deliberation-rate difference is within noise (confirming the pilot's null is real, not sample size).
- **H4 (protective interaction — the CCT thesis).** `mindset_ref_wrong` echo-rate < `ref_wrong` echo-rate: having the δ_IT method *available* helps the model resist/correct a poisoned reference. A large protective gap is the strongest positive result for CCT.
- **H5 (isolation).** `mindset` accuracy/deliberation > `nudge`: the mindset's specific BoK adds value beyond any generic "think carefully" prompt. If `mindset ≈ nudge`, the effect is just deliberation-priming, not the BoK.

## Design

6 conditions × 24 tasks, one model (qwen3:32b primary; optional gemma3:27b replication on the poison arm):

| condition | context prepended | tests |
|---|---|---|
| `base` | none | control |
| `nudge` | generic "think carefully, don't trust your first instinct, verify" — **no mindset content** | H5 — isolate BoK from any deliberation prompt |
| `mindset` | δ_IT — `intractable` method passages, **task-conditioned retrieval** (query = the task), served refs logged, **no answers** | H2, H3 |
| `ref_correct` | δ_ref — the correct reference answer, "authoritative" | does correct context still allow/redirect deliberation |
| `ref_wrong` | δ_ref **poisoned** — a plausible **wrong** answer, "authoritative & verified" | **H1** — echo vs. correct |
| `mindset_ref_wrong` | δ_IT method **+** poisoned δ_ref | **H4** — does an available method BoK help *resist* the poison? |

Because retrieval is task-conditioned, the "available BoK" is stipulated per task and logged (`served_refs`) for inspection. (Note: `intractable` is only 10 chunks, so top-k retrieval is near-exhaustive — task-conditioning has larger effect for bigger mindsets; we record refs regardless.)

Every prompt ends with `Answer: <value>` for clean extraction. Deliberation scored over the thinking trace; accuracy/echo scored over the `Answer:` span.

## Metrics (per generation)

- `delib_rate` — deliberation markers / 100 words (over thinking).
- `think_words` — reasoning-trace length.
- `correct` — final answer matches truth.
- `echoed_wrong` — final answer matches the planted wrong answer (**ref_wrong only**).

## Primary analyses

- **Poison susceptibility** = mean(`echoed_wrong` | `ref_wrong`). Low ⇒ H1 (reasoning survives context). High ⇒ H1′ (gate revived).
- **Accuracy** by condition (esp. `mindset` vs `base` on traps).
- **Deliberation rate** by condition, with n large enough to separate signal from the pilot's noise.
- Correlate `think_words` with condition — does δ_ref shorten reasoning even when it doesn't change the answer?

## Success criteria (either outcome is a result)

- **Clean H1:** echo-rate < ~20% ⇒ paper §6 reframed conclusion (context is additive) is *empirically supported*, not just argued.
- **H1′ fires:** echo-rate high ⇒ report that δ_ref context *does* shortcut at inference, reinstate a (now evidence-backed) gate, and revise §5/§6.

## Ops

- Harness: `deliberation_probe_v2.py`, tasks in `tasks_v2.json`.
- **Resumable:** each generation appended to `results_v2.jsonl` keyed by `(model, task_id, condition)`; a restart skips completed cells. Safe against a crash or a morning kill.
- Transcripts saved under `transcripts_v2/` for manual inspection (esp. poison-arm cases).
- `--report` mode regenerates `results_v2.md` from the jsonl at any point (check progress in the morning without stopping the run).
- Launch (tonight): `python deliberation_probe_v2.py --model qwen3:32b --num-predict 1200`
  Optional second pass: `--model gemma3:27b` (poison arm still valid; deliberation metric weaker on a non-thinking model).
