# Stock ability type dispatch map

This map records the stock ability type names and their switch-table cases in the RevRev executable. The per-ID crosswalk is in [`ability_type_map.csv`](ability_type_map.csv).

## ID coverage and indexing

The DLL startup capture logged all 75 named stock ability types, IDs `0x01` through `0x4b`. The crosswalk records each switch's selector byte, or `default_or_bypass` when the engine does not index that switch for the ID.

| Engine path | Table RVA | Index used | Indexed IDs |
|---|---:|---|---|
| Unit ability slot walk | `0x39861c` | `id` | `0x01`–`0x4b` |
| Has ability | `0x39880c` | `id` | `0x01`–`0x4b` |
| Activation | `0x38c520` | `id - 1` | `0x01`–`0x4b` |
| Can activate | `0x39b904` | `id - 1` | `0x01`–`0x4b` |
| Targeting/button behavior | `0x2e0bcc` | `id - 5` | `0x05`–`0x4a` |
| Order dispatcher | `0x4409c` | `id - 5` | `0x05`–`0x4a` |
| Command-bar click handler | `0x3470a8` | `id - 0x0d` | `0x0d`–`0x4a` |

The crosswalk records each applicable entry as `case_NN@0xRVA`: the byte-table selector and the exact code RVA selected by the jump table. The selector is not itself a behavior label. `default_or_bypass` preserves the engine's default path for IDs outside a switch's indexed range; those are not missing IDs.

## Targeting and click branch behavior

The targeting switch at `0x2e0aec` returns two byte flags in `AL` and `DL` (the caller initializes `DL` to 1 before dispatch):

| Case / target RVA | IDs using it | Result |
|---|---|---|
| `00` / `0x2e0b10` | BARRAGE, RADIOACTIVE_CONTAMINATE, PROXIMITY_MINES | `AL=1`, `DL=0` |
| `01` / `0x2e0b12` | WEAKEN_ENEMY, FIRE_LOBBING_SUPERWEAPON | `AL=1`, `DL=1` |
| `02` / `0x2e0b16` | SUMMON | `AL=0`, `DL=0` |
| `03` / `0x2e0b1c` | CORRUPT_SYSTEMS | `AL=1`, `DL=0` (copies the incoming `DL` into `AL`) |
| `04` / `0x2e0b23` | Most targeted types | `AL=0`, `DL=1` |

The click switch dispatches through the command-bar global at `0x140b27f60`. Its distinct branches call these handlers:

| Case | Click path |
|---|---|
| `00` | `0x2e0730`, mode arguments `r8=0`, `r9=0` |
| `01` | Context-gated (`edi=3`); calls `0x2f93f0` |
| `02` | Context-gated; calls `0x2e0920` with `r8=2` or `3` |
| `03` | `0x2e0730`, `r8=1`, `r9=0` |
| `04` | Context-gated (`edi=3`); calls `0x2f96f0` |
| `05` | Context-gated (`edi=3`); calls `0x2f9570` |
| `06` | Context-gated (`edi=3`); calls `0x2f9270` |
| `07` | `0x2e0570`, `r8=2` |
| `08` | Context-gated (`edi=3`); calls `0x2e0920`, `r8=2` |
| `09` | Context-gated (`edi=2`); jumps to `0x2e7ed0` |
| `0a` | `0x2e0730`, `r8=6`, `r9=0` |
| `0b` | Calls `0x307190` with the selected type's command-bar list and current mode |

These are engine handler addresses and arguments, not friendly action names; the per-ID CSV identifies which branch each type reaches.

The order dispatcher has five specialized branches plus the stock default path:

| Case / target RVA | Stock types | Observed branch |
|---|---|---|
| `00` / `0x043699` | BARRAGE | Builds the barrage order record and enters its follow-up processing. |
| `01` / `0x0438aa` | JET_PACK | Specialized jet-pack order path. |
| `02` / `0x043788` | DISTRACT, FOW_REVEAL_PING, WEAKEN_ENEMY | Shared target/order-record path; WEAKEN has an additional type check before this switch. |
| `03` / `0x0439b2` | FIRE_LOBBING_SUPERWEAPON | Specialized lobbing-superweapon path. |
| `04` / `0x043be1` | RADIOACTIVE_CONTAMINATE, PLACE_REMOTE_BOMB, PROXIMITY_MINES, BUZZ_DROIDS, SUMMON, CORRUPT_SYSTEMS | Shared special-order setup. |
| `05` / `0x043e45` | Most other types | Original out-of-range/default target, also used by ordinary indexed types assigned case `05`. |

