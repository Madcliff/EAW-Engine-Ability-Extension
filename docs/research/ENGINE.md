# Forces of Corruption engine research

The research behind the EAW Engine Ability Extension: how the 64-bit Steam `StarWarsG.exe` (Forces of Corruption,
1.121.859328) works in the areas the extension changes, and how each change is made. This chapter is the overview.
Exact addresses, config keys and patch sites are generated from the source into
[ENGINE_INDEX.md](ENGINE_INDEX.md), so this text explains and that one lists.

Conventions:

- Addresses are virtual addresses with the exe's image base, 0x140000000. "RVA" is the address minus the base.
- `[x+0x10]` means the 8-byte value at x+0x10. Offsets on objects are byte offsets.
- "Line N" refers to `dll/zz_ability_buttons.c`.
- Everything here was found by disassembly and confirmed by log output in the game, unless it is marked
  *unverified*.

| Document | What it covers |
|---|---|
| [ENGINE_INDEX.md](ENGINE_INDEX.md) | Generated: config keys, named engine addresses, patch sites, DLL pages, address index |
| [ability_type_map.md](ability_type_map.md) + [.csv](ability_type_map.csv) | The 75 stock ability type ids, names and their switch-table cases |
| [engine_ability_classes.md](engine_ability_classes.md) + [classes](engine_ability_classes.csv) / [fields](engine_ability_fields.csv) CSVs | The 85 XML ability classes (`<Abilities SubObjectList="Yes">`), their factories and field tables |
| [../../ability_expansion/CENSUS.md](../../ability_expansion/CENSUS.md) | Census of every per-type array and id check, for new ability ids |
| [../ability_id_checks.md](../ability_id_checks.md) | The 67 one-byte id checks the expansion widens (generated) |
| [../exe_patch_4_ability_buttons_plan.md](../exe_patch_4_ability_buttons_plan.md) | Original design of the extra ability buttons |
| [../FEATURES.md](../FEATURES.md) | Feature list with hook addresses |
| [../CONFIG.md](../CONFIG.md) | Config files and Lua functions, for modders |

## 1. The executable and how the DLL gets in

**Target.** `StarWarsG.exe` 1.121.859328, 64-bit, 12,428,800 bytes, SHA-256
`07daeeae…f723d018a4` (stock) / `f3c1fa3a…f2bd09efca` (import renamed). Built with MSVC: the code uses `std::string`
(buffer or pointer at +0, size +0x10, capacity +0x18, inline when capacity < 16), `std::map`, `std::list` and
`std::vector`.

**Loading.** The exe imports exactly one function, `CallNtPowerInformation`, from `POWRPROF.dll`. The installer
renames that import's 12-byte DLL name to `ZZ_SWFOC.dll`. It's the same length, so nothing else in the file moves.
The DLL exports the same function, forwarded to `ntdll!NtPowerInformation` (which is what the real powrprof calls).
The loader then maps `ZZ_SWFOC.dll` from the game folder before the exe's own code runs, and `DllMain` applies
everything to the running image. No `WINEDLLOVERRIDES` is needed under Wine/Proton.

**Patch model.** Every hook first compares the original bytes at its site. If they differ, that feature is left off
and the log says why, while the rest still installs. The core button patch is all-or-nothing: it reuses
code assembled for the patched exe (`zzpatch.s`, `cave.s` → `dll/patch_data.h`), so it needs the same addresses.
That code is placed at the same RVAs it was assembled for:

- the old code cave, in the zero padding after `.text` (RVA 0x7fc4c0, inside the last `.text` page);
- the `.zzpatch` code, in a page allocated directly after the image (RVA 0xcc0000).

