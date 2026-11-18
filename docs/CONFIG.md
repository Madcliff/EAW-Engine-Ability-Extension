# Configuration reference (for modders)

The DLL reads plain text files from the running mod's `Data/` folder, which it finds through the `MODPATH=` launch
argument. If the game runs without `MODPATH`, it reads them from the game's `corruption/` folder. The files are read
once, when the game starts.

Every file is optional, and a feature whose file or setting is missing stays off. All files share these rules:

- one entry per line;
- `#` starts a comment, also in the middle of a line;
- words are separated by spaces or tabs;
- `key=value` pairs can't contain spaces (write category masks as `Infantry|Vehicle`);
- names are not case-sensitive;
- switches accept `1/0`, `on/off`, `yes/no` and `true/false`;
- files can be up to 256 KB, with up to 64 words per line.

The DLL logs what it loaded, and every name it couldn't resolve, to `corruption/zz_ability_buttons.log`. A full list
of keys generated from the source is in [research/ENGINE_INDEX.md](research/ENGINE_INDEX.md#1-config-file-keys).

## `zz_settings.txt`: feature switches

`name value`, one per line. Example: [examples/zz_settings.txt](examples/zz_settings.txt).

| Key | Default | Effect |
|---|---|---|
| `ability_expansion N` | 0 | Room for N new ability ids after the stock 0x4c (max 128). Needed for `id=new` ability types. Above about 50 the DLL widens the engine's one-byte id checks |
| `diagnostics` | off | on = debug hooks plus full logging; off = only problems are logged after startup |
| `weapon_inaccuracy` | off | Applies the engine's unused XML inaccuracy values (`Targeting_Fire_Inaccuracy`, `Fire_Inaccuracy_Distance`) |
| `lua_functions` | 1 | Registers the `ZZ_*` Lua functions (see below) |
| `hero_bar_rows` | 2 | `4` = 4-row hero bar, 22 heroes per side. Needs the hero bar XML and frame models |
| `fog_targeting` | off | Ability reticles may aim at fogged ground. Fogged units still can't be clicked as targets |
| `double_cards_first` | off | Card groups holding a double-card unit are laid out first in the selection bar |
| `ui_first T1,T2,…` | – | Order among those first groups; a listed single-card type is pulled ahead of the normal groups too |
| `wide_shared_groups` | off | A card group holding a double-card unit always gets rows of 4 and the control panel column |
| `damage_hook` | on | Hooks the engine damage function; needed by the aura keys `invuln`, `reflect` and `absorb` |
| `panel_card_pads` | on | The control panel column uses its card buttons as a plain background, with its health bars hidden |
| `galactic_ranges` | off | System Spy uses its own range from `zz_galactic_ranges.txt` |
| `ability_type_map` | off | Logs the stock ability id and name table at startup |

## `zz_ability_types.txt`: new ability types

```
NEW_NAME  slot=UNUSED_TYPE  like=EXISTING_TYPE  [key=value ...]
NEW_NAME  id=new            like=EXISTING_TYPE  [key=value ...]
```

A new type behaves like an existing type (`like=`): same targeting, activation and button behaviour, but with its own
id, button and cooldown. Use `NEW_NAME` in XML (`<Type>NEW_NAME</Type>`) and in Lua like any stock type. There are
two ways to get an id:

- **`slot=UNUSED_TYPE`** takes over a stock id that no unit or script in the mod uses. It's saved in save games.
  Free slots in a typical mod: `BUZZ_DROIDS`, `INFECTION`, `SABER_THROW`, `AVOID_DANGER`, `CAPTURE_VEHICLE`,
  `TARGETED_REPAIR`, `CABLE_ATTACK`, `TRACTOR_BEAM`, `CONCENTRATE_FIRE`, `ION_CANNON_SHOT`, `MAXIMUM_FIREPOWER`,
  `FIRE_LOBBING_SUPERWEAPON`, `SUPER_LASER`, `LEECH_SHIELDS`, `BLAST`, `AFTERBURNER`.
- **`id=new`** gives a brand-new id (0x4d, 0x4e, … in file order). It needs `ability_expansion N`. Its cooldowns
  aren't saved, so they reset when a save loads. `icon=` has no effect: set `<Alternate_Icon_Name>` on the unit's
  ability entry instead.

| Key | Effect |
|---|---|
| `like=TYPE` | Stock type whose behaviour is copied (required) |
| `slot=TYPE` / `id=new` | Where the id comes from (one is required) |
| `icon=file.tga` | Button icon (`slot=` types only) |
| `targeting=location` | Aim at any ground point, also on top of units (as `PROXIMITY_MINES`) |
| `targeting=both` | Aim at a point or an object (as `WEAKEN_ENEMY`). The default is the `like=` type's targeting |
| `fog=off` | Keep the stock fog-of-war check for this type when `fog_targeting` is on |
| `aura=NAME` | Activating makes the caster pulse that aura from `zz_auras.txt` (one without `object=`) |
| `aura_secs=N` | How long, in seconds. Otherwise the ability's `<Expiration_Seconds>`, otherwise 10. Switching a toggle off stops it |
| `teleport=1` | Moves the caster to the target point |
| `depart_delay=S` | Seconds the caster stands frozen (casting) before vanishing |
| `arrive_delay=S` | Seconds until it reappears at the target |
| `depart_object=T` / `arrive_object=T` | Object or particle spawned where the caster leaves and arrives |
| `group_radius=R` *(next release)* | Teleport takes the caster's own movable units within R along, keeping formation |
| `group_max=N` *(next release)* | At most N group members (default 12; up to 64 units teleport at once) |
| `group_categories=MASK` *(next release)* | Which units go along (default `Infantry\|Vehicle\|Air\|LandHero`) |
| `anim=NAME` | Caster animation on activation (Play_Animation names without `_00`: `FL_ATTACK`, `FTK_HOLD`, …) |
| `anim_loop=1` | Loop that animation |
| `anim_hold=S` | Keep the caster in place for S seconds while it plays |

For `like=WEAKEN_ENEMY` types, `Effective_Radius` is the cast range, and `-1` means unlimited.

## `zz_auras.txt`: auras

```
Name  key=value key=value ...
```

An aura pulses around a source and affects the units in range. There are three ways to run one:

1. **Ability block:** give a unit a `Force_Healing_Ability` block whose `Name` is the aura's name. The block then
   pulses on its `Heal_Interval_In_Secs`, with radius `Heal_Range` unless `radius=` is set. A negative
   `Heal_Amount` / `Heal_Percent` adds flat / % damage, and positive values heal.
2. **Object aura:** `object=Type[,Type]` makes every live object of those types pulse the aura by itself every
   `interval=` seconds. No Lua is needed. Use this for storm vortices, domes and markers.
3. **Lua:** `ZZ_Aura(object, "Name" [, radius [, now]])` pulses once. With `now = GetCurrentTime()` and `interval=`
   set, a script can call it on a fast tick and the aura keeps its own frequency.

A new ability type can also start an aura with `aura=` (see above).

Stacking: different auras stack, and the same aura from different units stacks too (two storms both apply). Repeated
pulses from one unit refresh their own modifier entry. `unique=1` and `stack=N` limit stacking.

**Targeting and timing**

| Key | Effect |
|---|---|
| `target=` | `enemy` (default), `ally`, `both` or `self` (the source unit only) |
| `radius=` | Range |
| `categories=MASK` | Only these units, e.g. `Infantry\|Vehicle` |
| `interval=S` | Seconds between pulses (object auras default to 1) |
| `duration=S` | How long modifiers last after each pulse (default 3; refreshed while in range) |
| `once=1` | Each source pulses only once (a burst) |
| `random=P` | Each target is affected with probability P per pulse |
| `stack=N` | At most N sources affect one target at a time |
| `unique=1` | One modifier entry per target whatever the number of sources |
| `cancel=A,B` | No effect on targets inside aura A or B |
| `requires=A,B` | Only targets inside every listed aura (combos) |
| `grow=F` / `shrink=F` | Radius grows or shrinks by F over the source's lifetime (`lifetime=`, else 10 s) |
| `object=Type,…` | Object aura (see above) |
| `lifetime=S` | Object auras: the DLL removes a carrier object S seconds after it appears (backstop if its script stops) |
| `effect=Type` | Particle shown on each target |

**Damage and healing**

| Key | Effect |
|---|---|
| `damage=` / `damage_percent=` | Flat damage / share of max health per pulse (0.01 = 1%) |
| `damage_type=Damage_…` | Damage type (default `Damage_Force_Corruption`) |
| `heal=` / `heal_percent=` | Flat / % heal per pulse |
| `hardpoints=1` | Heal goes to a ship's damaged hardpoints first, then the hull |
| `revive=1` | With `hardpoints=1`, also brings destroyed hardpoints back |
| `drain=F` / `self_heal_from=F` | The source heals F × the damage dealt |
| `ramp=F` / `ramp_max=N` | Damage and heal grow by F per pulse a target stays inside (counting at most N pulses, default 10) |
| `chain=N` | Damage jumps N times from enemy to enemy |
| `chain_range=` / `chain_falloff=` | Jump range (default radius / 2) and multiplier per jump (default 0.7) |
| `shield_regen=X` / `shield_drain=X` | Add or remove X shield points per pulse (`X%` = a share of max shield) |
| `invuln=1` | Targets take no damage (needs `damage_hook`) |
| `reflect=F` | Targets send F × the damage they take back at the attacker (needs `damage_hook`) |
| `absorb=Type[:F]` / `absorb=all[:F]` | Damage of that type is cancelled and heals F × its amount (default 1; needs `damage_hook`) |

**Modifiers** (these last `duration=`)

| Key | Effect |
|---|---|
| `mult=NAME:value` | Any `<Mod_Multiplier>` type; the value is the multiplier itself (1.25 = +25%). Up to 8. Names: `WEAPON_DELAY`, `SHIELD_REGEN`, `SHIELD_REGEN_INTERVAL`, `ENERGY_REGEN`, `ENERGY_REGEN_INTERVAL`, `SPEED`, `TAKE_DAMAGE`, `CAUSE_DAMAGE`, `FIRE_RATE`, `SCATTER_RADIUS`, `TARGET_SPEED`, `TARGET_TAKE_DAMAGE` |
| `mod=NAME:value` | Any engine combat modifier; +0.5 = ×1.5. Up to 8. Names: `DEFENSE`, `DAMAGE`, `HEALTH`, `SHIELD`, `ENERGY`, `SPEED`, `FIRE_RATE`, `FOW_REVEAL_RANGE`, `FIRE_RANGE`, `ABILITY_RECHARGE_TIME`, `TACTICAL_BUILD_TIME` |
| `mark=F` | Targets take F more damage from everything (same as `mult=TAKE_DAMAGE:1+F`) |
| `taken=` / `dealt=` | Older damage taken / dealt modifiers. `dealt=` misses ability damage, so prefer `mult=CAUSE_DAMAGE` / `mult=TAKE_DAMAGE` |
| `speed=` / `slow=F` | −0.5 = half speed; `slow=0.3` = `speed=-0.3` |
| `fire_rate=` | −0.5 = fire half as often |
| `recharge=` | −0.5 = abilities used inside get half their cooldown |
| `cooldown=F` | With `target=both`: allies' cooldowns × (1 − F), enemies' × (1 + F) |
| `stun=S` | Targets can barely move or fire for S seconds |
| `disarm=S` | Targets can't fire for S seconds |
| `confuse=S` | Enemies fight for the source's side for S seconds (the engine's Force Confuse) |
| `fear=S` | `disarm=S` plus a push of 80 units/s |
| `convert=1` | Enemies hit permanently change to the source's owner (Force Corrupt) |

