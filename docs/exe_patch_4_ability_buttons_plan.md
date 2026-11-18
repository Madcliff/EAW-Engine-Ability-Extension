# StarWarsG.exe patch plan: 4 ability buttons per unit group

Status (2026-11-12): **built, installed and working in game** — buttons 3 and 4 show the right icon,
fire, and recharge on their own cooldown, including aimed abilities (Force Storm). Applied with
`exe_patch/patch_starwarsg.py` (check / apply / restore). Stock exe kept as `StarWarsG.exe.orig`.

**Unit-swap button on the unit cards (2026-11-12, DLL only, needs in-game test):** `s_shield_24..47` (`0x181..0x198`)
= a half-size button in the lower right of unit card 0..23 (bones 17 right / 5 down from `s_select_00..23`, scale 0.5;
XML: TextButton with `ZZ_I_SA_REVAN_FORM_NEXT.TGA`, layer 6). Hook `0x14031cb9f` (`card_hook`) runs after the selection
bar fills a card (rdi = card, r14 = unit, [rsp+0x54] = 0x139 + slot) and calls the DLL through `zz_card_fn`
(`0x140cc02f8`); `cave_hide3` also hides `0x181..0x198`. The DLL shows the button for your own single units whose type is
in `Mods/<mod>/Data/zz_unit_swap.txt` ("FROM TO" lines), and its click handler (table +0x18) swaps the unit using the
engine routines behind Lua: create `0x14029f810(objmgr=[[0x140b15418]+0x18], type, player id, &pos, &{0}, 1, 0)`,
type by name = crc32(upper(name)) in the map at `[0x140b2f020+0x40]`, position/facing `0x1403a56b0` / `0x1403abb80(obj,
old+0x78)` / `0x1403a8710(obj, old+0x84)`, health = float at +0x5c (max `0x1403727a0(type, obj)`), despawn
`0x140488890(0x14004fd50(), obj)` (+ parent) then `0x140391310(obj, 1)`, select `0x1402bd2f0(objmgr, obj+0x50, player id)`.
Swaps are logged to `corruption/zz_ability_buttons.log`. Unit cards show hero *companies* (`[+0x348] != 0xff`, members via behaviour 0x16:
`[[beh+0x28]+0x110]`, count +0x18, array +0x10), so the list names companies (`Revan_Jedi_MW_I_Team` <-> `_II_Team`) and
the whole company is swapped: create the new company, move/face/heal its member, despawn the old company the way Lua
`Despawn()` does (each member: notify, notify parent, delete). If a created company has no single member it is undone.

**Tooltips + right-click for rows 3/4 (2026-11-12, needs in-game check):** both mouse-over paths that call the
ability tooltip builder `0x1402f3e20` only accepted ids `0x1a5..0x1d4`; hooks `0x1402e11db` -> `tip_a` and
`0x1402e379a` -> `tip_b` (in `.zzpatch`) also send `0x121..0x138` and `0x151..0x168` there. The right-click
(autofire) handler `0x14030edf0` had the same index == 1 group-key bug as the click handler (patched at
`0x14030ee33`), and rows 3/4 now get that handler in their +0x28 table slot (DLL only).

**Extended to 8 buttons (2026-11-12, confirmed in game):** fourth row = `s_health_24..47` (ids `0x151..0x168`,
unused because the selection bar is pinned at 24). `zzpatch.s`: button loop k = 2..7 (k 6/7 -> component `0x14b+k+b`),
unit-list pass and cleanup up to index 7, `cave_hide3` also hides `0x151..0x168` (moved to `0x140cc01ef`). Their
click-handler slots are empty and unrelocated, so only the DLL sets them (`DLL_ONLY_DATA_PATCHES`); the file patch
leaves row 4 unclickable. Mod side: `s_health_24..47` button components in CommandBarComponents.xml, a fourth bone row
in `i_tactical_controls.alo` (25.2 above row 3). Test unit Revan I: abilities 7/8 = SPRINT, STIM_PACK.
Next free block for a fifth row: `s_shield_24..47` (`0x181..0x198`).