Later features each allocate their own 64 KB unit after the image (list in
[ENGINE_INDEX.md §5](ENGINE_INDEX.md#5-dll-pages-at-fixed-addresses)). They have to stay within ±2 GB of the code so
that 5-byte `jmp rel32` hooks reach them.

**Hook techniques used**

| Technique | Where |
|---|---|
| Overwrite an instruction with `jmp stub`, replay the overwritten instructions in the stub, `jmp` back | Most features (fog targeting, cards first, damage hook, System Spy) |
| Copy a window of whole instructions (no rip-relative operand, nothing branching into it) into a stub with a fix-up inserted; replay twice when the fix-up would clobber flags | Command bar per-type lists (line 4336) |
| Raise a one-byte bound in place; above 0x7f, move the `cmp` plus at least 5 following bytes to a stub with a 32-bit immediate (opcode 0x83 → 0x81) and re-target its relative branches | Ability id expansion (67 sites) |
| Replace a vtable slot or a call target with a wrapper that calls the original | Force_Healing timers, Mod_Multiplier, unit ability update |
| Copy and enlarge a static table, then redirect every reference to it | Command bar component table (965 → 1,229+ entries) |
| Subclass the game window's procedure | Hotkeys (`#`, `[`, `]`) |
| Vectored exception handler | Crash catcher (logs first 8 distinct crash sites, then lets the exception continue) |

## 2. Core engine objects

| Thing | How to reach it | Notes |
|---|---|---|
| Game mode object | `[0x140b15418]` | `[+0x18]` = object manager. Mode (as Lua `Get_Game_Mode`): vt+0xe0, else int at 0x140b153fc. 0 = galaxy, 1 = land, 2 = space (also the menu background) |
| Object manager | `[[0x140b15418]+0x18]` | Live objects: `std::list` at +0x88; node +0x10 id, +0x18 object. Id lookup 0x1402aca60. Spatial lists: one per player (index player + 0x4c) plus a shared one (−1) |
| Player list | 0x140a16fd0 | +0x20 array, +0x28 count. By id 0x140294bc0; local player id 0x140294a70. Faction object `[player+0x68]` |
| Type manager | `[0x140b2f020]` | +0x40 = `std::map` crc32 → type. Names are upper-cased, then crc32 0x140215a30(buf, len, 0) |
| Category enum | 0x140b31020 | vt+0x20(enum, &std::string, &u64 mask): "Infantry \| Vehicle" → mask |
| Game time | frame counter `+0x10` of 0x14028a950(0x140b153e0, 0) × seconds per frame (0x140b0a344) | As Lua `GetCurrentTime`. Frames per second at 0x140b0a340 |
| Area search | 0x1402a8fb0(objmgr, −1, player index or −1, &pos, radius, max, 0) → list (+8 array, +0x10 count) | Blasts use it. In space most objects are only in the per-player lists, so the DLL searches every list and merges |
| Create object | 0x14029f810(objmgr, type, player id, &pos, &extra, 1, 0) | Core of `Create_Generic_Object` |

**Game object fields used**

| Offset | Field |
|---|---|
| +0x50 | Object id |
| +0x5c | Current health (float). Max: 0x1403727a0(type, obj) |
| +0x78 / +0x84 | Position / facing (setters 0x1403abb80 / 0x1403a8710, as `Teleport_And_Face`) |
| +0xf0 → +0x138 | Combat modifier store (§4) |
| +0x100 | Ability/behaviour state; also the stealth fields (§4) |
| +0x1e8 | ABILITY_COUNTDOWN data (§3) |
| +0x2d0 | Hardpoint list (+8 array, +0x10 count); hardpoint +0x20 type (type+0x4d = destroyable), +0x28 health, +0x6e destroyed |
| +0x348 | ≠ 0xff for companies; members in behaviour 0x16 |
| +0x384 + id | (hardpoint *type*) `Fire_When_In_<ability>_Mode` bytes |
| +0x3a2 bit 0 | Hidden (reinforcement pool, transports, Lua `Hide`) |
| +0x3d0 + id×16 | Ability slots (+8 = active byte); the slot walk starts at +0x3e0 = id 1 |

## 3. The ability system

**Ids.** Active abilities (`<Unit_Abilities_Data>` types) have fixed ids 1..0x4c, 77 slots including 0. The name
list is an enum object at `[0x140b310c0]`, built by 0x1405dea20, and names are registered with 0x140341ce0(list, id,
&std::string). The full id ↔ name table is in [ability_type_map.md](ability_type_map.md). Passive and galactic
abilities are a separate system of XML classes ([engine_ability_classes.md](engine_ability_classes.md)).

**Dispatch.** The id selects behaviour through several byte-table switches, all indexed by id:

| Switch | Code | Byte table RVA | Index |
|---|---|---|---|
| Unit ability slot walk | 0x1403984b8 | 0x39861c | id |
| Has ability | 0x1403986d1 | 0x39880c | id |
| Activation | 0x14038a532 | 0x38c520 | id − 1 |
| Can activate | 0x14039b640 | 0x39b904 | id − 1 |
| Targeting / button | 0x1402e0aec | 0x2e0bcc | id − 5 |
| Order dispatcher (input handler 0x140a60df0, method 0x140041f70) | in 0x140041f70 (cases at RVA 0x44084) | 0x4409c | id − 5 |

The order dispatcher also checks `[handler+0x948]` (the targeted type) against 0x4d three times with a *memory*
compare, and has an extra `WEAKEN_ENEMY`-only call at 0x140043628.

**Per-type data.**

- Static table at 0x140b2f2e0, 0x30 bytes per id (icon `std::string` +0, flags +0x20..+0x2c), filled by 0x14043fab0.
- ABILITY_COUNTDOWN data at `[unit+0x1e8]`, 0x2c8 bytes, allocated at 0x1403901aa. Layout: +0x8 dword[77] time
  left, +0x13c dword[77] recharge total, +0x270 byte[77] ready flags, +0x2c0 last frame. Save/load serializes
  exactly 0x4d entries.
- Command bar per-type unit lists (§5).
- Faction SFX lists at `[player+0x68]` +0x7a0 / +0xc70 / +0x1140 / +0x1610.

**New types by takeover** (`slot=`, line 3226). A new type takes an id no unit uses. Its name is registered for that
id right after the list is built, and the id's switch cases and per-type table entry are copied from the `like=`
type. The order dispatcher needs both its switch case and the `WEAKEN_ENEMY` call, or no order is ever made.
Activation handlers that pass a literal type id to the activate call 0x1403a3e20 are patched to pass the actual id
(r13d), so cooldown and state belong to the new type.

**New ids by expansion** (`id=new`, line 3944, census in [CENSUS.md](../../ability_expansion/CENSUS.md)). Ids from
0x4d up to 0x4c + N. Read-only per-type data is redirected to the `like=` type, and per-type state goes to side
storage:

1. Switch byte tables and per-type table getters are extended.
2. Single range checks are raised by N; above 0x7f they are widened.
3. and 4. Per-object side storage: where stock code computes `idx` and then accesses `[base + idx*scale + disp]`,
   the `idx` computation is replaced so the unchanged access lands in a DLL block.
5. The countdown object is grown in place.
6. The unit slot walk moves to side slots after id 0x4c.

New ids aren't saved. The order dispatcher's memory compares were missed by the first register-only census and
added later.

**Fixes to stock behaviour.**

- *Force_Healing timers* (line 1215): every `Force_Healing_Ability` block on a unit shared one countdown
  (`[[unit+0x100]+0x25c]`), so a second block never fired. The class update (vtable slot RVA 0x8c7438 →
  0x1406fbb20) is wrapped so each (unit, block) keeps its own countdown. Negative `Heal_Percent` is kept (load check
  0x1406fc99c, jbe → jmp).
- *Mod_Multiplier* (line 5112): 0x140398010(unit, mod type) only counted ability indexes 0 and 1. The wrapper also counts
  every further index of the unit type's ability list.
- *Unlimited range* (line 5040): `Effective_Radius -1` made `WEAKEN_ENEMY`-type abilities refuse every target. The
  DLL turns it into a very large radius.

## 4. Combat: damage, modifiers, states

**Damage function** 0x1403a9e30(target, damage type, amount in xmm2, source) handles every hit: weapons, abilities
and auras. `damage_hook` puts an entry stub on its first instruction (`mov [rsp+0x20],r9`, 5 bytes). The stub saves
the argument registers and xmm2 and calls `damage_pre`, which implements `invuln`, `absorb` and `reflect`. It never
touches stack arguments.

**Combat modifier store** `[[obj+0xf0]+0x138]`: 11 slots of 0x20 bytes, where slot k holds COMBAT_MOD id k+1. Each
slot is a `std::map` keyed by mode. Its vector holds 0x30-byte entries: +0 value, +4 expiry frame, +8 name hash,
+0x10 source.

- Add function 0x1403fe810 (one entry per mode and source, overwritten on each call). Rewriting the same entry every
  pulse made health bars flicker, so the DLL only extends the expiry when the value is unchanged.
- Dispatcher 0x140536a70(manager, COMBAT_MOD id 1..11, value, &mode, &source, name, duration), as
  `Projectile_Combat_Mod` uses it. Ids: 1 defense / damage taken, 2 damage dealt, 6 speed, 7 fire rate (as the ion
  stun). Its stacking check 0x140536640 is skipped, otherwise entries were never extended.
- Sources are (object id, type) plus a per-aura key at +0x10, so different auras and different casters stack. The
  engine uses −1 for normal sources and −2 as a wildcard when removing.

**Mod_Multiplier** values (`<Mod_Multiplier>` types: `TAKE_DAMAGE`, `CAUSE_DAMAGE`, …) go through 0x140398010. The
damage function applies `TAKE_DAMAGE` to weapon *and* ability hits, while the old `taken=` / `dealt=` combat-mod
slots miss ability damage.

**States the DLL drives with the engine's own code**

| State | How |
|---|---|
| Confuse | `ForceConfuseAbilityClass` 0x140716ef0 does it per target: the CONFUSE behaviour (id 0x53, created by name 0x1404c3520, attached 0x14038c570), started with 0x1406364e0(behaviour, frames, particle) |
| Stealth | Fields at `[unit+0x100]`: +0x2a4 stealthed, +0x294 alpha target, +0x29c/+0x2a0 fade time/rate, +0x2b8 frames left. Shared by `Stealth_Ability` 0x1405926e0 and `Force_Cloak_Ability` 0x140714890. Uncloak 0x140592d00(unit, fade seconds). A unit without a cloak ability has no countdown, so the DLL keeps the timer |
| Hardpoint repair | Max health 0x140385ae0, set health 0x140387ca0, revive as a station repair does: 0x140387d10(hp, 0) |
| Conversion | The engine's Force Corrupt conversion |
| Lightning bolt | 0x140481ce0(manager 0x140a2a850, &target, &source, &name, 1), then handed to the scene: `[game]` vt+0x100 → vt+0x78 → vt+0xa8 (as `Play_Lightning_Effect`) |
| Position / hide | `Teleport_And_Face` setters (§2), hidden bit +0x3a2 (as Lua `Hide`) |

**Object auras** (line 2931) are driven from the per-object update 0x1403a6b80. Its call to each unit's ability
update (0x14037da80 at 0x1403a72f1) goes through a stub that then calls `object_aura_tick`. That runs on the game
thread every frame while units with abilities exist, and walks the object list. It is skipped on the galaxy map.

## 5. Command bar and UI

**Command bar object** 0x140b27f60 (a static; referenced by about 800 instructions). It holds two per-type unit list
arrays, 24 bytes per type, 0x4d entries each: +0x1188 groups units by their first ability, +0x18c0 by their other
abilities. An entry is a small vector (vtable 0x140800488, data, count +0x10, capacity +0x14). For new ids, every
index computation gets a stub that adds an offset, so the access lands in one shared side block.

**Ability buttons.** The button routine 0x14030e660 sets up ability 0 on button b, then runs a block for ability 1
on button b+1. The patch runs that block again for abilities 2..15 on the extra rows. 0x140374b50(type, k) returns
the ability type of button k, and spell books hook it. The icon builder 0x14043eaf0(table, out, ability *index*,
unit type) reads by index, so spell books remap it too. A ready button is set up through vtable +0x80 (greyed out),
+0xf0 (recharge fill), +0x2f0 and +0xd8 (selected), as at 0x14030e8a0..0x14030e912.

**Component table** 0x140a174e0: 965 entries of 72 bytes, with the click handler at +0x18. The engine binds entries
by name to `CommandBarComponents.xml` and to bones in `i_tactical_controls.alo`. The DLL copies the table to RVA
0xcd0000 and redirects every reference, plus the binding loop's count (`cmp edi,965` at 0x140347deb). It adds:

- ability rows 3–8 (`zz_button_r3_00` …);
- 24 swap buttons;
- 96 control panel buttons;
- the 4-row hero bar block.

New entries copy `special_button_00` (id 0x1a5). Card slot s uses ids 0x109+s (card, `s_select`), 0x139+s (health
bar) and 0x169+s (shield bar). Get a component with 0x140347b50(id), and set slot / bone with 0x140353ad0 /
0x14034ba10.

**Selection bar layout.** Selection routine 0x14031b590. Card groups are laid out in a loop over the group key t,
which is the units' first ability type, so groups appear in type-id order. Card entries have stride 0x38: +0 group
key, +0x18 unit pointer array, +0x28 count.

- `double_cards_first` replaces the loop's start (0x14031c80f) and next step (0x14031d077) to walk a permutation.
- `wide_shared_groups` fixes the cave's rows-of-4 test (zz+0x10c) and the group-end column rule (zz+0x3bd) for
  groups that span several card columns.

**Hero bar.** Stock component ids 0x27d..0x2aa (a frame plus 11 slots and 11 bars per side) are rebuilt at a new id
block with 22 slots per side. 49 code sites are repointed (`dll/hero_bar_data.h`, generated by
`dll/gen_hero_bar.py` from the stock exe).

**Targeting and fog.** The command bar hands targeting to the input handler with `call [cmdbar+0x2868]`
(0x140037ae0) at 0x1402e0b5a. Stack argument 0x38 becomes handler+0x958, the "ignore fog" byte. The cursor routine
0x140039980 refuses a fogged point when that byte is 0 (fog test 0x14035f3b0). `fog_targeting` hooks the join of the
per-id targeting switch (0x1402e0b25) to set the byte per id. Objects under fog are never picked (0x14003ed90 /
0x14003f330), and that part isn't patched.

## 6. Lua

The script function registration routine 0x140546c70 jumps at 0x140549106 to a trampoline that calls the DLL's
`register_fns(script)`. Functions are registered with 0x140247000(script, function object, name). The function
object is built by 0x140249c20 with `Create_Position`'s method table (0x1408943c0; slot 10 = call(this, script,
args)) as the template. Game object wrappers are unwrapped with 0x1405791e0.

