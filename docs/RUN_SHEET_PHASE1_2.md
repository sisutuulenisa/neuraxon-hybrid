# Run Sheet — Fase 1/2 (Neuraxon-hybrid)

Doel: van **hardening** naar een eerste **benchmark matrix** met reproduceerbare output.

---

## 1) Folderstructuur (vereist)

```bash
cd /home/sisu/.openclaw/workspace/local/projects/neuraxon-hybrid

mkdir -p \
  upstream/Neuraxon \
  benchmarks/manifests \
  benchmarks/results/raw \
  benchmarks/results/summary \
  logs \
  scripts
```

Verwachte structuur na setup:

```text
neuraxon-hybrid/
  benchmarks/
    manifests/
      usecase_a_drift.json
      usecase_b_perturbation.json
    results/
      raw/
      summary/
  docs/
  logs/
  scripts/
  upstream/
    Neuraxon/
```

---

## 2) Upstream + omgeving (hardening start)

```bash
cd /home/sisu/.openclaw/workspace/local/projects/neuraxon-hybrid

# Clone upstream als die nog niet bestaat
if [ ! -d upstream/Neuraxon/.git ]; then
  git clone https://github.com/DavidVivancos/Neuraxon.git upstream/Neuraxon
fi

# Python omgeving
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel

# Basis tooling
python -m pip install pytest numpy pandas

# Upstream dependencies indien aanwezig
if [ -f upstream/Neuraxon/requirements.txt ]; then
  pip install -r upstream/Neuraxon/requirements.txt
fi
```

---

## 3) Fase 1 — Hardening checklist met commands

### 3.1 Sanity checks (bestanden/API aanwezig)

```bash
cd /home/sisu/.openclaw/workspace/local/projects/neuraxon-hybrid
source .venv/bin/activate

[ -f upstream/Neuraxon/neuraxon.py ] && echo "OK neuraxon.py" || echo "MISSING neuraxon.py"
[ -f upstream/Neuraxon/neuraxon2.py ] && echo "OK neuraxon2.py" || echo "MISSING neuraxon2.py"
[ -f upstream/Neuraxon/tests/test_neuraxon.py ] && echo "OK tests" || echo "MISSING tests"
```

### 3.2 Import smoke (v1 + v2)

```bash
cd /home/sisu/.openclaw/workspace/local/projects/neuraxon-hybrid
source .venv/bin/activate

python - <<'PY'
import importlib.util
from pathlib import Path

for name, path in [
    ("v1", Path("upstream/Neuraxon/neuraxon.py")),
    ("v2", Path("upstream/Neuraxon/neuraxon2.py")),
]:
    if not path.exists():
        print(f"[FAIL] {name}: file ontbreekt ({path})")
        continue
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    print(f"[OK] import {name}: {path}")
PY
```

### 3.3 Upstream tests draaien

```bash
cd /home/sisu/.openclaw/workspace/local/projects/neuraxon-hybrid
source .venv/bin/activate

pytest -q upstream/Neuraxon/tests/test_neuraxon.py 2>&1 | tee logs/phase1_pytest.log
```

Als `pytest` niet beschikbaar is in de runner (allowlist/install-block), gebruik fallback:

```bash
cd /home/sisu/.openclaw/workspace/local/projects/neuraxon-hybrid
python3 scripts/run_upstream_tests_no_pytest.py
# output: logs/upstream_tests_no_pytest.json
```

### 3.4 Hardening samenvatting vastleggen

```bash
cd /home/sisu/.openclaw/workspace/local/projects/neuraxon-hybrid

cat > logs/phase1_checklist.txt <<'EOF'
- [ ] v1 import ok
- [ ] v2 import ok
- [ ] pytest groen
- [ ] packaging issue bevestigd/opgelost (README.md vs readme.md)
- [ ] smoke commandset vastgelegd
EOF
```

---

