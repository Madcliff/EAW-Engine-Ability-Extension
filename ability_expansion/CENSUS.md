# Expanding EaW FoC ability ids beyond 0x4c — census (started 2026-11-13)

Goal: add new ability ids (0x4d+) as real engine types instead of taking over unused ids
(the current, working approach: Data/zz_ability_types.txt `slot=` / `like=`).

## Facts
- Ability name list (enum object) at `[0x140b310c0]`, built by `0x1405dea20` (called at `0x14046f218`).
  Ids 7..0x4b are named; valid ids are 1..0x4c (77 slots incl. 0). Register a name: `0x140341ce0(list, id, &std::string)`.
- Checks against the count: 77 sites in 65 functions (`ability_type_sites.txt`), forms `lea eax,[id-1]; cmp eax,0x4b`,
  `cmp id,0x4c`, loops `cmp i,0x4d`. Some sites are other enums (e.g. `0x140035e40` family checks a second arg ≤ 6;
  `0x1400047da` is an HRESULT switch) — to be filtered.
- Id switches (byte table → dword case table): has-ability `0x1403986d1` (bytes RVA 0x39880c), slot walk `0x1403984b8`
  (0x39861c), activation `0x14038a532` (0x38c520, id-1), can-activate `0x14039b640` (0x39b904, id-1),
  targeting/button `0x1402e0aec` (0x2e0bcc, id-5). `0x14055e818` is NOT ability (save-game chunk reader).
- `WEAKEN_ENEMY`'s activation case passes the id literally (`mov edx,0x2a` at `0x14038a664`).

## Per-type arrays (from `idtrace.py`, see `idtrace_accesses.txt`)
Static (copy to a larger table and redirect, like the command-bar component table):
- per-type table `0x140b2f2e0`, 0x30 bytes/id (icon std::string +0, flags +0x20..+0x2c); filled by `0x14043fab0`;
  getters `0x14043eab0/ead0/fa10/fa30/fa50/fa70/fa90`, `0x14043eaf0/ebc0/ec10/ec50/eff0/f340/f6e0`.
- the switch byte tables above (each needs entries for new ids).

In live objects (the hard part — their sizes and following fields are fixed):
| array | object | entry | notes |
|---|---|---|---|
| `id*0x10 + 0x3d0` (+8 byte flag) | unit (game object) | 16 B | ability slots; indexed as `[unit + (id+0x3d)*16]`; 13 sites in 8 fns (`unit_array_index_refs.txt`) + loop `0x140398470` + fixed reads in `0x14039c3a0` |
| `id + 0x384` | HARDPOINT TYPE (`[hardpoint+0x20]`), not the unit | 1 B | XML flags `Fire_When_In_<ability>_Mode` (Defend +0x385 = id 1, Turbo +0x38d = id 9, Power_To_Weapons +0x3a1 = id 0x1d); 77 bytes, followed by `Fire_When_Deployed` (+0x3d1) etc.; read in `0x140384850` (2 sites) |
| `id*4 + 0x8` | ability countdown data `[unit+0x1e8]` | 4 B | ends at 0x13c |
| `id*4 + 0x13c` | same | 4 B | ends at 0x270 — contiguous with the previous |
| `id + 0x270` | same | 1 B | ends at 0x2bd; object has one more field at +0x2c0 |
| `id*0x18 + 0x18c0` (+8 list, +0x10 count) | command bar, a GLOBAL at `0x140b27f60` | 24 B | per-type selection groups (`0x1402e0570`, `0x1402e0730`, `0x1402e0920`, `0x14031b590`); object referenced by 792 instructions (535 lea of its start) |
| `+0x7a0` / `+0xc70` / `+0x1140` / `+0x1610` (each 16 B x 77, packed, end +0x1ae0) | faction object `[player+0x68]` | 16 B | XML fields `SFXEvent_GUI_Toggle_Non_Hero_Ability_On/_Off` and `SFXEvent_GUI_Enemy_Toggle_Non_Hero_Ability_On/_Off` (field type 0x4c = per-ability-type SFX list, descriptors at `0x140a3c670..0x140a3c6d0`); filled by the generic XML reader `0x14051a280` case 0x4c (has its own id bound check); read in `0x14042f460` as `(id+0xc7)*16` and `(id+0x161)*16` |

