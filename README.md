# EAW Engine Ability Extension (`ZZ_SWFOC.dll`)

An engine extension for **Star Wars: Empire at War – Forces of Corruption** (64-bit Steam `StarWarsG.exe`
1.121.859328). It removes hard-coded engine limits on abilities and adds new ability mechanics for mods to use. It
was made for the Revan's Revenge submod `zz_mod_revrev`, but any mod can switch its features on with plain text
files in its `Data/` folder.

All changes are made in memory when the game starts, by the extension's own DLL. On disk, the only change to the
exe is one renamed import (`POWRPROF.dll` → `ZZ_SWFOC.dll`), and no system DLL is replaced. Works on Windows and on
Linux / Steam Deck (Proton).

## For players: install

1. Download the newest zip from [Releases](https://github.com/Madcliff/EAW-Engine-Ability-Extension/releases) and
   extract it.
2. **Windows:** double-click `Install.bat`.
   **Linux / Steam Deck:** run `./install.sh` in a terminal in the extracted folder.
3. Start the game with your mod as usual.

Run the installer again after every Steam update or *Verify integrity of game files*. To remove the patch, use
`Uninstall.bat` or `./install.sh uninstall`.

**Step-by-step guide, options and troubleshooting: [docs/INSTALL.md](docs/INSTALL.md)**

## What it adds

- **Up to 16 ability buttons per unit** (stock: 4), in rows of 2 or 4, with tooltips; **spell books** with pages
  of abilities that you flip with `[` / `]`
- **New ability types**: up to 128 new ability ids. Each behaves like an existing type but has its own icon,
  cooldown and targeting
- **Object auras**: damage, heal, buffs and debuffs, pull / push / lift, fear, conversion, shield drain, chain
  lightning, summons, cloaking and more. They pulse from units or ability objects
- **Lightning strikes**, **teleport** abilities with a vortex, and **cast animations**
- **Unit swap** in battle (switch a unit to its other form, keeping position and health)
- **Hero bar** with 4 rows (22 heroes per side)
- **Control panel**: 12 extra buttons for double-card units, defined from Lua
- **Fog-of-war targeting**: ability reticles can aim at fogged ground
- **Weapon inaccuracy**: switches on the engine's unused XML inaccuracy values
- **System Spy** can use its own galactic range
- **Lua functions** for scripts (`ZZ_Pull`, `ZZ_Aura`, `ZZ_Heal_Hardpoints`, `ZZ_Panel_Button`, …)
- **Crash catcher**: logs crashes with the code address and recently loaded models

Full technical list with engine addresses, performance notes and limits: [docs/FEATURES.md](docs/FEATURES.md).

## For modders: configuration

The DLL reads its configuration from the running mod's `Data/` folder, which it finds through the `MODPATH=`
launch argument. If the game runs without `MODPATH`, it reads the files from the game's `corruption/` folder
instead. Each file is optional, and a feature whose file or setting is missing stays off.

**Every key, default and Lua function: [docs/CONFIG.md](docs/CONFIG.md).**

| File | What it configures |
|---|---|
| `zz_settings.txt` | Feature switches, one `name value` per line (example: [docs/examples/zz_settings.txt](docs/examples/zz_settings.txt)) |
| `zz_ability_types.txt` | New ability types (`id=new like=X`, icon, cooldown, targeting, `teleport`, `anim`, `fog`) |
| `zz_auras.txt` | Object aura definitions |
| `zz_spell_books.txt` | Spell book pages per unit type |
| `zz_wide_cards.txt` | Units that always get 4-wide (double) cards |
| `zz_panel_buttons.txt` | Default control panel buttons |
| `zz_unit_swap.txt` | Unit swap pairs |
| `zz_galactic_ranges.txt` | System Spy ranges |

`zz_settings.txt` keys: `ability_expansion N`, `diagnostics on|off`, `weapon_inaccuracy`, `lua_functions`,
`hero_bar_rows 4`, `fog_targeting`, `double_cards_first`, `ui_first`, `wide_shared_groups`, `damage_hook`,
`panel_card_pads`, `galactic_ranges`, `ability_type_map`. Switches accept `on/off`, `1/0`, `yes/no` and
`true/false`.

The log is `corruption/zz_ability_buttons.log`. Every feature reports there whether it was installed. If the exe
differs from the expected bytes at a hook site, that feature stays off and the log says so. Use `diagnostics on`
when developing and `diagnostics off` for release builds of your mod.

Known limits:

- New ability ids aren't saved, so their cooldowns reset when a save loads.
- The DLL only finds the mod through `MODPATH=`. With Steam Workshop launches (`STEAMMOD=`) it reads the files from
  the game folder instead.

## Engine research

How the engine works, and how each change is made, is documented in
[docs/research/ENGINE.md](docs/research/ENGINE.md). It covers core objects, the ability system, damage and
modifiers, the command bar, Lua and the hook techniques.
[docs/research/ENGINE_INDEX.md](docs/research/ENGINE_INDEX.md) is generated from the source by
`tools/gen_engine_index.py` and lists every config key, named engine address, patch site and DLL page. Each release
attaches everything as one PDF (`EAW-Engine-Research.pdf`); build it locally with `release/make_pdf.sh`.

Changes that add a hook, an address or a config key update these docs in the same commit (ENGINE.md §9), and
`make_release.sh` refuses to package while the generated index is out of date.

## Building from source

Requirements: `clang`, `lld-link`, `llvm-dlltool` and `python3`. The build cross-compiles from Linux and links no
C runtime. It also needs a **stock** `StarWarsG.exe` 1.121.859328 (by default, the Steam install), because
`dll/gen_hero_bar.py` reads the original instruction bytes from it.

```bash
dll/build.sh
```

The build writes `dll/ZZ_SWFOC.dll`. For testing, install it with `./install.sh`, which uses `dll/ZZ_SWFOC.dll`
when no DLL sits next to the script. To make a release zip:

```bash
release/make_release.sh 0.1.0
```

That writes `dist/EAW-Engine-Ability-Extension-v0.1.0.zip` with the DLL, both installers, the guide, the license
and checksums.

| Path | What |
|---|---|
| `dll/zz_ability_buttons.c` | DLL source (everything) |
| `dll/build.sh` | Build script; also regenerates `patch_data.h` / `hero_bar_data.h` |
| `install.py`, `install.sh` | Installer (Linux, and Windows with Python) |
| `install.ps1`, `release/*.bat` | Windows installer (no Python needed) |
| `release/make_release.sh` | Builds the release zip |
| `patch_starwarsg.py`, `zzpatch.s`, `cave.s` | Code patches and code-cave assembly (turned into `dll/patch_data.h`) |
| `patch_import_name.py` | Older developer tool that only renames the exe import (`--check`, `--revert`) |
| `ability_expansion/CENSUS.md` | Map of the engine's ability tables and id sites |
| `docs/ability_id_checks.md`, `tools/map_id_checks.py` | The 67 one-byte ability id checks and the script that maps them |
| `docs/exe_patch_4_ability_buttons_plan.md` | Original design notes |

## Not yet verified in game (2026-11-17)

Spell book page flipping, ability ids above 0x88, the teleport vortex timing, and the cast-animation fix. Stuck
animations after stock channelled abilities (Force Lightning, Berserker) are being traced with `diagnostics on`.
The Windows installer has been tested with PowerShell 7 but not yet on a Windows PC with Windows PowerShell 5.1.

## License

GPL-2.0. See [LICENSE](LICENSE). Star Wars: Empire at War is © Lucasfilm / Disney and Petroglyph. This project
doesn't include any game files; the installer patches your own copy.