**Movement and stealth**

| Key | Effect |
|---|---|
| `pull=X` / `push=X` | Units move X units/s towards / away from the centre |
| `inner=R` | Where pulling stops |
| `hold=1` | Units that reach `inner` are held there until they leave or the aura stops |
| `pull_z=1` | Also pull towards the source's height (space) |
| `lift=S` | Raise targets `lift_height=` (default 40), hold for S seconds, drop them for `lift_damage=` |
| `cloak=1` / `cloak_fade=S` | Units inside are stealthed as Force Cloak does (use `target=ally`) |
| `reveal=1` | Stealthed enemies inside are uncloaked |
| `summon=Type,count,cap` | Each pulse spawns `count` units for the source's owner, with at most `cap` alive per source |

**Lightning**

| Key | Effect |
|---|---|
| `strike_radius=R` | Each pulse strikes a random point within R (Force Lightning Storm) |
| `bolt=NAME` | `LightningEffectTypes.xml` effect drawn for strikes and chain jumps |
| `sky=H` | Height the strike bolts come from (default 900) |
| `flash=T1,T2` | Particle or object types spawned at each strike point |

## `zz_spell_books.txt`: ability pages

```
UnitType   2-9 | 10-16,20 | 17-19
```

Numbers are the unit's abilities in XML order (`Unit_Abilities_Data`, 1-based). You can write ranges and lists, and a
list keeps the order you write. `|` separates pages, up to 16 pages with at most 15 abilities each. Button 1 always
shows ability 1, because the command bar groups units by their first ability. In battle, `[` and `]` flip the pages
of every spell-book unit. Abilities on hidden pages keep their cooldowns, toggles and auras.

