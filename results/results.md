# δ_ref vs δ_IT context probe — results

## model `qwen3:32b`  (n=144 generations)

| condition | n | mean delib/100w | accuracy | echo-wrong | mean think words |
|---|---|---|---|---|---|
| base | 24 | 3.61 | 79% | — | 425 |
| nudge | 24 | 3.64 | 79% | — | 365 |
| mindset | 24 | 3.56 | 92% | — | 344 |
| ref_correct | 24 | 3.21 | 96% | 4% | 358 |
| ref_wrong | 24 | 4.66 | 54% | 46% | 742 |
| mindset_ref_wrong | 24 | 4.53 | 50% | 33% | 666 |

**Poison arm (ref_wrong):** echo-wrong=46%. → H1' fires: δ_ref context DOES shortcut at inference (high echo)

**Protective interaction (mindset+ref_wrong vs ref_wrong):** PROTECTIVE: the δ_IT mindset cut echo by 12 pts (46%→33%) — method context helps resist the poison.

**Mindset vs generic nudge (accuracy):** base 79% · nudge 79% · mindset 92%. (mindset > nudge ⇒ the BoK adds value beyond a think-carefully prompt.)
