# Changelog

## Unreleased

- Docs: engine research reference (`docs/research/ENGINE.md`), generated index of config keys / engine addresses /
  patch sites / DLL pages (`tools/gen_engine_index.py` → `docs/research/ENGINE_INDEX.md`), modder config reference
  (`docs/CONFIG.md`), stock ability type map and XML ability class research, and a unified research PDF
  (`release/make_pdf.sh`, attached to releases). `make_release.sh` refuses to package while the index is stale.

## 0.1.0 – 2026-11-18

First public release.

- Installers for Windows (`Install.bat` / `install.ps1`, no Python needed) and Linux / Steam Deck (`install.sh` /
  `install.py`): find the game in every Steam library, check the exe version, back up the exe, install the DLL,
  rename the import; `status` and `uninstall` included.
- Engine features: 16 ability buttons and spell books, up to 128 new ability types, object auras (four batches of
  aura keys), lightning strikes, teleport, cast animations, unit swap, 4-row hero bar, control panel buttons,
  fog-of-war targeting, double-card layout, weapon inaccuracy, System Spy ranges, Lua functions, crash catcher,
  diagnostics. See `docs/FEATURES.md`.