## `zz_wide_cards.txt`: double-card units

One unit or company type per line. The unit's card group gets an empty card column next to it, so its abilities show
in rows of 4 and the column can hold the control panel.

## `zz_panel_buttons.txt`: control panel buttons

```
UnitType  SLOT  ICON.TGA  ACTION
```

The unit must be listed in `zz_wide_cards.txt`. Slots 1–8 are the second card, a 2 × 4 grid counted from the top
left. Slots 9–12 are under the unit's own icon (2 × 2), shown only while the card slot under the unit is empty.
`ICON` is a name in the command bar atlas (`MT_Commandbar.MTD`). `ACTION` is one of:

- `prev` / `next`: previous / next spell book page;
- `page`: next page, showing the page number;
- `swap`: switch to the unit's other form;
- `none`: icon only.

Spell-book units get slots 1–3 by default (previous, next, page number), and a line for one of those slots replaces
the default. Lua can take a unit type's panel over entirely; see `ZZ_Panel_Button` below.

## `zz_unit_swap.txt`: unit swap

```
FROM_TYPE  TO_TYPE
```

A selected `FROM` unit you own gets a swap button on its card (hotkey `#`). Clicking it replaces the unit with `TO`
in place, keeping owner, position, facing and health fraction. Company names swap the whole company, which is
recommended for heroes.