The DLL patches the separate WEAKEN type check at `0x043628`, so a new type using `like=WEAKEN_ENEMY` enters both its special pre-check and case `02`.

### Fog targeting status

The command-bar targeting selector at `0x2e0aec` only chooses the reticle's point/object modes. `targeting=location` changes that selector to point-only. The `like=` setting copies stock click, order, and activation cases; `FOW_REVEAL_PING` shares order case `02` with `WEAKEN_ENEMY`, while its activation case calls the shared effect routine with secondary ID `0x1c` (`0x3a3e20` at `0x38a760`). Changing another ability to `like=FOW_REVEAL_PING` is therefore not yet established as a fog-targeting remedy and could change its activation path. The nearby object-target filtering routine at `0x2d5440` checks target-class flags and entity properties; it does not expose a clear fog predicate. The final selection callback still needs to be traced before recommending a `like=` source or adding a fog bypass.

The can-activate switch at `0x39b640` has these stock predicate groups:

| Case / target RVA | Stock types |
|---|---|
| `00` / `0x39b69d` | DEFEND |
| `01` / `0x39b797` | INTERDICT |
| `02` / `0x39b68b` | HUNT |
| `03` / `0x39b667` | CAPTURE_VEHICLE, TARGETED_INVULNERABILITY, AREA_EFFECT_STUN, AREA_EFFECT_HEAL, AREA_EFFECT_CONVERT, CORRUPT_SYSTEMS |
| `04` / `0x39b7a9` | TRACTOR_BEAM |
| `05` / `0x39b7be` | ENERGY_WEAPON, LUCKY_SHOT, SUPER_LASER |
| `06` / `0x39b714` | DEPLOY_TROOPERS |
| `07` / `0x39b74f` | FIRE_LOBBING_SUPERWEAPON |
| `08` / `0x39b8a2` | FORCE_SIGHT |
| `09` / `0x39b7d0` | LEECH_SHIELDS, BLAST |
| `0a` / `0x39b87b` | PLACE_REMOTE_BOMB |
| `0b` / `0x39b7e4` | SHIELD_FLARE |
| `0c` / `0x39b7fd` | SUMMON |
| `0d` / `0x39b84d` | DEPLOY_SQUAD |
| `0e` / `0x39b8bf` | General predicate path used by the remaining types |

The specialized predicates also contain cross-ability and unit-state checks. Static inspection found no fixed reference to a case's own type ID in this switch.

## Lua `Object.Activate_Ability` selector coverage

The binding is `GameObjectWrapper::Activate_Ability` at `0x47aed0` (the parameter and unsupported-ability diagnostic strings xref into this routine). It resolves the ability name to a type ID, verifies the unit owns the ability, validates the second argument, then uses two selector tables:

| Selector | Index / bound | Table RVA | Behavior dispatch |
|---|---|---|---|
| First | `id - 2`, maximum `0x2c` | selector bytes `0x47cba0`; targets `0x47cb98` | `0` -> `0x47b0e5`; `1` -> `0x47b190` |
| Second | `id - 1`, maximum `0x2d` | selector bytes `0x47cbf4`; targets `0x47cbd0` | cases `0`–`8` -> `0x47b1b7`, `0x47b451`, `0x47b76d`, `0x47ba0d`, `0x47bdde`, `0x47c3bf`, `0x47c829`, `0x47c204`, `0x47cb3e` |