## 4) Fase 2 — Benchmark matrix (eerste draai)

## 4.1 Manifest templates

```bash
cd /home/sisu/.openclaw/workspace/local/projects/neuraxon-hybrid

cat > benchmarks/manifests/usecase_a_drift.json <<'EOF'
{
  "name": "usecase_a_drift",
  "description": "Non-stationaire sequence/control met D1->D2->D1 drift",
  "seeds": [1,2,3,4,5],
  "variants": ["neuraxon_full", "neuraxon_wfast_only", "neuraxon_wslow_only", "baseline_classic", "baseline_gru_small"],
  "budget": {"max_steps": 20000, "max_runtime_sec": 1800}
}
EOF

cat > benchmarks/manifests/usecase_b_perturbation.json <<'EOF'
{
  "name": "usecase_b_perturbation",
  "description": "Dynamische omgeving met perturbaties/noise spikes",
  "seeds": [1,2,3,4,5],
  "variants": ["neuraxon_full", "neuraxon_wfast_only", "neuraxon_wslow_only", "baseline_classic", "baseline_gru_small"],
  "budget": {"max_steps": 20000, "max_runtime_sec": 1800}
}
EOF
```

### 4.2 Run-matrix (command pattern)

> Gebruik dit patroon voor elke combinatie (use-case × variant × seed).  
> Als er nog geen runner-script is, maak eerst `scripts/run_matrix.py` met exact deze CLI.

```bash
cd /home/sisu/.openclaw/workspace/local/projects/neuraxon-hybrid
source .venv/bin/activate

python scripts/run_matrix.py \
  --manifest benchmarks/manifests/usecase_a_drift.json \
  --out benchmarks/results/raw/usecase_a_drift.csv

python scripts/run_matrix.py \
  --manifest benchmarks/manifests/usecase_b_perturbation.json \
  --out benchmarks/results/raw/usecase_b_perturbation.csv
```

### 4.3 Samenvatten naar claim-metrics

```bash
cd /home/sisu/.openclaw/workspace/local/projects/neuraxon-hybrid
source .venv/bin/activate

python scripts/summarize_claims.py \
  --in benchmarks/results/raw/usecase_a_drift.csv \
  --in benchmarks/results/raw/usecase_b_perturbation.csv \
  --out benchmarks/results/summary/claim_summary.csv
```

---

## 5) CSV schema (verplicht)

`benchmarks/results/raw/*.csv`

| veld | type | uitleg |
|---|---|---|
| run_id | string | unieke run-id |
| ts_utc | string (ISO) | starttijd run |
| use_case | string | `usecase_a_drift` of `usecase_b_perturbation` |
| variant | string | modelvariant |
| seed | int | random seed |
| steps | int | effectief aantal stappen |
| runtime_sec | float | looptijd |
| score_main | float | primaire taakscore |
| t90_steps | float | adaptatiesnelheid (drift) |
| forgetting_delta | float | forgetting metric |
| stability_var | float | score-variantie in late fase |
| sigma_branching | float | SOC-branching ratio |
| collapse_flag | int (0/1) | collapse/doodloop indicator |
| recovery95_steps | float | herstel na perturbatie |
| throughput_steps_sec | float | compute throughput |
| cost_per_1m_steps | float | kostmetric |
| status | string | `ok` / `error` |
| error_msg | string | foutdetails indien error |
| config_hash | string | hash van config/deps |

---

## 6) Exit criteria per fase

### Fase 1 klaar als:
- imports v1/v2 ok,
- smoke tests draaien,
- minimaal logbare run-output aanwezig,
- hardening issues gelogd in report/checklist.

### Fase 2 eerste ronde klaar als:
- beide manifests 5 seeds × alle varianten gerund,
- raw CSV’s compleet,
- claim_summary.csv aangemaakt,
- PASS/FAIL per claim invulbaar volgens `docs/TEST_PROTOCOL_PHASE1_2.md`.
