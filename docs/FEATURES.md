# Features (technical reference)

Addresses are exe virtual addresses (image base 0x140000000) in StarWarsG.exe 1.121.859328.

## Feature list

| Feature | What it does | Configured in |
|---|---|---|
| 16 ability buttons | Up to 16 ability buttons per unit group (stock: 4), in rows of 2 or 4, with tooltips | `zz_wide_cards.txt` (always 4-wide units) |
| New ability types | Abilities with their own id that behave like an existing type (`id=new like=X`); own icon, cooldown, targeting | `zz_ability_types.txt` |
| Ability id expansion | Room for up to 128 new ability ids (204 types in total). All 67 one-byte id checks are mapped and widened to 32-bit when needed | `zz_settings.txt`: `ability_expansion N` |
| Spell books | Per-unit pages of abilities; button 1 fixed, buttons 2–16 show the current page; `[` / `]` flip pages | `zz_spell_books.txt` |
| Object auras | Effects that pulse from units or ability objects: damage, % damage, heal, % heal, modifiers (damage dealt/taken, speed, fire rate), pull/hold, conversion, hardpoint repair and revival, lightning strikes | `zz_auras.txt` |
| Aura keys (batch 2) | invuln, disarm, push, fear, cooldown (allies faster / enemies slower), self_heal_from, ramp / ramp_max, grow / shrink (radius over lifetime), chain / chain_range / chain_falloff (enemy-to-enemy jumps with bolts), summon=Type,count,cap, unique (no stacking between casters). Logs "aura chain:", "aura summon:" | `zz_auras.txt` |
| Aura keys (batch 3) | shield_regen / shield_drain (points or %), random, stack, reflect, absorb (entry hook on damage 0x1403a9e30 -> damage_pre, stub page 0x140d50000), cancel / requires (who is inside which aura) | `zz_auras.txt`; `zz_settings.txt`: `damage_hook on` |
| Aura keys (batch 4) | lift / lift_height / lift_damage (raise, hold, drop; lift_update from the aura tick); cloak / cloak_fade (Force Cloak's activation on [unit+0x100] + DLL timer, ended by the engine uncloak 0x140592d00), reveal (engine uncloak on stealthed enemies); reflect follows a non-unit hit source to its parent | `zz_auras.txt` |
| Lightning strikes | Strike-mode auras draw engine lightning bolts with impact particles (Force Lightning Storm) | `zz_auras.txt` (`strike_radius`, `bolt`, `flash`, `sky`) |
| Teleport | `teleport=1` abilities move the caster to the target with a vortex at both ends | `zz_ability_types.txt` |
| Cast animations | Play a caster animation on activation, optionally holding the unit in place | `zz_ability_types.txt` (`anim`, `anim_loop`, `anim_hold`) |
| Unit swap | Swap a unit for its other form in battle (swap button on the card, or `#`), keeping position and health | `zz_unit_swap.txt` |
| Hero bar | 4 rows of hero icons (22 per side) in the top-right bar | `zz_settings.txt`: `hero_bar_rows 4` |
| Weapon inaccuracy | Turns on the engine's unused weapon inaccuracy values from XML | `zz_settings.txt`: `weapon_inaccuracy on` |
| Fog-of-war targeting | Ability reticles may aim at fogged ground (stock refuses it for BARRAGE / mines / SUMMON / CORRUPT_SYSTEMS / `targeting=location` types); hook at the command bar targeting join 0x1402e0b25 sets the handler's ignore-fog byte (+0x958) per id; `fog=off` per type keeps the check. Fogged units still can't be picked | `zz_settings.txt`: `fog_targeting on` |
| Double cards first | Tactical selection bar lays out card groups holding a double-card unit first (stock: first-ability type id order), so they start at column 0 with rows of 4 + panel column; `ui_first` orders among them. Hooks the card loop counter (0x14031c80f start, 0x14031d077 next) | `zz_settings.txt`: `double_cards_first on`, `ui_first T1,T2` |
| Wide shared groups | Card groups are keyed by the units' first ability type, so a double-card unit can share a group with other cards (Revan's Interdictor + other INTERDICT ships) and the group spans 2+ card columns. Such a group now always gets rows of 4 (stub at 0x140d40000 from zz+0x10c, log "rows of 4 (double-card group)") and group_end leaves the column after its last column empty for the control panel (zz+0x3bd jne nopped; log "panel: shared double-card group") | `zz_settings.txt`: `wide_shared_groups on` |
| System Spy own range | System Spy uses its own galactic range (by ability Name= or unit type) instead of the unit's Galactic_Influence_Range shared with the production modifiers; hooks the two +0x1a00 reads in System Spy's area method (0x14070f99c / 0x14070f9dd) | `zz_settings.txt`: `galactic_ranges on`; `zz_galactic_ranges.txt` |
| Lua functions | `ZZ_Pull`, `ZZ_Aura`, `ZZ_Heal_Hardpoints`, `ZZ_Log_Lua_Error` for scripts | `zz_settings.txt`: `lua_functions 1` |
| Control panel | 12 buttons per double-card unit: 8 on the empty second card, 4 under the unit icon. Lua defines them (`ZZ_Panel_Button` / `ZZ_Panel_Clear` / `ZZ_Panel_Get_Click`; in the unit's own object script via `ZZ_Panel_Setup`, `Scripts/Library/zz_PanelButtons.lua`), else the spell book defaults and `zz_panel_buttons.txt` | unit scripts, `zz_panel_buttons.txt` |
| Crash catcher | Logs crashes with the code address and recent model loads | always on |
| Diagnostics | Debug hooks plus full logging; off = no debug hooks, only problems are logged | `zz_settings.txt`: `diagnostics on/off` |

## Performance notes

- Object auras run about 10 times a second, only in battles (skipped on the galaxy map).
- The per-tick object walk uses hash sets. Pulled units are freed by the DLL as soon as their storm or dome is gone.
- With `diagnostics off`, no debug hooks are installed and the log stays small.

## Limits

| Thing | Limit |
|---|---|
| New ability ids / types | 128 (setting cap; the next real wall is probably ~255) |
| Abilities per unit | one per type id, so up to ~204; 16 visible at once, more with spell book pages (15 per page, 16 pages) |
| Aura definitions | 128 |
| Aura sources per tick / timer pairs | 256 / 512 |
| Objects hit per aura search | 1,024 |
| Units held by pulls | 256 |

New ability ids are not saved: their cooldowns reset when a save loads.