The first selector partitions stock IDs `0x02`–`0x2e` between the two internal paths. The second selector partitions IDs `0x01`–`0x2e` into nine behavior groups; see the per-ID assignments in the same CSV crosswalk's name/ID columns and the executable selector bytes at these RVAs. IDs above `0x2e` reach the `unsupported unit ability` diagnostic at `0x47cb3e` and return failure. The configured new IDs (`0x4d`–`0x53`) are therefore not supported by this Lua API, even though the DLL extends the command-bar activation and click paths. Extending Lua-driven activation requires raising both table bounds and supplying valid selector entries and handlers for new IDs; copying `like=` alone cannot do that.

## `like=` coverage

For `id=new`, the DLL copies the selected stock type's selector into the new ID for all seven paths, redirects per-type read-only data lookups to the selected stock ID, and gives the new ID its own unit slot and countdown state. It also handles the `WEAKEN_ENEMY` order check that is separate from the order jump table. Stock names are captured from the executable and resolved before `slot=` registrations can replace names.

The DLL also forwards the active type ID through all eight stock activation call sites that invoke the shared `0x3a3e20` routine. Their original handlers passed hard-coded IDs; the DLL now substitutes the active type ID and routes those calls through its activation wrapper. For stock IDs the value remains the same; for a new ID this preserves that ID through the shared activation path.

The activation audit found 62 immediate type-ID references across 19 specialized handlers (including Sensor Jamming, Stealth, Stun, Force Sight/Cloak, Laser Defense, Drain Life, Blast, Force Confuse, Cluster Bomb, and Deploy Squad). Those operands now use the active type ID as well, so the handler's own cooldown/state lookups address the takeover or new ID. All 62 original executable operands matched the expected stock bytes before the patch was built.

The can-activate switch was also scanned branch by branch. Its specialized cases use cross-ability checks and unit-state predicates, but none passes its own stock type ID as a fixed argument; those checks remain as the stock handler wrote them while the new ID selects the copied case.

There are additional ability-ID paths outside the seven switches extended for command-bar abilities, but an older census attributed several addresses incorrectly. On the installed executable, `0x570c86` is floating-point distance math and `0x570d50` begins object construction; `0x27b670` is in a vector insertion routine; `0x161560` is in a timed update loop; and `0x285043` is in an object-order processing loop. None of those instruction sites is itself an ability selector. The actual Lua activation binding and both selector tables are now mapped above. The AI/helper and serialization/save-data routes still need correct entry points before new-ID coverage can be claimed for those paths.

## Activation dispatch detail

The activation routine at `0x38a350` first verifies that the unit has the selected ability and resolves that unit's ability record. It then indexes the activation switch by `id - 1`. The selector's case target is not always a dedicated activation implementation: some targets call shared routines and pass a mode or secondary ability ID. This is why the crosswalk preserves both the case and target RVA rather than treating the case number as an action name.

| Activation case / target | Dispatch observed in the stock executable | Interpretation |
|---|---|---|
| `00` / `0x38a5a0` | Calls `0x3a4250` with the active type ID and the ability-record byte at `+0x67`. | Shared mode-based activation helper. |
| `01` / `0x38a558` | Calls `0x3a1ce0` with the ability-record byte at `+0x67`. | Shared helper; `DEPLOY` uses this selector. |
| `02` / `0x38a57a` | Calls `0x3a2240` with the active ID, record byte, and dword at record `+0x77`. | Shared parameterized activation helper. |
| `03` / `0x38a5b4` | Checks unit state, then calls `0x3a1930` with the active ID, record byte, and current position. | Position-aware activation path; used by `BARRAGE`. |
| `04` / `0x38a7ee` | Calls `0x3a4070` with the active ID and record byte. | Shared two-parameter helper; used by `HUNT`, `LURE`, and several other IDs. |
| `05` / `0x38a569` | Calls `0x3a3500` with the record byte. | Dedicated helper path. |
| `06` / `0x38a58f` | Calls `0x3a3260` with the record byte. | Dedicated helper path. |
| `07` / `0x38a60d` | Calls `0x3a1fb0` with the record byte. | Dedicated helper path; `FORCE_WHIRLWIND` uses this selector. |
| `08` / `0x38a72e` | Copies current position and calls `0x3a38d0` with the record byte. | Position-aware helper; `JET_PACK` uses this selector. |
| `09` / `0x38a802` | Checks `can activate`, searches/updates the active ability state, then reaches the shared success tail. | Predicate-gated activation path; includes `CAPTURE_VEHICLE`. |
| `0a` / `0x38a79f` | Calls `0x3a3e20` with secondary ID `0x13`, position, record byte, and the record's mask. | Shared effect routine with a fixed secondary ID (`TARGETED_INVULNERABILITY`). |
| `0b` / `0x38c448` | Shared success tail: marks activation successful and updates per-type state. | Not a standalone action body; selected for several types. |
| `0c`–`0e` / `0x38a61e`–`0x38a6be` | Call `0x3a3e20` with secondary IDs `0x17`–`0x19` and a position output. | Shared effect routine for stun, heal, and convert. |
| `0f` / `0x38a6ef` | Calls `0x3a3e20` with secondary ID `0x1a`, current position, record byte, and mask. | Shared effect routine for `DISTRACT`. |
| `10` / `0x38a760` | Calls `0x3a3e20` with secondary ID `0x1c`, position, record byte, and mask. | Shared effect routine for `FOW_REVEAL_PING`. |
| `15` / `0x38a64f` | Calls `0x3a3e20` with secondary ID `0x2a`, position, record byte `1`, and mask. | Shared effect routine for `WEAKEN_ENEMY`. |
| `28` / `0x38c46c` | Common fallback returns the current success flag without running a dedicated action body. | A fallback selector, not evidence of a generic ability implementation. |

