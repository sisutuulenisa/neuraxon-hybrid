# Claim → Bewijs matrix (v1)

_Deze versie bevat ook de mapping van de Qubic-nieuwsbrief “Neural Networks: Where Neuroscience Meets AI” (doorgestuurd op 2026-02-26)._ 

| Claim | Bron | Huidige status | Nodige verificatie |
|---|---|---|---|
| Continue real-time learning zonder aparte train/inference | Paper + README + nieuwsbrief v4 | Onbevestigd | Drift-scenario benchmark met online update protocol |
| Trinaire states (`+1/0/-1`) verbeteren robuustheid/efficiëntie | Paper + codeconcept + nieuwsbrief v4 | Onbevestigd | Vergelijking tegen binaire/continue baseline met gelijk budget |
| Dual-weight plasticity (`w_fast` + `w_slow`) ondersteunt snelle + trage adaptatie | Nieuwsbrief v4 + paper claims | Onbevestigd | Ablation: `w_fast` only vs `w_slow` only vs beide; adaptatiesnelheid + stabiliteit meten |
| Homeostatic stabilisatie voorkomt runaway / forgetting | Paper (Eq met `tanh` + homeostasis) + nieuwsbrief v4 | Gedeeltelijk conceptueel | Lange-run stabiliteitstest + forgetting metrics |
| Small-world topologie geeft snellere adaptatie | Paper + codeparameter (`ws_k`, `ws_beta`) + nieuwsbrief v4 | Onbevestigd | Ablation: random vs small-world onder identieke taken |
| Contextuele neuromodulatie (`meta`) verhoogt flexibiliteit | Paper + codestructuur + nieuwsbrief v4 | Onbevestigd | Factorial ablation per modulator/receptorgroep + sensitivity-analyse op `meta` |
| Self-organized criticality (balans orde/chaos) verbetert adaptief gedrag | Nieuwsbrief v4 + conceptueel paperkader | Onbevestigd | Dynamische regime-tests (perturbatie-respons, stabiliteitsvenster, collapse-rate) |
| Useful Proof of Work levert schaalbare compute voor Neuraxon-simulaties | Nieuwsbrief v4 (Qubic infra claim) | Onbevestigd in onze setup | Deploy/profiling-test op Qubic-pad: throughput, kost, reproduceerbaarheid, fault tolerance |
| Physical robotbeslissingen zijn niet gescript | Social claim + HF Space code | Gedeeltelijk onderbouwd (fysieke BLE-control aanwezig, maar ook heuristische replay/explore code) | Reproduceerbare live demo + script-detect protocol + log-evidence |

## Nieuwsbrief-mapping (kort)

- **Direct bevestigd als overlap met bestaande matrix:** trinaire states, small-world, neuromodulatie, continue learning, homeostase.
- **Nieuw expliciet benoemd in de nieuwsbrief (toegevoegd aan matrix):** dual-weight plasticity (`w_fast`/`w_slow`), self-organized criticality, Useful Proof of Work compute-claim.
- **Belangrijk:** de nieuwsbrief voegt vooral **narratief en framing** toe; geen nieuwe onafhankelijke benchmarkresultaten.

## Beslisregel
Claim telt pas als “bewezen” bij:
1. reproduceerbare run,
2. heldere metricwinst,
3. vergelijking met minstens 1 sterke baseline.

## Testprotocol
Concreet protocol (fase 1/2) met metrics + pass/fail-drempels:
- `docs/TEST_PROTOCOL_PHASE1_2.md`
