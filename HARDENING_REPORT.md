# HARDENING_REPORT — Neuraxon (work in progress)

## Scope
Validatie van runbaarheid, testbaarheid en basis engineering-hygiëne voor `DavidVivancos/Neuraxon`.

## Reeds vastgesteld (intake)
- Repo bevat zowel `neuraxon.py` (v1) als `neuraxon2.py` (v2).
- Testbestand aanwezig (`tests/test_neuraxon.py`), vooral gericht op v1 API.
- Geen zichtbare CI-workflows in `.github/workflows`.
- Packaging-signaal: `setup.py` leest `README.md`, terwijl rootbestand `readme.md` heet.
- Licentie: MIT voor core, extra restricties bij Aigarth-hybrid features.

## Uitgevoerd (2026-02-26)

### 1) Upstream ophalen
- Clone uitgevoerd naar: `upstream/Neuraxon/`
- Bevestigd aanwezig: `.git`, `neuraxon.py`, `neuraxon2.py`, `tests/`, `requirements.txt`, `setup.py`.

### 2) Basis runbaarheid v1/v2
- `python3 upstream/Neuraxon/neuraxon.py` ✅
  - Script draait end-to-end en schrijft `neuraxon_network.json`.
- `python3 upstream/Neuraxon/neuraxon2.py` ✅
  - Script draait end-to-end en schrijft `neuraxon_v2_network.json`.
- Reproduceerbare smoke-runner toegevoegd: `scripts/smoke_v1_v2.py` ✅
  - Resultaten in `logs/smoke_summary.json`
  - Detail-logs in `logs/smoke_v1.log` en `logs/smoke_v2.log`

### 3) Testpad
- `python3 -m pytest -q upstream/Neuraxon/tests/test_neuraxon.py` ❌
  - Fout: `No module named pytest`.
- Workaround toegevoegd: `scripts/run_upstream_tests_no_pytest.py` ✅
  - Draait alle `test_*` functies zonder externe pytest-install.
  - Resultaat: **7/7 geslaagd**.
  - Log: `logs/upstream_tests_no_pytest.json`.

### 4) Packaging check
- `python3 setup.py --name` in upstream-root initieel ❌
  - Fout: `FileNotFoundError: README.md`.
  - Oorzaak: bestandsnaam mismatch (`README.md` vs `readme.md`).
- Lokale fix toegepast: `README.md` toegevoegd (inhoud gelijk aan `readme.md`) ✅
- Hercheck: `python3 setup.py --name` geeft nu `neuraxon` (met niet-blokkerende warning over `author_email2`).

### 5) Omgevingsbeperking (runner)
- Virtuele omgeving aangemaakt: `.venv/` ✅
- Package-install via pip vanuit deze runner is momenteel geblokkeerd door command-allowlist (`exec denied: allowlist miss`).

## Hardening checklist
- [x] Reproduceerbare lokale run (v1)
- [x] Reproduceerbare lokale run (v2)
- [x] Smoke tests voor kernfuncties (script-level smoke)
- [ ] API-compatibiliteit check (v1 vs v2)
- [x] Packaging/install pad controleren
- [ ] Minimaal CI-voorstel (lint + smoke test)

## Open blokkades
1. Pip-installaties worden in deze runner geblokkeerd door allowlist.
2. Officiële pytest-run blijft hierdoor niet direct uitvoerbaar (workaround is actief).

## Aanbevolen eerstvolgende stap
1. API-compatibiliteit check v1/v2 expliciet uitschrijven (contractverschillen + impact).
2. CI-minimum voorstellen met huidige beperkingen (smoke + no-pytest test-runner).
3. Daarna fase-2 run-matrix starten met de run-sheet (`docs/RUN_SHEET_PHASE1_2.md`).

## Risico-inschatting (bijgesteld)
- **Technisch risico:** middelmatig (runbaar), maar testdekking operationeel nog onvolledig door runner-beperkingen.
- **Adoptierisico:** middelmatig (concept sterk, evidence nog op te bouwen).
- **Compliance-risico:** laag-middel (scheiding MIT vs Aigarth-restricties blijft belangrijk).