The shared-effect calls above are the sites where hard-coded secondary type IDs matter. The DLL's forwarding patch substitutes the active type ID at the eight audited shared-handler call sites, while the activation audit separately updates 62 fixed IDs used for state lookups. The helper's other parameters (including fixed secondary IDs such as `0x17` for the stun effect) retain their stock meaning. A new type inherits its source selector and read-only type data; this map does not imply that every chosen `like=` produces a useful effect when the source type's stock behavior is a no-op or depends on other unit-specific state.

The RevRev log confirms all seven switches and seven per-type getters were extended for the configured capacity through `0x54`; the current configuration registers seven new types, `0x4d`–`0x53`. This is static mapping evidence; it does not establish an in-game result for every base type.

## Cooldown and GUI interpretation

The base archive's `UnitAbilityTypes.xml` is only a placeholder; assignments are in unit XML. Scanning `config.meg` found 174 `<Unit_Ability>` entries covering 43 of the 75 named stock types, and no `<Tactical_Ability>` entries. The crosswalk includes per-type entry counts, recharge values, and GUI activation names. [The assignment list](zz_ability_unit_assignments.csv) shows all 174 entries with their unit object, source XML, recharge, GUI activation name, icon override, spawned object, radius, and expiration fields. The base archive has 103 recharge fields and 48 GUI-activation-name fields across those entries. A type's missing recharge field means that entry leaves it unspecified; multiple recharge values reflect different units using the same type.

The ability type ID indexes the engine's countdown state. The countdown object has two 77-entry dword arrays and a 77-entry byte array; the extension stores new-ID state separately. `like=` inherits read-only type behavior, while the new ID keeps separate cooldown state. The executable also has separate unit ability slots and command-bar selection groups. The type ID alone does not say whether a particular unit exposes that ability as a GUI button: that depends on the unit's ability entries and command-bar setup. `GUI_Activated_Ability_Name` is an XML field for activation labeling, not a complete visibility flag. The click-handler column records how a present button click is dispatched.

### Save/load boundary

The stock unit reader/saver walks exactly 77 ability slots (`0x01`–`0x4c`); the countdown reader/saver likewise serializes 77 entries in each of its three arrays. The DLL keeps expanded IDs `0x4d` and above in side storage, outside those stock loops. Their unit-slot and cooldown state therefore resets on load and is not persisted. This preserves the stock save layout but means a saved battle does not retain a new ability's remaining cooldown or toggle state.

### Custom GUI wrappers for passive abilities