**Now loaded as a DLL instead (2026-11-12):** `exe_patch/dll/powrprof.dll`, installed next to `StarWarsG.exe`,
applies exactly the same patches in memory at startup; the exe on disk stays stock. Needs the Steam launch option
`WINEDLLOVERRIDES="powrprof=n,b" ... %command%` (without it Proton uses its built-in powrprof and the game runs stock).
The DLL forwards the game's only powrprof import, `CallNtPowerInformation`, to `ntdll!NtPowerInformation`; it puts the
cave at RVA 0x7fc4c0 (padding of the last .text page) and the .zzpatch code in a page allocated at RVA 0xcc0000, so the
assembled code is reused unchanged. It checks the PE timestamp (0x67002393), SizeOfImage and every original byte first,
and changes nothing if anything differs (also if the exe still has the file patch). Result goes to
`corruption/zz_ability_buttons.log`. Source + `build.sh` (clang/lld-link, no CRT); `patch_data.h` is generated from
`patch_starwarsg.py`. Launch test: memory matched the file patch at all 22 code/cave sites, 24 table slots and the zz code.

Added after the original design, from in-game testing:
* icon/tooltip index and button slot-3 index patches (`0x14030ec45`, `0x14030ece7`);
* click handler index >= 1 uses the group key (`0x140346ecf`);
* ability 3/4 recharge dial computed in the new code (`[rbp+0x77]`, same rule as `0x1403108b0`);
* per-ability-type unit lists also built for abilities 3/4 (selection routine hooks `0x14031c4e8`,
  `0x14031c63d`) and cleaned up on deselect/death (`0x1402e9f32`). This code lives in an extra
  section `.zzpatch` (VA `0x140cc0000`, 0x200 bytes, appended to the file; see `zzpatch.s`).

**Extended to 6 buttons (2026-11-12, needs in-game test):**
* third row = the 24 unused selection components `s_select_24..47` (ids `0x121..0x138`): their component-table
  click handler (`0x140a174e0 + 72*id + 0x18`, a relocated pointer) is changed from `0x140346b90` to the
  ability-button handler `0x140346ea0`;
* selection slot limit pinned: `0x14031b5c5` `call 0x140347af0` -> `mov eax,23`, so the 48 `s_select` bones in
  the model never make the selection bar use those components for units;
* button loop moved into `.zzpatch` (`cave_loop6`, k = 2..5): abilities 5/6 use component `0x121+b` / `0x122+b`;
  unit-list pass and cleanup run for indexes up to 5; `.zzpatch` is now 0x400 bytes;
* mod side: `s_select_24..47` defined in CommandBarComponents.xml as ability-button components, and a third
  row of bones/meshes in `i_tactical_controls.alo` (25.2 above row 2).
* abilities 5/6 confirmed working in game; the empty third-row bar (the `s_select_24..47` components shown
  with no ability) is hidden by `cave_hide3` (hook `0x1402e7915` in the hide-all routine: for ids
  `0x121..0x138`, hide the component and its bone), installed 2026-11-12;
* Not covered: hover tooltips for the third row (the hover routines only recognise ids 0x1a5..0x1d4).

Original design notes follow.

Earlier status: design only. Target: Forces of Corruption 64-bit
`corruption/StarWarsG.exe`, version 1.121.859328 (12,428,800 bytes, dated 2024-11-03).

## What the engine does today

* A unit type's abilities live in a variable-length list (`type+0x1ab0` begin / `+0x1ab8` end).
  `0x140374b50(type, index)` bounds-checks against the real list size, so XML with 3+ abilities loads fine.