## `zz_galactic_ranges.txt`: System Spy range

```
NAME  RANGE
```

`NAME` is a `System_Spy_Ability`'s `Name="…"` or a unit type; entry names are checked first. `RANGE` uses the same
units as `<Galactic_Influence_Range>`, and 0 means the unit's own planet only. Needs `galactic_ranges on`.

## Lua functions

These are registered in every script when `lua_functions` is on (the default).

| Function | What it does |
|---|---|
| `ZZ_Aura(object, "Name" [, radius [, now]])` | Pulses an aura from `zz_auras.txt` once around `object` |
| `ZZ_Pull(object, radius, step [, inner [, heroes [, categories [, hold [, pull_z]]]]])` | Moves enemy units within `radius` by `step` towards `object` (negative = away). `hold=1` freezes units that reach `inner`; `hold=-1` releases everything this object holds. `heroes` defaults to 1, `categories` to `"Infantry \| Vehicle"` |
| `ZZ_Heal_Hardpoints(object, radius, amount [, percent [, revive [, categories]]])` | Heals the hardpoints of own and allied ships in range. `revive=1` (default) also restores destroyed ones |
| `ZZ_Panel_Button(unit_type, slot, icon, action)` | Defines a control panel button. `action` is a number (a Lua button: clicks are queued) or `"prev"`, `"next"`, `"page"`, `"swap"`, `"none"`. The first Lua button for a type replaces its default panel |
| `ZZ_Panel_Clear(unit_type [, slot])` | Removes Lua buttons for a type (all, or one slot) |
| `ZZ_Panel_Get_Click(unit_type)` | Returns `tag, slot` of the oldest queued click, or `nil` |
| `ZZ_Log_Lua_Error(...)` | Writes a line to the DLL log (used by the Lua guard) |

`Scripts/Library/zz_PanelButtons.lua` in Revan's Revenge wraps the panel functions (`ZZ_Panel_Setup`) for use in a
unit's own object script.