## Objects found so far
- **Ability countdown data**: allocated 0x2c8 bytes at `0x1403901aa`, constructor `0x140562970`, stored at
  `unit+0x1e8`. Layout: +0x8 dword[77], +0x13c dword[77], +0x270 byte[77], +0x2c0 qword. Accessed via
  `[[behaviour+0x28]+0x1e8]` by the ABILITY_COUNTDOWN behaviour (descriptor at `0x140a2b690`: create `0x14042f640`,
  0x40-byte behaviour object; accessors `0x14042f6a0..0x14042fde0`, e.g. `0x14042f8e0` = recharged check).
  Save/load: `0x140562ab0` loops 0x4d entries through the chunk reader `0x140220710` -> arrays are serialized
  per entry (save format depends on the count).
- **Unit**: arrays at +0x384 (byte[77]) and +0x3d0 (16 B[77]) are mid-object (fields continue after +0x8a0).
- Not this: the 0x268-byte object built at `0x14042fe60` (type 0x2b, ability id at +0x18, flag +0x24c) is a
  command/event record that carries an ability id — its id field needs no array change.

## Approach options per object
1. Arrays at the end of an object: raise the allocation size (the `operator new` constant in its constructor) and,
   for packed arrays, re-offset every access to the later arrays (e.g. all `+0x13c` / `+0x270` uses in that class).