* Activation, readiness, recharge and autofire look abilities up **by ability type**
  (`0x1403986b0`, `0x14039bbd0`, `0x14039b480`), not by position. A 3rd/4th ability should already work
  if something triggers it; it just has no button.
* The selection bar (`0x14031b590`) groups selected units and, per group, calls the button routine
  `0x14030e660(cmdbar, b, type0, type1, ...)` **once**, where `b = startColumn + endColumn`.
* `0x14030e660` sets up two buttons:
  * button `b`   (component `0x1a5 + b`, `special_button_b`)    for the group's ability 0;
  * button `b+1` (component `0x1a6 + b`, `special_button_b+1`)  for ability 1, in a second block
    `0x14030e9a8 .. 0x14030edc0`. That block shows the type passed in `[rbp+0x67]` (caller's r9) and asks
    each unit for its ability with a hard-coded index (`mov edx,1` at `0x14030ea16`) to work out the
    ready/recharge/autofire state.
* Button components exist for `special_button_00..47` in the engine, but every special-button loop runs
  to `0x1a4 + count` where `count` (global `0x140b279f0`) is 24 and shared with the selection slots.

## The patch: run the ability-1 block again for abilities 2 and 3

Abilities 3 and 4 go on buttons `b+24` and `b+25`, the second row that sits directly above
`special_button_b` / `b+1` in the modified `i_tactical_controls.alo` (24 extra bones at +25.2 height).

### 1. Code edits inside `0x14030e660`

| Address | Original | New | Why |
|---|---|---|---|
| `0x14030e69a` (8 bytes) | `xor r14d,r14d` / `mov [rsp+0x20],rax` | `jmp cave_init` + 3 NOP | initialise the loop |
| `0x14030ea16` (5 bytes) | `mov edx,0x1` | `mov edx,[rbp+0x6b]` + 2 NOP | ability index = loop counter |
| `0x14030ec26` (6 bytes) | `add ecx,0x1a6` | `add ecx,[rbp+0x63]` + 3 NOP | button component = per-pass offset |
| `0x14030edc0` (8 bytes) | `movaps xmm7,[rsp+0xb0]` | `jmp cave_loop` + 3 NOP | after each pass, loop or finish |
| `0x14030e9a8` (7 bytes) | `lea rax,[rsi+0xbb]` | `jmp cave_entry` + 2 NOP | mark "block entered" (added during build: `[rsp+0x30]` is also a temp in the first half) |
| `0x14030ec45` (6 bytes) | `mov r8d,1` | `mov r8d,[rbp+0x6b]` + 2 NOP | icon/tooltip builder `0x14043eaf0` gets the right ability index (found in test 1: buttons showed ability 2's icon) |
| `0x14030ece7` (12 bytes) | `mov edx,1` / `mov rcx,rbx` / `lea r8d,[rdx+2]` | `mov edx,[rbp+0x6b]` / `mov rcx,rbx` / `mov r8d,3` | button data slot 3 = ability index, read back by the click handler and cooldown (test 1: cooldown followed ability 2) |

All four spots checked: no jump lands inside the overwritten bytes. `0x14030edc0` is also the target of
5 early exits; the loop code handles those (see guard below).

Scratch slots (unused halves of the routine's own home area):
`[rbp+0x6b]` = ability index k (upper half of the r9 home slot), `[rbp+0x63]` = component offset
(upper half of the r8 home slot; its low byte `[rbp+0x5f]` is the routine's flag and is untouched).

Click handler (found in test 2: buttons 3/4 did nothing when clicked):

| Address | Original | New | Why |
|---|---|---|---|
| `0x140346ecf` (9 bytes) | `cmp rax,1` / `jne` / `lea edx,[rax+3]` | `cmp rax,1` / `jb` / `push 4` / `pop rdx` | special-button click handler `0x140346ea0` used the group key (slot 4) only for index == 1; index 2/3 fell into the index-0 branch and targeted a group that doesn't exist |

Ability recharge countdowns are stored per ability **type** (`0x14042fa70`: `[base + type*4 + 0x13c]`),
so abilities 3/4 have their own countdowns; no patch needed there.

### 2. New code in the spare space at the end of `.text`

329 zero bytes at `0x1407fc4b7 .. 0x1407fc5ff`. The `.text` VirtualSize must be raised from `0x7fb4b7`
to `0x7fb600` so the loader maps them (the next section starts at `0x1407fd000`, so nothing moves).

```
cave_init:                         ; replaces the two instructions at 0x14030e69a
    xor   r14d, r14d
    mov   [rsp+0x20], rax
    mov   dword [rbp+0x6b], 1      ; k = 1  (stock ability-1 pass)
    mov   dword [rbp+0x63], 0x1a6  ; button b+1
    mov   qword [rsp+0x30], 0      ; guard: block not entered yet (block stores the group type here)
    jmp   0x14030e6a2

cave_loop:                         ; replaces movaps at 0x14030edc0
    cmp   qword [rsp+0x30], 0      ; block never ran (no ability 1 / early exit) -> finish
    je    finish
    mov   eax, [rbp+0x6b]
    cmp   eax, 3
    jge   finish
    inc   eax
    mov   [rbp+0x6b], eax          ; k = 2, then 3
    lea   ecx, [rax+0x1bb]         ; k=2 -> 0x1bd (button b+24), k=3 -> 0x1be (button b+25)
    mov   [rbp+0x63], ecx
    ; type shown on the button = ability k of the group's first unit
    mov   rsi, [rsp+0x30]          ; group's ability-0 type
    mov   r15, [rbp+0x4f]          ; command bar (block reuses r15 as a flag)
    lea   rax, [rsi+0xbb]
    lea   rax, [rax+rax*2]
    mov   rcx, [r15+rax*8+0x8]     ; group's unit array
    mov   rcx, [rcx]               ; first unit
    call  0x1403973b0              ; unit -> type
    mov   rcx, rax
    mov   edx, [rbp+0x6b]
    call  0x140374b50              ; type, k -> ability type (0 = none)
    test  eax, eax
    jz    finish                   ; no ability k: stop (button stays hidden)
    mov   [rbp+0x67], eax          ; type the block displays
    xor   r14d, r14d               ; block expects r14 = 0
    mov   rsi, [rsp+0x30]
    mov   r15, [rbp+0x4f]
    jmp   0x14030e9a8              ; run the ability-1 block again for ability k
finish:
    movaps xmm7, [rsp+0xb0]
    jmp   0x14030edc8
```
(About 150 bytes. Assembled with GNU `as`, which is installed; calls/jumps are rip-relative and are
re-checked against the disassembly before writing.)

### 3. Let the special-button loops cover 48 buttons (not the selection slots)

Each of these reads the shared count (24) only to build a special-button range; patch the read to a
constant 48 so buttons 24..47 are hidden/refreshed/clickable. Selection, health and shield slots keep 24.

| Address | Original | New |
|---|---|---|
| `0x1402dccfa`, `0x1402dcd3a` | `mov eax,[rip+..0x140b279f0]` (6 B) | `mov eax,0x30` + NOP (button lookup loop) |
| `0x1402e78a2`, `0x1402e7904` | same | same (hide-all loop) |
| `0x1402f59a5`, `0x1402f59f1` | same | same (find button by ability) |
| `0x1402e11e3` | `lea eax,[rdx+0x1a4]` (6 B) | `mov eax,0x1d4` + NOP (click range) |
| `0x1402e37a6` | `lea eax,[rcx+0x1a4]` (6 B) | `mov eax,0x1d4` + NOP (click range) |

Left alone on purpose: `0x1402e0d8e`, `0x1402e34d2`, `0x1402f5a81`, `0x14031c03a` (selection-slot ranges).

## Mod-side files needed

* `CommandBarComponents.xml` (submod override): `special_button_24..47` defined. The current override
  also adds `s_select/s_health/s_shield_24..47`; trim those back to 24 for this patch.
* `i_tactical_controls.alo` with the second row of 24 button bones (built earlier; kept in the
  scratchpad as `i_tactical_controls_row2.alo`), installed in `Mods/zz_mod_revrev/Data/ART/Models`.
* Units given 3rd/4th `<Unit_Ability>` entries with ability **types different from their first two**.

## How it would be applied

A Python script that: checks the exe's size/hash and every original byte listed above; refuses if
anything differs; backs up `StarWarsG.exe` to `StarWarsG.exe.orig`; writes the patch; and can restore.
Steam overwrites the exe on updates or "verify files", so the script is re-run afterwards.

## Risks / unknowns to settle in testing

1. Re-running the block also redoes its highlight call on button b (`0x14030ebee..0x14030ec1e`);
   expected harmless (same values), but button b could flicker if not.
2. Hotkeys: abilities 3/4 get no keyboard shortcut, click only.
3. Mixed groups: the button shows the *first* unit's ability k; units lacking it are treated as
   "not ready", the same way the stock code handles ability 1.
4. Multiplayer: a patched exe will desync with unpatched players.
5. Crash = most likely a register/stack mistake in the new code; the restore option brings the stock exe back.

## Test plan (needs you in game)

1. Patch + model + XML, start a skirmish/GC land battle with a unit that has 4 abilities.
2. Check: 4 buttons visible (2 on top row); clicking 3/4 fires the ability; recharge overlay shows;
   other units' buttons unaffected; selecting many groups still lays out correctly.
3. If it crashes on selecting the unit: restore, report, I adjust the new code.

## 2026-11-13: modifiers, auras and Force Storm (powrprof.dll)

### Mod_Multiplier on abilities 3-12 (fixed, installed, untested)
- XML `<Mod_Multiplier>NAME, value</Mod_Multiplier>` is stored as `float[13]` in the unit-ability entry at
  `+0xac + id*4` (reader: XML field type 0x4d, case `0x14051befe`; names/ids from table `0x140a433f0`:
  1 WEAPON_DELAY, 2 SHIELD_REGEN, 3 SHIELD_REGEN_INTERVAL, 4 ENERGY_REGEN, 5 ENERGY_REGEN_INTERVAL, 6 SPEED,
  7 TAKE_DAMAGE, 8 CAUSE_DAMAGE, 9 FIRE_RATE, 10 SCATTER_RADIUS, 11 TARGET_SPEED, 12 TARGET_TAKE_DAMAGE).
  Getter `0x140565990(entry, id)` (default 1.0 at `0x1407ffaf8`).
- `0x140398010(unit, id)` is the per-unit ability multiplier every consumer asks. It only checked list index 0 and 1
  (unrolled): extra-button abilities never applied their modifiers (Battle Meditation slowed Bastila, slot 1, not
  Revan, slot 4/5). DLL `zz_mod_mult` wraps it and multiplies in every further active ability the same way
  (`[unit+(t+0x3d)*16]` entry, byte +8 active, type 0x22 excluded as the engine does).

### Combat modifier slots (unit `[[obj+0xf0]+0x138]`, 11 lists of 0x20 bytes)
- Dispatcher `0x140536a70(mgr, id, value, &mode, &src, name, duration)` uses the COMBAT_MOD ids (table `0x140a434e0`,
  XML `Projectile_Combat_Mod`): id k -> slot (k-1)*0x20: 1 DEFENSE (damage taken) 0x00, 2 DAMAGE 0x20, 3 HEALTH 0x40,
  4 SHIELD 0x60, 5 ENERGY 0x80, 6 SPEED 0xa0, 7 FIRE_RATE 0xc0, 8 FOW_REVEAL_RANGE 0xe0, 9 FIRE_RANGE 0x100,
  10 ABILITY_RECHARGE_TIME 0x120, 11 TACTICAL_BUILD_TIME 0x140.
- Confirmed by `Out_Of_Combat_Defense_Adjustment` (unit type +0xde0) writing slot 0 and the ion stun writing speed
  0xa0 / shot rate 0xc0. Aura keys taken=/dealt=/speed=/fire_rate= = slots 0/0x20/0xa0/0xc0.

### Aura keys added (zz_auras.txt)
- `mod=NAME:value` (COMBAT_MOD names, via the dispatcher; +0.5 = x1.5).
- `mult=NAME:value` (Mod_Multiplier names; the value is the multiplier itself) - stored per unit in the DLL with an
  expiry and multiplied in by `zz_mod_mult`, so it behaves like an active ability's Mod_Multiplier (covers
  TARGET_TAKE_DAMAGE, WEAPON_DELAY, SCATTER_RADIUS, ...).
- Auras skip hidden sources/targets (`obj+0x3a2` bit 0); first 40 pulsing sources logged ("aura source:").

### Force Storm (takeover id 0x47) on the Interdictor: still not activating
- Chain log: button -> "can activate" (r8=0) ok -> command bar `0x1402e0920` (mode 3) -> targeting hand-off
  `call [cmdbar+0x2868]` at `0x1402e0b5a` with the same flags as Microjump (al=1 dl=1, entry+0x88 = 0) -> no
  activation. Microjump: same, then "can activate" with r8=1 and the activation `0x14038a350`.
- Effective_Radius -1 is the cast range for WEAKEN-case abilities (never in range); the DLL now sets negative values
  on WEAKEN-like entries to 1e6 (`fix_unlimited_ranges`), XML keeps -1. Not sufficient alone.
- Revan I's ground storm works because its XML type is WEAKEN_ENEMY (0x2a); as FORCE_STORM (0x47) it also failed.
  So an id-specific check remains between the target click and the order. Next: caller addresses of the chain
  hooks ("from" in the log) to find the function that issues Microjump's activation.

### Force Storm root cause found (2026-11-13 evening; fix built, not yet installed)
- The targeting callback `[cmdbar+0x2868]` = `0x140037ae0` only stores the targeting state in the input handler
  `0x140a60df0` (+0x928..: ability type at +0x948). On the target click the command dispatcher `0x140041f70` (same
  object) builds the order with a SIXTH per-id switch: `[handler+0x948]-5` -> byte table RVA `0x4409c` (bound 0x45,
  case table `0x44084`). WEAKEN_ENEMY = case 2 (`0x140043788`: new 0x268 record, fill `0x1404305d0`, queue
  `0x1403b01f0`); BUZZ_DROIDS (0x47) = case 4, INFECTION (0x42) = default -> takeover types never got an order.
  Also `cmp dword [rax+0x948],0x2a; je` at `0x140043628` (non-WEAKEN types take an extra call `0x1400418b0`).
- Fix: register_new_types copies the like= entry into `0x4409c`; a stub at `0x140043628` sends types marked in
  `g_weaken_like_tab` down the WEAKEN branch. The expansion (id=new) still needs this table extended and the
  dispatcher's own `cmp [..+0x948],0x4d` checks (0x140042ed9, 0x140043317, 0x140043386) raised.

### Other results that run
- mult= verified engine-side: `0x140398010` returns the aura values (SPEED 1.5, TAKE_DAMAGE 0.5, ... SHIELD_REGEN 2).
- Creation log: only 2 REVAN_JEDI_MW_I created that battle (from `0x14040120c` and `0x1406449aa`).

## Hero bar 2 -> 4 rows (2026-11-14, built, NOT installed; staged in `staged_hero_bar/`, see its README)

The top-right hero bar (galactic + tactical) is the component block 0x27d..0x2aa: `good_hero_frame` 0x27d,
`hero_slot_good00..10` 0x27e-0x288, `hero_hb_good00..10` 0x289-0x293, `evil_hero_frame` 0x294,
`hero_slot_evil00..10` 0x295-0x29f, `hero_hb_evil00..10` 0x2a0-0x2aa (shell models `I_MAIN_HERO_FRAME_REBEL/EMPIRE.ALO`,
stock only, in GameData/Data/models.meg; RevRev has no copy). XML entries: RevRev / submod CommandBarComponents.xml
`good_hero_frame` .. `hero_hb_evil10`. Click 0x140347810 (galactic: camera to hero 0x1403cd1b0; tactical 0x1402f64e0).
The engine hard-codes the id ranges (contiguous, so slots can't simply be appended):
* 0x1402e1044/104a mouse-over range (good slots); 0x1402fa8d6/9bd effect objects per slot (count = group size of
  slot 00 via 0x140347af0); 0x1402fcc25/6c frame colour; 0x140306c2d-c7c clear loop;
* 0x140311615-0x1403119ec timer-list mode (incl. effect index `[id*8-0x13f0]` at 0x140311800 / 0x1403118aa);
* hero list fill 0x14031af30: 0x14031af55-0x14031b11b (good slot edi from 0x27e, bar = slot+0xb, evil = 0x295,
  evil bar = good00+0x22, frames good00-1 / good00+0x16, ends 0x288 / 0x29f), cleanup 0x14031b3d9-0x14031b558
  (counts `r15-0x27e` / `r13-0x295`, frame ALT = min(count,6)-1 via vtable +0x300, `[id*8-0x13f0]`, `-0x14a8`).
DLL (`hero_bar_rows 4` in zz_settings.txt): the block is rebuilt at ids 1085..1174 of the enlarged table (frame,
22 slots, 22 bars per side, same order; 00..10 keep the stock names, 11..21 new; stock entries renamed
`zz_old_hero_...`) and the 49 sites above are pointed at it (`dll/hero_bar_data.h`, generated by `dll/gen_hero_bar.py`
from the stock exe; every site's full original instruction is checked at runtime, a mismatch only disables this
feature). No overlap with PATCHES / expansion / zz code; live audit of the running game 2026-11-14: all 49 sites
still stock. Models: `exe_patch/alo_hero_bar_rows.py` (slot/bar k = copy of k-11, 78.4 lower). Frame stays ALT0..5.

## 16 ability buttons (2026-11-14, built, DLL not installed yet)
* `zzpatch.s`: selection pass, cleanup and button loops run to ability index 15 (were 11). Wide layout (rows of 4)
  gets a fourth row (k 12-15 -> `zz_button_r4_`, 989 + b + col); narrow layout (rows of 2) k 12/13 -> row 7
  (1061 + b), k 14/15 -> row 8 (1085 + b). Hide-all now 965..1132 (rows 3-8 + swap buttons 1109..1132), tooltips
  965..1108. Reassembled (1022 of 1024 bytes); moved labels updated in `patch_starwarsg.py` (CAVE_HIDE3 0x140cc0275,
  TIP_A/B 0x140cc02cc/02f1, CARD_HOOK 0x140cc0316, ZZ_CARD_FN 0x140cc0358, ZZ_WIDE 0x140cc0360, GROUP_END 0x140cc0370).
* DLL `NEW_ROWS 6`: table rows 3-8 (`zz_button_r3_00`..`zz_button_r8_23`), swap buttons 1109..1132, hero bar block
  from 1133 (`gen_hero_bar.py` FIRST_NEW 1133, `hero_bar_data.h` regenerated).
* Mod: `CommandBarComponents.xml` rows 7/8 (copies of row 6), `i_tactical_controls.alo` rows 7/8 via
  `exe_patch/alo_ability_rows.py <src> <dst> 7 2` (each bone = row 6 + (row 6 - row 5) per extra row; 25.2 up).
