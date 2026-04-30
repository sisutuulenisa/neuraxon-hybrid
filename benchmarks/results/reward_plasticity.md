# Reward-driven plasticity benchmark

Verdict: `behavioral_plasticity_observed`

No broad Qubic/Neuraxon intelligence claim is made from adapter-only behavior; this benchmark only reports whether reward feedback changed later decisions.

No broad Qubic/Neuraxon intelligence claim is made from adapter-only behavior.

| Mode | Before accuracy | After accuracy | Accuracy delta | Decision-change rate | Internal state changed |
| --- | ---: | ---: | ---: | ---: | --- |
| cold_tissue | 0.250 | 0.167 | -0.083 | 0.417 | True |
| feedback_trained_tissue | 0.208 | 0.250 | 0.042 | 0.375 | True |
| raw_network_only | 0.208 | 0.208 | 0.000 | 0.458 | True |
| semantic_bridge | 0.208 | 0.208 | 0.000 | 0.167 | True |
| persisted_checkpoint | 0.292 | 0.250 | -0.042 | 0.292 | True |
| random | 0.083 | 0.167 | 0.083 | 0.917 | True |
| always_execute | 0.250 | 0.250 | 0.000 | 0.000 | True |

Interpretation:
- Before/after accuracy measures observable behaviour, not just neuromodulator state.
- Decision-change rate records whether later actions changed after feedback.
- If accuracy does not improve, the verdict remains limited even when internal state changes.
