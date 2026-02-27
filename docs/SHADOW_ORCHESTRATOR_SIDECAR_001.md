# SHADOW_ORCHESTRATOR_SIDECAR_001

**Datum:** 2026-02-27  
**Status:** ontwerp (read-only pilot)  
**Doel:** een extra “point of view” toevoegen boven ACP/SA zonder de hoofdinfrastructuur te breken.

---

## Waarom dit bestaat

We zien in de praktijk dat sommige ACP-runs stilvallen (weinig zichtbare output/file-activiteit). Een lichte sidecar kan dan:
- sneller signaleren dat iets scheef loopt,
- een tweede mening geven (niet alleen watchdog-regels),
- fallback-advies geven (ACP -> SA) met motivatie.

Belangrijk: dit is **advisory**, geen extra uitvoeringslaag.

---

## Scope (fase 1)

### In scope
1. **Read-only event ingest**
   - leest task-state (`active-tasks.json`) en history events.
2. **Shadow scorecard per task**
   - progress score
   - reliability score
   - evidence score
3. **Advies-output**
   - `continue` / `steer` / `fallback-to-sa` / `needs-human`
   - met compacte redenregels.

### Niet in scope
- Geen auto-kill, auto-restart of auto-merge.
- Geen write-acties op code/worktrees.
- Geen extra model dat rechtstreeks acties uitvoert.

---

## Architectuur (thin sidecar)

1. **Observer** (collector)
   - input: runtime state + logs
   - output: genormaliseerde task snapshots
2. **Critic** (scorer)
   - berekent scorecard op vaste regels
3. **Advisor** (policy)
   - vertaalt scorecard naar advies + confidence
4. **Reporter**
   - schrijft korte samenvatting naar sidecar-output
   - kan later naar thread/milestone format worden gemapt

---

## Scorecard v0

- **Progress (0-100)**
  - recente file-activiteit
  - status-updates/checkpoints
  - aantoonbare artifacts
- **Reliability (0-100)**
  - retries
  - stale-detecties
  - probe gezondheid (`UNKNOWN`/timeouts)
- **Evidence (0-100)**
  - test output aanwezig
  - reproduceerbaar runbewijs
  - doc/status sync

**Adviesregel (v0):**
- lage progress + lage reliability => `fallback-to-sa`
- hoge progress + stabiele reliability => `continue`
- medium progress + beperkte issues => `steer`
- max retries / harde blocker => `needs-human`

---

## Pilotplan (veilig)

### Stap 1 — observatie-only (nu)
- sidecar produceert alleen rapportjes, geen acties.

### Stap 2 — advisory in workflow
- advies zichtbaar in statusblokken, mens beslist.

### Stap 3 — optioneel semi-auto
- pas na bewezen precisie mag sidecar pre-gevulde suggestieacties aanreiken.

---

## Exit criteria voor fase 1

Pilot is geslaagd als:
1. sidecar bij >=80% van vastlopers dezelfde richting geeft als menselijke interventie;
2. false alarms beperkt blijven (<=20%);
3. geen impact op stabiliteit van bestaande ACP/SA flow.

---

## Koppeling met huidige afspraken

- ACP blijft default waar het werkt.
- SA-fallback blijft toegestaan bij niet-productieve ACP-runs.
- Sidecar ondersteunt die beslissing met extra context, maar forceert niets.
