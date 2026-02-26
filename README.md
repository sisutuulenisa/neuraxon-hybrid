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
