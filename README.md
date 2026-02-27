# Neuraxon Hybrid Workspace

Doel: een **overzichtelijke plugin-hybride** evaluatie van Neuraxon opzetten.

## Structuur

- `docs/` — roadmap, claim-matrix, paper-notes, beslissingen
- `upstream/` — referenties naar upstream code (Neuraxon repo)
- `plugins/` — onze pluginlaag (interfaces + adapters)
- `benchmarks/` — benchmark scenario's, scripts en resultaten
- `data/` — kleine testdata/manifests (geen zware datasets committen)
- `scripts/` — lokale helper scripts voor reproduceerbare runs

## Principes

1. **Kerncode vs pluginlaag scheiden**
2. **Alles reproduceerbaar documenteren**
3. **Claims pas accepteren na meetbaar bewijs**

## Swarm orchestration-notitie

Queue/prompts voor swarm orchestration leven bewust **buiten deze projectrepo**:

- runtime queue/state: `local/runtime/agent-swarm/...`
- orchestration prompt templates: `local/scripts/agent-swarm/prompts/...`

Zo blijft deze repo clean en projectgericht.

## Visuele statuspagina (lokaal/Tailscale)

Dashboard: `dashboard/index.html`

Server starten:

```bash
cd /home/sisu/.openclaw/workspace/local/projects/neuraxon-hybrid
python3 scripts/serve_dashboard.py --host 0.0.0.0 --port 8787
```

URL (Tailscale):

- `http://100.76.31.10:8787/dashboard/`
