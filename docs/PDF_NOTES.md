# PDF-notes — Neuraxon v2.0 (Vivancos & Sanchez)

_Noot: dit is een eerste analyse op basis van de gedeelde papertekst/snippets uit WhatsApp. Volledige sectie-voor-sectie review volgt in de hardeningfase._

## Wat de paper claimt (samengevat)

1. **Trinaire neuronuitvoer** (`+1/0/-1`) voor excitatie/neutraliteit/inhibitie.
2. **Continue verwerking in de tijd** i.p.v. strikt discrete inferentiestappen.
3. **Derde synaptische toestand** (modulerend/subthreshold) met nadruk op metabotrope dynamiek.
4. **Structurele plasticiteit**: synapsvorming, collapse/reconnect, en zeldzame neuron death.
5. **Homeostatische stabilisatie** met verzadiging (`tanh`) + firing-rate target term.
6. **Small-world / schaalvrije synchronisatie** als architecturale eigenschap.
7. **Aigarth-hybridisatie** als case study voor evolutionaire componenten.

## Sterke punten in tekst

- Verbindt expliciet neurowetenschappelijke mechanismen aan architectuurkeuzes.
- Benoemt beperkingen/open punten zoals Dale’s law en interneuron-diversiteit als uitbreidingsrichting.
- Formuleert stabilisatieideeën (bounded modulation + homeostasis), wat relevant is voor continue learning.

## Kritische gaten (voor ons validatieplan)

- Veel conceptuele claims; in de papertekst die we nu hebben zijn nog geen harde, onafhankelijke benchmarktabellen gezien.
- "Revolutionair" taalgebruik moet getest worden met **strikte baselines**.
- Onzeker of alle genoemde bio-mechanismen in code volledig en robuust operationeel zijn.

## Conclusie voor roadmap

- Paper is waardevol als **hypothese- en ontwerpdocument**.
- Voor productiekeuze blijft vereist:
  - reproduceerbare experimentset,
  - baseline-comparatie,
  - meetbare winst op concrete use-cases.

## Addendum — Qubic nieuwsbrief (Volume 4, doorgestuurd 2026-02-26)

Kernclaims uit de nieuwsbrief zijn gemapt naar `CLAIM_MATRIX.md`.

Wat de nieuwsbrief toevoegt:
- expliciete framing van **Neuraxon als brug** tussen ANN en bio-geïnspireerde dynamiek,
- expliciete claim rond **dual-weight plasticity** (`w_fast`/`w_slow`),
- expliciete claim rond **self-organized criticality**,
- expliciete infrastructuurclaim rond **Useful Proof of Work** (Qubic miners als compute-laag).

Wat de nieuwsbrief **niet** toevoegt:
- geen nieuwe onafhankelijke benchmarktabellen,
- geen extra reproduceerbaar experimenteel protocol,
- geen direct bewijs dat marketingclaims al production-grade zijn.