The intended GUI-special feature is to give passive-style effects separate custom ability IDs and buttons, while each ID keeps its own cooldown and activation state. That allows two abilities based on the same stock effect (for example, two `like=FORCE_LIGHTNING` types) to be used independently: one can recharge while the other is ready. The expansion has per-ID slots and cooldown state, and the Revan battle log shows separate cooldown updates for different new IDs. That is not yet the acceptance test for this feature, because those Revan abilities use different `like=` sources. Acceptance requires two GUI entries on one unit with distinct IDs and the same `like=` source, then confirming that using one starts only its cooldown and leaves the other available.

The stock command-bar object keeps two per-type unit-list arrays at offsets `+0x1188` and `+0x18c0`, with 24-byte vector entries indexed by ability type. The first array groups a unit under its first ability; the second groups its other abilities. Button fill, selection refresh, card layout, and removal all consult these lists. The engine also checks that the selected unit has the ability and is unlocked, then reads the type's flags and button group. These are separate gates from the activation and click switches mapped above. Thus `button_click` describes what happens after a button is present and clicked, not whether a particular unit's ability entry is shown. The DLL's existing selected-card diagnostic can log these gates in a live session, but the current startup log contains no such card-selection records.

### Live battle observation (2026-11-16)

The current RevRev battle log records player-owned `REVAN_JEDI_MW_I` in card slot `0x4`, with a swap target `Revan_Jedi_MW_II`. Its stock entries include `FORCE_TELEKINESIS`, `FORCE_WHIRLWIND`, `FORCE_SIGHT`, `LURE`, `FORCE_CONFUSE`, `TARGETED_INVULNERABILITY`, `FORCE_CLOAK`, and `DRAIN_LIFE`. For the stock entries, the selection diagnostic reports slot-present and has-ability as true, unlocked as true, and includes the type flags and command-bar group. It also records six expanded IDs in the same ability list: `0x4e`, `0x51`, `0x52`, `0x50`, `0x4f`, and `0x4d` (Force Teleport, Oneness, Lightning Storm, Force Restore, Force Corruption, and Force Storm respectively).

The subsequent click log records successful activation results (`result 1`) for all six expanded IDs present on that Revan card. It logs the targeting hand-off for Force Teleport, Lightning Storm, and Force Corruption; Force Teleport proceeds through departure and arrival; and Oneness starts its aura and applies modifiers. Recharge updates are logged for the new IDs, confirming that these activations use their own ID state. This is in-game confirmation for the six Revan Jedi custom abilities in this configuration. Among the stock Revan entries, click and activation traces are present for `FORCE_WHIRLWIND`, `LURE`, `FORCE_SIGHT`, `FORCE_CONFUSE`, `TARGETED_INVULNERABILITY`, and `FORCE_CLOAK`; `DRAIN_LIFE` (`0x45`) was clicked, but its activation returned false; the player reports no valid targets were available. The log does not contain a click event for the unit's `FORCE_TELEKINESIS` (`0x0d`) entry or the separate Revan Interdictor `FORCE_CONSTRUCT` (`0x53`) entry. The player reports Telekinesis could not be tried because no vehicle was in range; Drain Life had no valid targets. These target limitations explain the missing/failed observations and do not indicate a dispatch failure. A refused activation does not distinguish an invalid target/state from a `like=` dispatch issue. The selection diagnostic only prints gate values for stock IDs through `0x4c`, so the expanded-ID slot/unlocked/flag values are not shown.

## Remaining interpretation

The crosswalk gives every stock type's activation and can-activate case number and code RVA, and the specialized order and click paths have branch descriptions. Activation routing now identifies shared helpers and the common fallback. Static inspection has identified the command-bar list and gating fields, and the current battle log confirms successful use of the six expanded Revan Jedi abilities. Lua `Object.Activate_Ability` is mapped and rejects IDs above `0x2e`, including the configured new IDs. Save/load behavior is classified: expanded slot and cooldown state is not persisted by the stock 77-entry serializers. The AI/helper path still needs a correctly identified entry point, and Force Construct (`0x53`) remains untested in battle. The current log also shows `DRAIN_LIFE` (`0x45`) refused on that attempt because it was not ready, and has no click trace for stock `FORCE_TELEKINESIS` (`0x0d`).