2. Arrays mid-object (unit): keep the stock array for ids <= 0x4c; send new ids to per-object side storage owned by
   the DLL (keyed by object, freed via the object's destructor hook), with a stub at every indexed access.
3. Save/load: find the serializer of each object; arrays may be written with their fixed size.

## Id checks (filtered, `id_checks_classified.txt`)
76 of the 77 are real ability-id checks; only `0x1400047da` (an HRESULT switch) is unrelated. The "second index
<= 6" family `0x140035e40/35f00/36060/37940/37a00/37ae0` and `0x140429da0/429e60` store an ability id into a
record/message without indexing an array (range checks only). Every check must accept the new top id.

## Totals so far (sites to patch)
| item | sites |
|---|---|
| id range checks | 76 (one constant each) |
| switch byte tables | 5 tables, entries for each new id (copy/extend) |
| per-type table `0x140b2f2e0` + getters | relocate (≈14 getters + fill `0x14043fab0`) |
| command bar array | 22 instructions / 7 functions |
| faction SFX arrays (4 packed) | indexed 2 + XML reader case 0x4c + faction ctor/dtor (`0x14033a580`/`0x14033c160`) |
| countdown object | ≈20 in its class + ≈16 outside + allocation |
| unit slot array | 13 indexed + walk loop + reader + saver + 2 setup loops + activation byte write + fixed reads |
| unit byte array +0x384 | 2 reads + init/save (not yet found) |
| name list | register new names (already done by the takeover code) |
Roughly 180-200 individual sites. Save games: unit reader/saver, countdown reader/saver write exactly 77 entries.

## Plan per object (draft)
1. Static tables (per-type table `0x140b2f2e0`, switch byte tables): copy into larger DLL tables, redirect refs.
2. Command bar array (global singleton): move the whole per-type array (all ids) to a DLL buffer and patch only the
   instructions that index it (≈10 found by the tracer + its constructor/clear/destructor), instead of moving the
   792-reference object.
3. Faction arrays (+0xc70, +0x1610): few objects; same as 2 but per faction (side buffer keyed by faction object),
   plus the Factions.xml loader that fills them.
4. Countdown data (0x2c8, `unit+0x1e8`): allocate larger at `0x1403901aa` and relay out the packed arrays (patch the
   0x13c / 0x270 / 0x2c0 offsets in every method of the class, the constructor `0x140562970` and the serializer
   `0x140562ab0`), or give new ids a tail region and stub the indexed accesses.
5. Unit arrays (+0x384, +0x3d0): per-unit side storage for new ids, stub at each indexed access (13 + loops +
   copy/ctor/dtor/save).
6. Raise the real id checks (77 sites minus the unrelated ones) from 0x4c to the new top id.
7. Save games: decide whether new ids are saved at all (the serializers write 0x4d entries).

## Access counts (exe-wide search, 2026-11-13)
- Countdown class code: ctors `0x140562970`/`0x1405629b0` (memset 0x2b5, +0x2c0 = 0); reader `0x140562ab0` (6 loops
  `cmp edi,0x4d` over +0x270 and the dword arrays); saver = vtable slot 0 `0x140562d30` (`mov esi,0x4d` loop over +0x8,
  +0x13c, +0x270, and +0x2c0); vtable slot 1 `0x1405629f0` (+0x2c0). Allocation `0x1403901aa` (0x2c8).
- Command bar array: 22 instructions in 7 functions (`cmdbar_array_refs.txt`; the other hits there are unrelated
  objects with fields at the same offsets): indexed in `0x1402e0570`, `0x1402e0730`, `0x1402e0920`, `0x140307190`;
  whole-array loops in `0x14031b590` (refresh) and `0x1402e0730`; probable init/teardown `0x1402d9890`, `0x1402dac80`.
- Faction arrays: indexed only in `0x14042f460` (2 sites, `(id+0xc7)*16`, `(id+0x161)*16`); probable ctor/dtor
  `0x14033a580` / `0x14033c160` (lea of both +0xc70 and +0x1610); loader still to find. `faction_offset_refs_raw.txt`
  is the unfiltered offset search (most hits are other classes, e.g. the unit type in `0x14036xxxx`).
- Unit slot array (+0x3d0, 16 B x 77): 13 indexed (`unit_array_index_refs.txt`); walk loop `0x140398470`;
  enabled-byte write in activation `0x14038c464` (`[rbx+rax*8+0x3d8]`); save-game READER `0x14039c3a0` (loop of 77:
  `add rcx,0x3d; shl rcx,4; add rcx,unit` -> `0x14039ca90`, plus fixed reads of +0x3e0/+0x3e8); SAVER `0x1403a5ad0`
  (pointer loop from +0x3d0, step 0x10, count 0x4d -> `0x1403a6900`); unit setup `0x140388720` and `0x140388b60`
  (each clears 77 slots in a 0x10-step loop). Probable unit-to-unit copy `0x140472560` (lea +0x3e0 on two objects) —
  to confirm. Unit save files therefore hold exactly 77 slots.
- Hardpoint-type byte array (+0x384, 77 B, `Fire_When_In_<ability>_Mode`): read twice in `0x140384850`; filled by the XML reader (bool fields). The unit has no array at +0x384 (that region holds separate fields: +0x39c, flags +0x3a0..+0x3a7 incl. hidden +0x3a2, +0x3a8 ...).
- Countdown object: class vtable `0x140899a90`; ctor `0x140562970` (and a copy at `0x1405629b0`) does
  memset(+0x8, 0, 0x2b5) — exactly the three packed arrays — then sets the dword at +0x2c0. Uses through
  `[unit+0x1e8]` (`countdown_refs_via_unit1e8.txt`, which also contains other classes' +0x1e8 fields): idx*4+0x8 x8,
  idx*4+0x13c x4, +0x270 x1 (+ forms with the pointer as index register), +0x2c0 x3, in ~17 functions. Relayout =
  change alloc 0x2c8, memset 0x2b5, offsets 0x13c / 0x270 / 0x2c0 in all of these + the vtable methods + serializer.

## Decision: save games (2026-11-13)
New ids are NOT saved: their per-type state (cooldowns, enabled flags, slots) resets when a save loads. The unit
reader/saver (`0x14039c3a0` / `0x1403a5ad0`) and countdown reader/saver (`0x140562ab0` / `0x140562d30`) keep looping
over the stock 77 entries and never touch the new-id storage, so saves stay compatible both ways.

## Design refinement: read-only data vs state
Read-only per-type data needs no new storage: at each access a new id is replaced by its like= id, so it inherits
that type's data (per-type table flags, the 5 switch tables, hardpoint Fire_When_In_X_Mode flags, faction SFX lists).
Only per-type STATE needs side storage: unit slots (+0x3d0), countdown arrays, command bar groups.

## Implementation plan (stages; nothing new-id is enabled until stage 6)
Constants: NEW = number of new ids (start with 8 -> ids 0x4d..0x54), TOP = 0x4c + NEW, COUNT = TOP + 1.
1. Static tables in the zz page / DLL memory:
   - per-type table: copy 0x140b2f2e0 (0x4d x 0x30) into a COUNT x 0x30 table; redirect the ~14 getters and the
     filler `0x14043fab0` (rip-relative refs to 0x140b2f2e0) — same technique as the command-bar component table.
   - switch byte tables (has-ability 0x39880c, slot walk 0x39861c, activation 0x38c520, can-activate 0x39b904,
     targeting 0x2e0bcc): copy each, extended with entries for the new ids (default = that switch's default case,
     or the like= type's case), and change the disp32 in each `movzx eax,BYTE PTR [base+idx+disp]` (they are
     image-base relative, so the zz page is reachable).
2. Range checks: per site, raise 0x4b/0x4c/0x4d by NEW — EXCEPT loops that walk stock storage (unit setup loops,
   reader/saver, countdown memset/reader/saver), which stay at 77, and get a second pass over the side storage
   only where needed (setup = clear the side slots; reader/saver = none, per the save decision).
3. Side storage (DLL-owned, keyed by object pointer, created lazily, freed by hooking the owner's destructor or
   validated by id lookup):
   - unit: 16 B x NEW slots + 1 B x NEW flags;
   - countdown object: 4 B x NEW, 4 B x NEW, 1 B x NEW;
   - faction: 4 x 16 B x NEW (SFX lists; entries are filled by the XML reader case 0x4c);
   - command bar (global): 24 B x NEW.
4. Access stubs: each indexed access gets a jump to a stub: `if id <= 0x4c` run the original instruction, else
   compute the side-storage address and do the same operation there. One stub per site (≈60).
5. Name list: register the new names on ids 0x4d.. (registration code exists — register_new_types).
6. Enable: zz_ability_types.txt gets `id=new` (instead of slot=) to use a fresh id; behaviour like= copies the
   switch entries and per-type table entry exactly as the takeover does.
7. Test plan: a unit with one new-id ability (Force Storm moved off BUZZ_DROIDS), check button, cooldown, activation,
   save/load (cooldown resets), and the log.

## Stage 2 list: id checks
- 68 single-id checks: raise (`checks_single_raise.txt`).
- Loops over all ids (`checks_loops.txt` + two that end in jge: selection groups `0x14031d07f`, countdown reader
  loops `0x140562b1f..`):
  | loop | does | decision |
  |---|---|---|
  | `0x14042fa20` in `0x14042f910` | countdown update, calls recharge handler `0x14042f460` per id | EXTEND (new cooldowns must tick) |
  | `0x1404378e8` in `0x1404376f0` | has-ability + can-activate + table flag per id (AI ability choice?) | EXTEND |
  | `0x14063640a` in `0x140636260` | has-ability + table flag per id (AI/autofire?) | EXTEND |
  | `0x14057f4a3` in `0x14057f430` | recharge checks per id (Lua query?) | EXTEND |
  | `0x14057ffe4` in `0x14057ff10` | has-ability, `0x1403a78b0(unit,id)` per id | EXTEND |
  | `0x1403985dc` in `0x140398470` | unit slot walk with id switch | EXTEND |
  | `0x14031d07f` in `0x14031b590` | selection-bar groups per id | EXTEND (else no buttons) |
  | `0x140062ffb` in `0x140061fe0` | string list over ids (debug/cheat?) | keep 77 |
  | unit reader/saver, countdown reader/saver/memset, unit setup clears | stock storage | keep 77 (side storage cleared separately) |

## Build progress
- 2026-11-13: module `install_expansion()` in dll/zz_ability_buttons.c, setting `ability_expansion N` in
  Data/zz_settings.txt (0/absent = off; nothing patched). Data block at image+0xcf0000 (64 KB, RWX).
  - Stage 1a DONE (built, untested): 5 switch byte tables copied and extended (new-id entries = like= id's case),
    bound imm8 raised by N, table disp32 redirected. Sites verified before writing.
  - Stage 1b DONE (built, untested): 7 per-type table getters remap new ids to like= via `g_id_like[]` stubs.
  - Stage 3/4 unit slots DONE (built, untested in game): side store keyed by unit pointer (4 MB pool, 32768-entry
    hash), cleared by hooks on the unit setup entries `0x140388720`/`0x140388b60`; the 13 `lea DST,[ID+0x3d]; add
    DST,DST` sites call generated stubs (stock ids unchanged; new ids get idx = (side - unit)/8 so the unchanged
    `[unit+idx*8(+8)]` access hits the side slot). Emitter output verified by native compile + objdump.
  - Not yet: getters that take the id another way (`0x14043eaf0/ebc0/ec10/ec50/eff0/f340/f6e0`: icon/text name
    lookups), stages 2-7.

## Next steps
- Start the DLL expansion module: config (number of new ids), side storage, stage 1 tables, then stubs; keep it
  disabled (no new ids registered) until every stage is in, verifying stock bytes at each site at startup.
1. For each array: exe-wide search of all access forms (indexed, `lea base`, loops with the entry stride, copies,
   ctor/dtor/serializer); identify the object class (vtable), allocation size and constructor.
2. Filter the 77 checks to real ability-id checks.
3. Decide option 1/2 per object; write the patch list.

## Progress 2026-11-13 (built, expansion off by default, untested)
- **Countdown object: DONE (relayout).** `exp_install_countdown`: object grown in place for M = 0x4d+N
  (array 2 at 8+4M, bytes at 8+8M, dword at align4(bytes+M), size +8); 34 sites verified against stock bytes
  (disp32 0x13c/0x270/0x2c0/0x134, memset 0x2b5, size 0x2c8 at alloc + delete, serializer fold `add rax,0x4f`,
  update loop bound `cmp esi,0x4d` at 0x14042fa20 -> M). Serializer/saver still 77 entries.
- **Command bar: DONE.** There are TWO per-type list arrays in the static object 0x140b27f60: +0x1188 (first
  ability) and +0x18c0 (other abilities), 24 B entries {vtable 0x140800488, data, count, cap}. `exp_install_cmdbar`:
  jmp-stubs at the 10 index-forming sites (0x1402e058c, 0x1402e075c, 0x1402e0940, 0x1403071cb, 0x14030e6c2,
  0x14030e9a8, 0x14030db02, 0x1402e9ee6, 0x14031c310, 0x14031c373) add D (or 3D) for t >= 0x4d -> side block in
  g_exp+0xc000 (array 1 new ids at S, array 2 at S+0x4d*24, one D for both). Also the 4 index sites in the zz cave
  (found by byte pattern at install), the refresh's unrolled count clears (stub at 0x14031b9b5 also zeroes side
  counts) and the card layout loop over all types (0x14031d07f, bound -> M). Stubs verified by native emit+objdump.
- Remaining: faction SFX arrays (0x14042f460 + XML case 0x4c), hardpoint +0x384 remap (0x140384850), other per-type
  table functions (0x14043eaf0/ebc0/ec10/ec50/eff0/f340/f6e0 - note 0x14043eaf0 = icon builder, has a `cmp ebp,0x4c`),
  raise the 68 single checks, extend the remaining loops, `id=new` in zz_ability_types.txt + name registration on
  0x4d+ (register function refuses taken ids: see the je at 0x140341e01 bypass), then test.

## Progress 2026-11-13 (afternoon; built, off by default, not installed, untested in game)
- **Read-only remap stage DONE** (`exp_install_remaps`): faction SFX index sites `lea rax,[rdi+0xc7]` (0x14042f532) and
  `lea rdx,[rdi+0x161]` (0x14042f586); hardpoint `Fire_When_In_X_Mode` reads 0x140384915/0x14038496f (rdi remapped
  around the original cmp, flags kept); table functions: icon builder 0x14043eaf0 and 0x14043ebc0 remap the id at
  entry, 0x14043ec50/eff0/f340/f6e0 remap only the `lea X,[R+R*2]` table index (their ability NAME lookup keeps the
  real id), 0x14043ec10 (name only) just raised. Range checks in these functions (8) are owned by this stage.
  Note: icon= in zz_ability_types.txt has no effect on new ids (they show the like= icon unless the unit's ability
  entry sets Alternate_Icon_Name).
- **Stage 2 single checks DONE** (`exp_install_raises`): 41 checks + 4 loops (0x1404378e8, 0x14057f4a3, 0x14057ffe4,
  0x14063640a) raised by N, verified as `cmp r32,imm8` + jcc.
- **Slot walk loop DONE** (`exp_install_slot_walk`, 0x1403985d6): r14 jumps to the unit's side slots at id 0x4d.
- **Missed unit slot accesses found and handled**: `mov rax,ID; add rax,rax` + `[unit+rax*8+0x3d8/0x3d9]` at
  0x14038c45e (enabled flag write), 0x14039b402, 0x1403a7942 (byte +0x3d9 write) - stubs with bias 0.
- **Bug fixed**: the unit slot site check expected `add r,r` as 01 /r; the exe uses 03 /r, so the expansion would have
  stopped at that stage. Whole module now installs on stock bytes in a native harness (all 9 stages, N=8).
- Remaining: `id=new` in zz_ability_types.txt + name registration on 0x4d+ (register bypass), then an in-game test.
  Unit side blocks are never freed (keyed by address, cleared on unit setup); fine unless very long sessions fill
  the 4 MB pool (falls back to a shared dummy block).

## Stage 6 DONE (2026-11-13, built, not installed, untested in game)
- zz_ability_types.txt `id=new` (instead of `slot=`): ids 0x4d.. assigned in file order at DLL load (max N from
  `ability_expansion N`). At name-list build (hook 0x14046f220) the name is registered on the new id (free id, no
  bypass needed), like= resolved, `exp_set_like` fills the 5 extended switch tables (targeting= override on the
  button table) and `g_id_like[id]`. Skipped (logged) unless every expansion stage installed (`g_exp_ok`).
- Takeover (`slot=`) types now also write their switch entries into the extended copies when the expansion is on.
- fix_new_type_table skips ids > 0x4c (no stock table entry; getters remap).
- Harness `cbtest/full2.c` (scratchpad): all stages + id=new registration on stock bytes: new id 0x4d gets
  WEAKEN_ENEMY's cases (slot walk 5, has 5, activation 0x15, can-activate 0xe) and targeting 0 when overridden.
- To test: `ability_expansion 4` in zz_settings.txt, change FORCE_STORM to `id=new like=WEAKEN_ENEMY`, install DLL.
  Watch for: button, cooldown after use, activation (log "ability use: type 0x4d"), AI use, save/load reset.

## Order dispatcher + click switches added to the expansion (2026-11-13, built, not installed)
- id=new types only got the 5 original switches, so an id=new storm would show the reticle but never issue an
  order (same bug Force Storm had as a slot= type). EXP_SWITCHES now also extends the order dispatcher
  (0x4409c, bound `cmp dword [rsp+0x70],0x45` at 0x14004366e, imm8 at +4) and the button click switch
  (0x3470a8, bound at 0x140346eea); id=new types also get g_weaken_like_tab (dispatcher literal 0x2a check).
- Fixed: extended byte tables used to leave ids between the stock bound and 0x4d uninitialised (and the bound
  only rose by N, missing the top 1-2 new ids on adj>0 switches). Each switch now gets a copied case table plus
  one added case = the stock `ja` target; gap ids and unknown like= use it; bound = top id - adj.
- Test: `ability_expansion 4`, FORCE_STORM `id=new like=WEAKEN_ENEMY` (drop slot=BUZZ_DROIDS).
- In-game run 1 (2026-11-13): stages 1-4 installed, then cmdbar failed at 0x30e9a8 (the 12-button patch's jmp to
  the cave sits there; the native harness never applied PATCHES). No rollback -> half-patched exe (countdown
  relaid out) -> galactic save load crash. Fixed: 0x30e9a8 accepted when it holds P1_N (its lea runs from the
  cave copy, already patched); install_expansion now journals every write_bytes and undoes all on any failure.
  Static cross-check: no other expansion site overlaps a button patch.
- In-game run 2 (2026-11-13): all stages installed, save loaded, FORCE_STORM on 0x4d; crash selecting the
  Interdictor: [cmdbar+0x2008] (array 2 entry 0x4d count) overwritten. A pair scan (`add/lea R,..0xbb|0x108`
  then `lea R,[R+R*2]`) finds 5 index sites the census missed: 0x2e9e87 (add rcx,0x108), 0x30eb73 (add rax,0xbb),
  0x31c5d0, 0x31d0a5, 0x31d116 (add rax,0x108), plus the live lea copy in the after-.text CAVE at 0x7fc4e3
  (target of the 0x30e9a8 jmp; only the zz cave was scanned). Rolled back to powrprof_tp_logs.dll,
  ability_expansion 0, FORCE_STORM slot=BUZZ_DROIDS until these are patched.
- Fix build (2026-11-13 night, built, not installed): CB_SITES +6 (0x2e9e87, 0x30eb73, 0x31c5d0, 0x31d0a5,
  0x31d116, 0x30ee4a right-click autofire `movsxd rax,edi; mov ebx,r12d; lea rcx,[rax+rax*2]`), old after-.text
  cave's 3 lea copies patched too. Re-scan of every *8 access with disp 0x1188-0x119c / 0x18c0-0x18d4: the rest
  reuse an index saved after a patched site (0x2e094b, 0x3071d2) or are ctor/dtor 77-entry loops.
  Same build: zz_mod_apply expiry extension falls back when the fps int reads 0 (watch showed SHIELD/ENERGY
  entries running down 66/36/6/gone and re-added = never extended), with "mod extend:" log lines.
- In-game run 3 (2026-11-13/14): no crash; storm id 0x4d showed reticle but no order. Cause: the order dispatcher
  checks the type as MEMORY compares `cmp dword [rax+0x948],0x4d ; jl` at 0x140042ed9 / 0x140043317 / 0x140043386
  (the census only looked at register compares). Now raised to top+1 in exp_install_raises.
  Scan of all memory compares vs 0x4c/0x4d: the rest are byte char checks or 0x14051b4f8 (text-parsed index of a
  77-entry table, unrelated). Two-level switch scan: Lua Activate_Ability (0x140570c86 / 0x140570d57, id from a
  name) and 0x14027b670 / 0x140161560 / save reader 0x140285043 not extended yet (AI/Lua use of new ids).
- BUG FIXED (2026-11-14 01:17): the five `add` CB sites (0x2e9e87, 0x30eb73, 0x31c5d0, 0x31d0a5, 0x31d116) had
  cmp_at=0 / ins_at=len, so the stub ran `cmp t,0x4d ; add r,imm ; jl ; add r,D` - the replayed add clobbered the
  flags and EVERY id was redirected to the side block. 0x31c5d0 is the selection refresh adding units to array 2,
  so buttons 1+ (Push/Whirlwind 0xe via 0x2f93f0 reading array2[0xe], Protect 0x13, Drain 0x45) found empty group
  lists. cb_patch_window now branches right after the cmp into two replays whenever cmp_at != ins_at.
  Type map (Revan I): 0xd Telekinesis, 0xe Whirlwind=Force Push, 0x13 TARGETED_INVULNERABILITY=Protect,
  0x34 Sight, 0xa Lure=Battle Meditation, 0x39 Confuse, 0x36 Cloak, 0x45 Drain Life.