Return values: a number is a 0x18-byte LuaNumber (vtable 0x1407ff930, +8 refcount, +0x10 double). The results table
comes from 0x14024a250, with values pushed into its vector at +0x10 / +0x18 / +0x20, as the stock `GetCurrentTime`
(0x1405428b0) does.

## 7. Galactic map

Every galactic ability of a unit uses the unit type's `Galactic_Influence_Range` (type +0x1a00; ≤ 0 = own planet).
System Spy's area method (vtable slot 21, 0x14070f950) reads it at 0x14070f99c and 0x14070f9dd, and both reads are
redirected for `galactic_ranges`. The ability entry's `Name=` is an MSVC string at +0x18. More on galactic ability
classes and ranges: [engine_ability_classes.md](engine_ability_classes.md).

## 8. Open questions and unverified

- **Save games:** new ids (`id=new`) aren't serialized, because the countdown save loops 0x4d entries and the chunk
  format depends on the count.
- **Lift:** does the engine keep a lifted land unit off the ground? Space units should lift fine.
- **Reflect:** it follows a projectile's parent, but not every hit source has one.
- **Fogged objects:** units in the fog can't be targeted, because the object picker (0x14003ed90 / 0x14003f330)
  isn't patched.
- **Stuck animations** after stock channelled abilities (Force Lightning, Berserker) are being traced with
  `diagnostics on`.
- **Not yet verified in game:** spell book page flipping, ids above 0x88, teleport vortex timing, group teleport,
  the cast-animation fix.

## 9. Keeping this up to date

Every change that adds or moves a hook, an engine address or a config key updates the docs in the same change:

1. Comment the hook in `dll/zz_ability_buttons.c`: what the engine code does, the addresses, and why the hook is
   safe. Give config keys an inline or declaration comment that names the key.
2. Run `python3 -I tools/gen_engine_index.py` to regenerate [ENGINE_INDEX.md](ENGINE_INDEX.md).
   `make_release.sh` refuses to package while the index is out of date.
3. Update the matching chapter here, [FEATURES.md](../FEATURES.md), [CONFIG.md](../CONFIG.md) for any key, and
   `CHANGELOG.md`.
4. Move items into or out of §8 as they are verified in game.
5. Run `release/make_pdf.sh` to rebuild the PDF (it's also attached to each release).
