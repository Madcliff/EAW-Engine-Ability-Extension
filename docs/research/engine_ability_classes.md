# Engine ability classes (the <Abilities SubObjectList="Yes"> block)

Mapped 2026-11-17 from StarWarsG.exe (original backup 2026-11-17). Companion to `ability_type_map.md`, which maps the
ACTIVE abilities (`<Unit_Abilities_Data>` / `<Unit_Ability>` type ids). This file maps the ability CLASSES: the XML tags
inside a unit's `<Abilities SubObjectList="Yes">` block (passives, galactic abilities, and the effects that active unit
abilities trigger through `GUI_Activated_Ability_Name`). CSVs: `engine_ability_classes.csv`, `engine_ability_fields.csv`.

## How the engine builds them

- **Registration:** one function lists every tag with its factory: `register(tag string, factory)` calls at
  0x14068b8xx..0x14068d2xx (helper 0x14068b1f0). 85 tags are registered. Each factory allocates the object (size below) and
  runs the class constructor, which sets the vtable.
- **vtable:** slot 2 returns the XML tag; slot 28 parses the class's own XML fields by calling its per-table parser
  (0x1405175xx..0x14051a2xx) with that class's field table and entry count.
- **Field tables** (in .data, 0x140a3d690..): 0x20-byte entries `{name ptr, type code, offset in the object, 0}`. Each
  table is registered once at start-up (0x140515f1d..0x1405163xx: table + byte size, stored in the parser object).
- **Base fields:** every class starts with the shared AbilityClass block (table 0x140a3d690, offsets below 0x178);
  class fields start at +0x178.
- **Type codes seen:** 0 = bool, 6 = int, 8 = float, 9 = float (chance), 14 = enum, 16 = colour, 23 = string, 27 = bone name, 29 = particle type, 30 = type list, 31 = SFX event, 86 = category mask (names inferred from the fields that use them).

## Range of galactic abilities (items 11/12)

- None of the classes has a range field. Galactic abilities use the OWNER UNIT's `Galactic_Influence_Range` (object
  type +0x1a00, float; field table 0x140a2fe70). One value per unit, shared by all its galactic abilities.
- System Spy (vtable slot 21, 0x14070f950): if the range is > 0, objects within that range are queried (0x1402a9ff0);
  if it is 0 or less (the default), only the unit's own planet counts.
- 0x1404f3430 / 0x1404f40c0 take the largest `Galactic_Influence_Range` among objects (both read +0x1a00 14 times).
- So "System Spy with its own range" = make System Spy (or a named ability entry) read its own value instead of
  +0x1a00 at 0x14070f99c / 0x14070f9dd. The production modifiers reach the range through the aggregate functions above.
- `Stacking_Category` (int) is a field of many classes: Combat_Bonus +0x19c, Reduce_Production_Price +0x17c, ...
  (see the field list). That is the hook for item 11 (stacking passives).

## Shared base fields (every class)

| Field | Type | Offset |
|---|---|---|
| Initially_Enabled | bool | 0x40 |
| Activation_Style | enum | 0x3c |
| Causes_Despawn | bool | 0x41 |
| Terminate_Effect_On_Move_Command | bool | 0x42 |
| Unit_Strength_Category | category mask | 0x48 |
| Unit_Strength_Factor | float | 0x50 |
| Applicable_Unit_Categories | category mask | 0x60 |
| Applicable_Unit_Types | type list | 0x68 |
| Excluded_Unit_Categories | category mask | 0x88 |
| Excluded_Unit_Types | type list | 0x90 |
| Owner_Light_Effect_Type | enum | 0xb0 |
| Owner_Light_Effect_Color | colour | 0xb4 |
| Owner_Light_Effect_Color2 | colour | 0xc0 |
| Owner_Light_Effect_Duration | float | 0xcc |
| Owner_Light_Effect_Pulse_Count | int | 0xd0 |
| Target_Light_Effect_Type | enum | 0xd4 |
| Target_Light_Effect_Color | colour | 0xd8 |
| Target_Light_Effect_Color2 | colour | 0xe4 |
| Target_Light_Effect_Duration | float | 0xf0 |
| Target_Light_Effect_Pulse_Count | int | 0xf4 |
| Owner_Particle_Effect | particle type | 0xf8 |
| Owner_Particle_Bone_Name | bone name | 0x108 |
| Target_Particle_Effect | particle type | 0x120 |
| Target_Particle_Bone_Name | bone name | 0x130 |
| SFXEvent_Activate | SFX event | 0x148 |
| SFXEvent_Target_Affected | SFX event | 0x158 |
| Min_Respawn_Time | float | 0x54 |
| Max_Respawn_Time | float | 0x58 |
| Must_Be_Bought_On_Black_Market | bool | 0x168 |

## Classes

| XML tag | Engine class | Size | Fields | Triggered by (Unit_Ability type, uses in mods) | Galactic (by name, unverified) |
|---|---|---|---|---|---|
| Berserker_Ability | BerserkerAbilityClass | 0x190 | 6 | BERSERKER (19) |  |
| Black_Market_Ability | BlackMarketAbilityClass | 0x1b0 | base only |  | yes |
| Blast_Ability | BlastAbilityClass | 0x1a0 | 6 | BLAST (1) |  |
| Buzz_Droids_Ability | BuzzDroidsAbilityClass | 0x1b8 | 9 |  |  |
| Cancel_Special_Ability | CancelSpecialAbilityClass | 0x178 | base only |  |  |
| Cluster_Bomb_Ability | ClusterBombAbilityClass | 0x198 | 5 |  |  |
| Combat_Bonus_Ability | CombatBonusAbilityClass | 0x1c8 | 11 |  |  |
| Concentrate_Fire_Attack_Ability | ConcentrateFireAttackAbilityClass | 0x188 | 3 |  |  |
| Corrupt_Planet_Ability | CorruptPlanetAbilityClass | 0x180 | 2 |  | yes |
| Corrupt_Systems_Ability | CorruptSystemsAbilityClass | 0x190 | 5 |  |  |
| Corruption_Ability | CorruptionAbilityClass | 0x180 | base only |  | yes |
| Demolition_Ability | DemolitionAbilityClass | 0x1b8 | 10 |  |  |
| Detect_Hero_Ability | DetectHeroAbilityClass | 0x188 | 3 |  | yes |
| Drain_Life_Ability | DrainLifeAbilityClass | 0x1f8 | 9 | DRAIN_LIFE (14) |  |
| Earthquake_Attack_Ability | EarthquakeAttackAbilityClass | 0x190 | 6 |  |  |
| Eat_Attack_Ability | EatAttackAbilityClass | 0x200 | 16 |  |  |
| Eliminate_Hero_Ability | EliminateHeroAbilityClass | 0x178 | base only |  | yes |
| Enable_Ability | EnableAbilityAbilityClass | 0x1a0 | 2 |  |  |
| Enable_Radar_Ability | EnableRadarAbilityClass | 0x180 | 1 |  |  |
| Energy_Weapon_Attack_Ability | EnergyWeaponAttackAbilityClass | 0x1c0 | 7 | ENERGY_WEAPON (2) |  |
| Enhance_Defense_Ability | EnhanceDefenseAbilityClass | 0x188 | 3 |  |  |
| Find_Weakness_Ability | FindWeaknessAbilityClass | 0x180 | 2 |  |  |
| Force_Cloak_Ability | ForceCloakAbilityClass | 0x190 | 2 | FORCE_CLOAK (10) |  |
| Force_Confuse_Ability | ForceConfuseAbilityClass | 0x1a0 | 8 | FORCE_CONFUSE (15) |  |
| Force_Healing_Ability | ForceHealingAbilityClass | 0x1c0 | 7 |  |  |
| Force_Lightning_Ability | ForceLightningAbilityClass | 0x1f8 | 10 | FORCE_LIGHTNING (32); FORCE_TORRENT (1) |  |
| Force_Sight_Ability | ForceSightAbilityClass | 0x180 | 3 | WEAKEN_ENEMY (1); FOW_REVEAL_PING (1); FORCE_SIGHT (10) |  |
| Force_Telekinesis_Ability | ForceTelekinesisAbilityClass | 0x190 | 6 | FORCE_TELEKINESIS (26) |  |
| Force_Whirlwind_Ability | ForceWhirlwindAbilityClass | 0x1b8 | 5 | FORCE_WHIRLWIND (39) |  |
| Galactic_Sabotage_Ability | GalacticSabotageAbilityClass | 0x190 | base only |  | yes |
| Galactic_Stealth_Ability | GalacticStealthAbilityClass | 0x180 | 14 |  | yes |
| Galaxy_Wide_Upgrade_Ability | GalaxyWideUpgradeAbilityClass | 0x198 | 2 |  | yes |
| Garrison_Upgrade_Ability | GarrisonUpgradeAbilityClass | 0x1a0 | 2 |  | yes |
| Generic_Attack_Ability | GenericAttackAbilityClass | 0x1b0 | 9 |  |  |
| Grenade_Attack_Ability | GrenadeAttackAbilityClass | 0x1f0 | 9 | STICKY_BOMB (49) |  |
| Hack_Ability | HackAbilityClass | 0x1f8 | 8 | TARGETED_HACK (11) |  |
| Hack_Super_Weapon_Ability | HackSuperWeaponAbilityClass | 0x178 | base only |  |  |
| Hero_Assassin_Ability | HeroAssassinAbilityClass | 0x188 | 5 |  | yes |
| Hero_Protection_Ability | HeroProtectionAbilityClass | 0x180 | 2 |  | yes |
| Income_Stream_Ability | IncomeStreamAbilityClass | 0x188 | 6 |  | yes |
| Income_Stream_Mod_Ability | IncomeStreamModAbilityClass | 0x1a0 | 7 |  | yes |
| Infection_Ability | InfectionAbilityClass | 0x1e8 | 12 |  |  |
| Ion_Cannon_Shot_Attack_Ability | IonCannonShotAttackAbilityClass | 0x180 | 3 |  |  |
| Laser_Defense_Ability | LaserDefenseAbilityClass | 0x240 | 14 |  |  |
| Leech_Shields_Ability | LeechShieldsAbilityClass | 0x218 | 12 | LEECH_SHIELDS (1) |  |
| Lucky_Shot_Attack_Ability | LuckyShotAttackAbilityClass | 0x188 | 3 | LUCKY_SHOT (45) |  |
| Maximum_Firepower_Attack_Ability | MaximumFirepowerAttackAbilityClass | 0x180 | 1 | MAXIMUM_FIREPOWER (1) |  |
| Neutralize_Hero_Ability | NeutralizeHeroAbilityClass | 0x210 | base only |  | yes |
| Permanent_Weapon_Swap_Ability | PermanentWeaponSwapAbilityClass | 0x180 | 3 |  |  |
| Personal_Flame_Thrower_Ability | PersonalFlameThrowerAbilityClass | 0x1b8 | 9 |  |  |
| Planet_Destruction_Ability | PlanetDestructionAbilityClass | 0x178 | base only |  | yes |
| Planet_Income_Bonus_Ability | PlanetIncomeBonusAbilityClass | 0x1a8 | 4 |  | yes |
| Planet_Income_Gambling_Ability | PlanetIncomeGamblingAbilityClass | 0x188 | 4 |  | yes |
| Political_Control_Bonus_Ability | PoliticalControlBonusAbilityClass | 0x180 | 2 |  | yes |
| Political_Control_Protection_Ability | PoliticalControlProtectionAbilityClass | 0x178 | base only |  | yes |
| Political_Transition_Bonus_Ability | PoliticalTransitionBonusAbilityClass | 0x180 | 2 |  | yes |
| Proximity_Mines_Ability | ProximityMinesAbilityClass | 0x1b0 | 12 | PROXIMITY_MINES (70) |  |
| Radioactive_Contaminate_Ability | RadioactiveContaminateAbilityClass | 0x1d8 | 6 |  |  |
| Redirect_Blaster_Ability | RedirectBlasterAbilityClass | 0x190 | 8 |  |  |
| Reduce_Production_Price_Ability | ReduceProductionPriceAbilityClass | 0x188 | 3 |  | yes |
| Reduce_Production_Time_Ability | ReduceProductionTimeAbilityClass | 0x188 | 3 |  | yes |
| Reduce_Technology_Price_Ability | ReduceTechnologyPriceAbilityClass | 0x180 | 14 |  | yes |
| Remote_Bomb_Ability | RemoteBombAbilityClass | 0x1b8 | 6 |  |  |
| Remove_Corruption_Ability | RemoveCorruptionAbilityClass | 0x188 | base only |  | yes |
| Repair_Ability | RepairAbilityClass | 0x1f8 | 8 | TARGETED_REPAIR (2) |  |
| Retreat_Prevention_Ability | RetreatPreventionAbilityClass | 0x178 | base only |  | yes |
| Retreat_Protection_Ability | RetreatProtectionAbilityClass | 0x180 | 2 |  | yes |
| Saber_Throw_Ability | SaberThrowAbilityClass | 0x1a8 | 4 |  |  |
| Sabotage_Political_Control_Ability | SabotagePoliticalControlAbilityClass | 0x188 | 2 |  | yes |
| Sensor_Jamming_Ability | SensorJammingAbilityClass | 0x1b8 | 6 | SENSOR_JAMMING (135) |  |
| Shield_Flare_Ability | ShieldFlareAbilityClass | 0x188 | 5 |  |  |
| Siphon_Credits_Ability | SiphonCreditsAbilityClass | 0x188 | 3 |  | yes |
| Slicer_Ability | SlicerAbilityClass | 0x228 | base only |  | yes |
| Spawn_Ability | SpawnAbilityClass | 0x1d0 | 8 |  |  |
| Starbase_Upgrade_Ability | StarbaseUpgradeAbilityClass | 0x178 | base only |  | yes |
| Stealth_Ability | StealthAbilityClass | 0x190 | base only | STEALTH (39) |  |
| Stun_Ability | StunAbilityClass | 0x1a0 | 6 | STUN (29) |  |
| Summon_Ability | SummonAbilityClass | 0x1a8 | 5 |  |  |
| Super_Laser_Ability | SuperLaserAbilityClass | 0x1e0 | 14 | SUPER_LASER (8) |  |
| System_Spy_Ability | SystemSpyAbilityClass | 0x190 | 17 |  | yes |
| Tactical_Bribe_Ability | TacticalBribeAbilityClass | 0x1c8 | base only |  |  |
| Tractor_Beam_Attack_Ability | TractorBeamAttackAbilityClass | 0x188 | 4 | TRACTOR_BEAM (2) |  |
| Unit_Ability | SpecialAbilityDataClass | 0x250 | base only |  |  |
| Vehicle_Thief_Ability | VehicleThiefAbilityClass | 0x188 | 3 | CAPTURE_VEHICLE (1) |  |
| Weatherproof_Ability | WeatherproofAbilityClass | 0x180 | 1 |  |  |

Unit_Ability types whose GUI ability name has no matching <Abilities> entry in the scanned XML: BUZZ_DROIDS, FULL_SALVO, HUNT, ROCKET_ATTACK, SELF_DESTRUCT, STEALTH, STICKY_BOMB.
Scanned XML: the zz_mod_revrev submod plus the three workshop mods (1125571106, 1976399102, 3417277973).

## Fields per class

**Berserker_Ability** (BerserkerAbilityClass): Activation_Min_Range (float 0x178), Activation_Max_Range (float 0x17c), Berserker_Speed (float 0x180), Berserker_Damage (float 0x184), Berserker_Damage_Range (float 0x188), Berserker_Duration_In_Secs (float 0x18c)

**Blast_Ability** (BlastAbilityClass): Charge_Up_Seconds (float 0x178), Damage_Multiplier (float 0x17c), Charging_Effect (particle type 0x190), Charged_Effect (particle type 0x180), Stealth_Color (22 0x178), Stealth_Transition_Time (float 0x188)

**Buzz_Droids_Ability** (BuzzDroidsAbilityClass): Activation_Min_Range (float 0x178), Activation_Max_Range (float 0x17c), Object_Type (particle type 0x198), Chase_Radius (float 0x188), Damage_Radius (float 0x184), Enemy_Damage_Per_Second (float 0x190), Own_Damage_Per_Second (float 0x18c), Activation_Time_In_Seconds (float 0x180), Activate_SFX (SFX event 0x1a8)

**Cluster_Bomb_Ability** (ClusterBombAbilityClass): Detonation_Time_In_Secs (float 0x178), Bomb_Type (particle type 0x180), Number_Of_Bombs (int 0x190), Stealth_Color (22 0x178), Stealth_Transition_Time (float 0x188)

**Combat_Bonus_Ability** (CombatBonusAbilityClass): Health_Bonus_Percentage (float 0x178), Damage_Bonus_Percentage (float 0x17c), Energy_Pool_Bonus_Percentage (float 0x180), Shield_Bonus_Percentage (float 0x184), Movement_Speed_Bonus_Percentage (float 0x188), Defense_Bonus_Percentage (float 0x18c), Ability_Recharge_Bonus_Percentage (float 0x190), Fire_Range_Bonus_Percentage (float 0x194), Tactical_Build_Time_Bonus_Percentage (float 0x198), Stacking_Category (int 0x19c), Specific_Faction (string 0x1a0)

**Concentrate_Fire_Attack_Ability** (ConcentrateFireAttackAbilityClass): Target_Damage_Increase_Percent (float 0x178), Target_Speed_Decrease_Percent (float 0x17c), Stacking_Category (int 0x180)

**Corrupt_Planet_Ability** (CorruptPlanetAbilityClass): Required_Corruption_Level (int 0x178), Transition_Time_In_Secs (float 0x17c)

**Corrupt_Systems_Ability** (CorruptSystemsAbilityClass): Activation_Min_Range (float 0x178), Activation_Max_Range (float 0x17c), Duration_In_Seconds (float 0x180), Shield_Drain_Per_Second (float 0x184), Inaccuracy_Radius (float 0x188)

**Demolition_Ability** (DemolitionAbilityClass): Activation_Chance (float 0x180), Activation_Min_Range (float 0x178), Activation_Max_Range (float 0x17c), Damage_Amount (float 0x184), Damage_Percentage (float 0x188), Bomb_Type (particle type 0x190), Bomb_Position_Offset (colour 0x1a4), Bomb_Spawn_Frame (int 0x1b0), Bomb_Damage_Type (enum 0x1a0), Bomb_Timer_In_Secs (float 0x1b4)

**Detect_Hero_Ability** (DetectHeroAbilityClass): Detect_Interval_In_Seconds (float 0x178), Detection_Chance (float (chance) 0x17c), Detect_Credit_Siphon_Effects (bool 0x180)

**Drain_Life_Ability** (DrainLifeAbilityClass): Duration_In_Seconds (float 0x17c), Charging_Time_In_Seconds (float 0x180), Damage_Per_Second (float 0x178), Drain_Effect_Name (string 0x188), Drain_Source_Bone_Name (string 0x1a8), Drain_Target_Bone_Name (string 0x1c8), Drain_Radius (float 0x1e8), Max_Drain_Victims (int 0x1ec), Should_Heal (bool 0x1f0)

**Earthquake_Attack_Ability** (EarthquakeAttackAbilityClass): Activation_Chance (float 0x180), Activation_Min_Range (float 0x178), Activation_Max_Range (float 0x17c), Damage_Amount (float 0x184), Damage_Percentage (float 0x188), Damage_Interval_In_Secs (float 0x18c)

**Eat_Attack_Ability** (EatAttackAbilityClass): Activation_Chance (float 0x178), Activation_Min_Range (float 0x17c), Activation_Max_Range (float 0x180), Damage_Amount (float 0x184), Damage_Percentage (float 0x188), Damage_Type (enum 0x18c), Attack_Animation (enum 0x190), Attack_Animation_Speedup (float 0x194), Owner_Attachment_Bone (bone name 0x198), Target_Attachment_Bone (bone name 0x1b0), Attachment_Frame (int 0x1c8), Target_Destruction_Frame (int 0x1cc), Target_Grabbed_Animation (enum 0x1d0), Needs_To_Rotate (bool 0x1d4), Rotation_Base_Bone_Name (string 0x1d8), Health_Per_Victim (float 0x1f8)

**Enable_Ability** (EnableAbilityAbilityClass): Ability_Name (string 0x178), Affects_All_Allies (bool 0x198)

**Enable_Radar_Ability** (EnableRadarAbilityClass): Affects_All_Allies (bool 0x178)

**Energy_Weapon_Attack_Ability** (EnergyWeaponAttackAbilityClass): Activation_Min_Range (float 0x17c), Activation_Max_Range (float 0x180), Damage_Per_Frame (float 0x178), Beam_Color (22 0x184), Beam_Frames (int 0x198), Beam_Width (float 0x194), Beam_Texture (string 0x1a0)

**Enhance_Defense_Ability** (EnhanceDefenseAbilityClass): Enhancement_Percentage (float 0x178), Stacking_Category (int 0x17c), Apply_To_All_Allies (bool 0x180)

**Find_Weakness_Ability** (FindWeaknessAbilityClass): Damage_Bonus_Percentage (float 0x178), Stacking_Category (int 0x17c)

**Force_Cloak_Ability** (ForceCloakAbilityClass): Force_Cloak_Color (22 0x178), Force_Cloak_Transition_In_Secs (float 0x188)

**Force_Confuse_Ability** (ForceConfuseAbilityClass): Activation_Min_Range (float 0x178), Activation_Max_Range (float 0x17c), Confuse_Time_In_Secs (float 0x180), Confuse_Range (float 0x184), Confuse_Travel_Time_In_Secs (float 0x188), Confuse_Effect (particle type 0x190), Stealth_Color (22 0x178), Stealth_Transition_Time (float 0x188)

**Force_Healing_Ability** (ForceHealingAbilityClass): Heal_Range (float 0x178), Heal_Percent (float 0x17c), Heal_Amount (float 0x180), Heal_Interval_In_Secs (float 0x184), Single_Target_Heal (bool 0x188), Heal_Range_Blob_Material (string 0x190), Blob_Color (22 0x1b0)

**Force_Lightning_Ability** (ForceLightningAbilityClass): Activation_Min_Range (float 0x178), Activation_Max_Range (float 0x17c), Damage_Amount (float 0x180), Damage_Application_Time_In_Secs (float 0x184), Start_Lightning_Frame_Number (float 0x188), Lightning_Effect_Name (string 0x190), Lightning_Source_Bone_Name (string 0x1b0), Lightning_Target_Bone_Name (string 0x1d0), Lightning_Max_Targets (int 0x1f0), Lightning_Targets_Radius (float 0x1f4)

**Force_Sight_Ability** (ForceSightAbilityClass): Force_Sight_Duration_In_Secs (float 0x178), Stealth_Color (22 0x178), Stealth_Transition_Time (float 0x188)

**Force_Telekinesis_Ability** (ForceTelekinesisAbilityClass): Activation_Chance (float 0x180), Activation_Min_Range (float 0x178), Activation_Max_Range (float 0x17c), Damage_Amount (float 0x184), Damage_Percentage (float 0x188), Damage_Interval_In_Secs (float 0x18c)

**Force_Whirlwind_Ability** (ForceWhirlwindAbilityClass): Activation_Chance (48 0x178), Activation_Min_Range (float 0x1a0), Activation_Max_Range (float 0x1a4), Stealth_Color (22 0x178), Stealth_Transition_Time (float 0x188)

**Galactic_Stealth_Ability** (GalacticStealthAbilityClass): Evade_Detection_Chance (float (chance) 0x178), FOW_Reveal_Range_Multiplier (float 0x17c), Reinforcement_Time_Multiplier (float 0x180), Stealth_Duration_Multiplier (float 0x184), Capture_Point_Time_Multiplier (float 0x188), Base_Shield_Upgrade (bool 0x190), Enable_Bombing_Runs (bool 0x191), Enable_Special_Weapons (bool 0x192), Apply_To_All_Allies (bool 0x195), Reverse_Application_Logic (bool 0x196), Stacking_Category (int 0x178), Enable_Planetary_Bombardment (bool 0x193), Reinforcement_Deploy_Time_Multiplier (float 0x18c), Disable_Reinforcement_Vulnerability (bool 0x194)

**Galaxy_Wide_Upgrade_Ability** (GalaxyWideUpgradeAbilityClass): Space_Upgrade_Type (particle type 0x178), Land_Upgrade_Type (particle type 0x188)

**Garrison_Upgrade_Ability** (GarrisonUpgradeAbilityClass): Additional_Garrison_Units (type list 0x180), Apply_To_All_Allies (bool 0x178)

**Generic_Attack_Ability** (GenericAttackAbilityClass): Activation_Chance (float 0x178), Activation_Min_Range (float 0x17c), Activation_Max_Range (float 0x180), Damage_Amount (float 0x184), Damage_Percentage (float 0x188), Damage_Type (enum 0x18c), Attack_Animation (enum 0x190), Attack_Animation_Speedup (float 0x194), Damage_Frame_Number (int 0x198)

**Grenade_Attack_Ability** (GrenadeAttackAbilityClass): Activation_Chance (48 0x178), Activation_Min_Range (float 0x1a0), Activation_Max_Range (float 0x1a4), Requires_Direct_Player_Command (bool 0x1a8), Grenade_Type (particle type 0x1b0), Grenade_Toss_Anim (enum 0x1c0), Grenade_Spawn_Frame (float 0x1c4), Grenade_Spawn_Bone (string 0x1c8), Grenade_Explode_Timer_In_Secs (float 0x1e8)

**Hack_Ability** (HackAbilityClass): Team_Member_With_Ability (particle type 0x1e8), Activation_Min_Range (float 0x178), Activation_Max_Range (float 0x17c), Lightning_Effect_Name (string 0x180), Lightning_Source_Bone_Name (string 0x1a0), Lightning_Target_Bone_Name (string 0x1c0), Lightning_Max_Targets (int 0x1e0), Lightning_Targets_Radius (float 0x1e4)

**Hero_Assassin_Ability** (HeroAssassinAbilityClass): Can_Assassinate_Minor_Heroes (bool 0x178), Can_Assassinate_Major_Heroes (bool 0x179), Trigger_Only_On_Defense (bool 0x17a), Chance_To_Succeed (float 0x17c), Chance_To_Be_Caught_Upon_Failure (float 0x180)

**Hero_Protection_Ability** (HeroProtectionAbilityClass): Neutralization_Cost_Multiplier (float 0x178), Stacking_Category (int 0x17c)

**Income_Stream_Ability** (IncomeStreamAbilityClass): Base_Income_Value (float 0x178), Base_Interval_In_Secs (float 0x17c), Owner_Income_Percentage (float 0x180), Split_Income_With_Allies (bool 0x184), Split_Favors_Owner (bool 0x185), Full_Amount_To_Everyone (bool 0x186)

**Income_Stream_Mod_Ability** (IncomeStreamModAbilityClass): Income_Multiplier (float 0x178), Income_Additive_Value (float 0x17c), Interval_Multiplier (float 0x180), Stacking_Category (int 0x184), Target_Stream_Source (particle type 0x188), Affects_All_Allied_Sources (bool 0x198), Reverse_Application_Logic (bool 0x199)

**Infection_Ability** (InfectionAbilityClass): Activation_Min_Range (float 0x178), Activation_Max_Range (float 0x17c), Shoot_Anim (enum 0x180), Spawn_Frame (float 0x184), Spawn_Bone (string 0x188), Damage_Per_Second (float 0x1a8), Duration_Of_Infection (float 0x1d0), Projectile_Type (particle type 0x1b0), Infection_CategoryMask (category mask 0x1c0), Distance_To_Infect (float 0x1c8), Infection_Particle (particle type 0x1d8), Seconds_To_Infect (float 0x1cc)

**Ion_Cannon_Shot_Attack_Ability** (IonCannonShotAttackAbilityClass): Dummy (int 0x178), Activation_Min_Range (float 0x17c), Activation_Max_Range (float 0x180)

**Laser_Defense_Ability** (LaserDefenseAbilityClass): Stealth_Color (22 0x178), Stealth_Transition_Time (float 0x188), Defense_Duration_In_Secs (float 0x178), Laser_Color (22 0x17c), Bone_Names (42 0x190), Projectile_Types_Targeted (81 0x1c0), Protection_Radius (float 0x1d8), Laser_Beam_Frames (int 0x1dc), Laser_Beam_Width (float 0x1e4), Projectile_Dist_Travelled (float 0x1e0), Lightning_Effect_Name (string 0x1e8), Laser_Beam_Texture (string 0x208), Recharge_Time_In_Secs (float 0x228), Zap_SFXEvent (SFX event 0x230)

**Leech_Shields_Ability** (LeechShieldsAbilityClass): Activation_Min_Range (float 0x178), Activation_Max_Range (float 0x17c), Duration_In_Secs (float 0x180), Shield_Damage_Per_Second (float 0x184), Damage_Multiplier (float 0x188), Beam_Color (22 0x18c), Beam_Bone_Name (string 0x1a0), Beam_Frames (int 0x1c0), Beam_Width (float 0x1c4), Beam_Texture_Name (string 0x1c8), Beam_Effect_Name (string 0x1e8), Leech_Effect (particle type 0x208)

**Lucky_Shot_Attack_Ability** (LuckyShotAttackAbilityClass): Target_Damage_Increase_Percent (float 0x178), Target_Speed_Decrease_Percent (float 0x17c), Stacking_Category (int 0x180)

**Maximum_Firepower_Attack_Ability** (MaximumFirepowerAttackAbilityClass): Dummy (int 0x178)

**Permanent_Weapon_Swap_Ability** (PermanentWeaponSwapAbilityClass): Weapon_Index (int 0x178), Force_Cloak_Color (22 0x178), Force_Cloak_Transition_In_Secs (float 0x188)

**Personal_Flame_Thrower_Ability** (PersonalFlameThrowerAbilityClass): Activation_Min_Range (float 0x178), Activation_Max_Range (float 0x17c), Damage_Arc_In_Degrees (float 0x188), Damage_Amount (float 0x184), Fire_Time_In_Secs (float 0x18c), Recharge_Time_In_Secs (float 0x194), Damage_Delay_In_Secs (float 0x190), Flame_Emitter_Model_Name (string 0x198), Damage_Type (enum 0x180)

**Planet_Income_Bonus_Ability** (PlanetIncomeBonusAbilityClass): Percentage_Income_Modifier (float 0x178), Absolute_Income_Modifier (float 0x17c), Additional_Multiplier_On_Mining_Colonies (float 0x180), Specific_Mod_Source_Text (string 0x188)

**Planet_Income_Gambling_Ability** (PlanetIncomeGamblingAbilityClass): Evaluation_Interval_In_Secs (float 0x178), Min_Income_Modifier (float 0x17c), Max_Income_Modifier (float 0x180), Chance_To_Win (float 0x184)

**Political_Control_Bonus_Ability** (PoliticalControlBonusAbilityClass): Political_Change (int 0x178), Change_Duration_In_Seconds (float 0x17c)

**Political_Transition_Bonus_Ability** (PoliticalTransitionBonusAbilityClass): Time_Reduction_Percentage (float 0x178), Stacking_Category (int 0x17c)

**Proximity_Mines_Ability** (ProximityMinesAbilityClass): Activation_Min_Range (float 0x178), Activation_Max_Range (float 0x17c), Mine_Type (particle type 0x188), Trigger_Radius (float 0x184), Number_Of_Mines (int 0x198), Activation_Time_In_Seconds (float 0x180), Activate_SFX (SFX event 0x1a0), Duration_In_Seconds (float 0x17c), Charging_Time_In_Seconds (float 0x180), Damage_Per_Second (float 0x178), Drain_Effect_Name (string 0x188), Drain_Source_Bone_Name (string 0x1a8)

**Radioactive_Contaminate_Ability** (RadioactiveContaminateAbilityClass): Activation_Min_Range (float 0x178), Activation_Max_Range (float 0x17c), Spray_Time_In_Secs (float 0x180), Emitter_Name (string 0x188), Contamination_Object_Name (string 0x1a8), SFXEvent_Radioactive (SFX event 0x1c8)

**Redirect_Blaster_Ability** (RedirectBlasterAbilityClass): Redirect_Chance (float 0x178), Block_Chance (float 0x17c), Reaction_Arc_In_Degrees (float 0x180), Max_Projectile_Redirection_Angle_In_Degrees (float 0x184), Turn_To_Face_Unblockable_Shots (bool 0x188), Absorb_Chance (float 0x178), Damage_Absorb_Percentage (float 0x17c), Damage_Absorb_Amount (float 0x180)

**Reduce_Production_Price_Ability** (ReduceProductionPriceAbilityClass): Price_Reduction_Percentage (float 0x178), Stacking_Category (int 0x17c), Galaxy_Wide (bool 0x180)

**Reduce_Production_Time_Ability** (ReduceProductionTimeAbilityClass): Time_Reduction_Percentage (float 0x178), Stacking_Category (int 0x17c), Galaxy_Wide (bool 0x180)

**Reduce_Technology_Price_Ability** (ReduceTechnologyPriceAbilityClass): Price_Reduction_Percentage (float 0x178), FOW_Reveal_Range_Multiplier (float 0x17c), Reinforcement_Time_Multiplier (float 0x180), Stealth_Duration_Multiplier (float 0x184), Capture_Point_Time_Multiplier (float 0x188), Base_Shield_Upgrade (bool 0x190), Enable_Bombing_Runs (bool 0x191), Enable_Special_Weapons (bool 0x192), Apply_To_All_Allies (bool 0x195), Reverse_Application_Logic (bool 0x196), Stacking_Category (int 0x178), Enable_Planetary_Bombardment (bool 0x193), Reinforcement_Deploy_Time_Multiplier (float 0x18c), Disable_Reinforcement_Vulnerability (bool 0x194)

**Remote_Bomb_Ability** (RemoteBombAbilityClass): Bomb_Type (particle type 0x180), Activation_Min_Range (float 0x178), Activation_Max_Range (float 0x17c), Toss_Anim (enum 0x190), Spawn_Frame (float 0x194), Spawn_Bone (string 0x198)

**Repair_Ability** (RepairAbilityClass): Team_Member_With_Ability (particle type 0x1e8), Activation_Min_Range (float 0x178), Activation_Max_Range (float 0x17c), Lightning_Effect_Name (string 0x180), Lightning_Source_Bone_Name (string 0x1a0), Lightning_Target_Bone_Name (string 0x1c0), Lightning_Max_Targets (int 0x1e0), Lightning_Targets_Radius (float 0x1e4)

**Retreat_Protection_Ability** (RetreatProtectionAbilityClass): Retreat_Loss_Mitigation (float (chance) 0x178), Stacking_Category (int 0x17c)

**Saber_Throw_Ability** (SaberThrowAbilityClass): Activation_Min_Range (float 0x178), Activation_Max_Range (float 0x17c), Catch_Dist (float 0x180), Saber_Name (string 0x188)

**Sabotage_Political_Control_Ability** (SabotagePoliticalControlAbilityClass): Political_Change (int 0x178), Change_Duration_In_Seconds (float 0x180)

**Sensor_Jamming_Ability** (SensorJammingAbilityClass): Duration_In_Secs (float 0x178), Blob_Color (22 0x1a0), Blob_Material_Name (string 0x180), Show_Blob_To_Enemies (bool 0x1b0), Stealth_Color (22 0x178), Stealth_Transition_Time (float 0x188)

**Shield_Flare_Ability** (ShieldFlareAbilityClass): Max_Damage_Per_Victim (float 0x178), Damage_Radius (float 0x17c), Charge_Up_Seconds (float 0x180), Stealth_Color (22 0x178), Stealth_Transition_Time (float 0x188)

**Siphon_Credits_Ability** (SiphonCreditsAbilityClass): Min_Siphon_Percentage (float (chance) 0x178), Max_Siphon_Percentage (float (chance) 0x17c), Siphon_Duration_In_Cycles (int 0x180)

**Spawn_Ability** (SpawnAbilityClass): Activation_Min_Range (float 0x178), Activation_Max_Range (float 0x17c), Object_Type (particle type 0x180), Creation_Delay_In_Seconds (float 0x190), Recharge_Time_In_Seconds (float 0x194), Spawn_Bone_Name (string 0x198), Self_Destruct_Radius (float 0x1b8), Explosion_Type (particle type 0x1c0)

**Stun_Ability** (StunAbilityClass): Activation_Min_Range (float 0x178), Activation_Max_Range (float 0x17c), Stun_Time_In_Secs (float 0x180), Stun_Range (float 0x184), Stun_Travel_Time_In_Secs (float 0x188), Stunned_Effect (particle type 0x190)

**Summon_Ability** (SummonAbilityClass): Activation_Min_Range (float 0x178), Activation_Max_Range (float 0x17c), Object_Type (particle type 0x180), Creation_Delay_In_Seconds (float 0x190), SFXEvent_Unit_Summoned (SFX event 0x198)

**Super_Laser_Ability** (SuperLaserAbilityClass): Activation_Min_Range (float 0x17c), Activation_Max_Range (float 0x180), Damage_Per_Frame (float 0x178), Fire_Frame (float 0x184), Attack_Anim_Sub_Index (5 0x188), Beam_Texture_Name (string 0x190), Num_Anim_Frames (int 0x1b0), Line_Width (float 0x1b4), Line_Color (22 0x1b8), Face_Target (bool 0x1c8), Turn_Rate (float 0x1cc), Firing_Cone (float 0x1d0), Fire_Delay (float 0x1d4), Fire_Continuation (float 0x1d8)

**System_Spy_Ability** (SystemSpyAbilityClass): Duration_In_Secs (float 0x178), See_Base_Levels (bool 0x17c), See_Credit_Income (bool 0x17d), See_Credit_Income_Breakdown (bool 0x17e), See_Num_Fleets (bool 0x180), See_Most_Powerful_Ship (bool 0x181), See_Fleet_Contents (bool 0x182), See_Num_Ground_Companies (bool 0x183), See_Ground_Company_Contents (bool 0x184), See_Special_Structures (bool 0x185), See_Political_Control (bool 0x186), See_Political_Control_Breakdown (bool 0x187), See_Current_Production (bool 0x17f), See_Minor_Stealth_Heroes (bool 0x188), See_Major_Stealth_Heroes (bool 0x189), See_Force_Sensitive_Heroes (bool 0x18a), See_Super_Weapons (bool 0x18b)

**Tractor_Beam_Attack_Ability** (TractorBeamAttackAbilityClass): Activation_Min_Range (float 0x180), Activation_Max_Range (float 0x184), Target_Speed_Decrease_Percent (float 0x178), Stacking_Category (int 0x17c)

**Vehicle_Thief_Ability** (VehicleThiefAbilityClass): Activation_Chance (float 0x180), Activation_Min_Range (float 0x178), Activation_Max_Range (float 0x17c)

**Weatherproof_Ability** (WeatherproofAbilityClass): Apply_To_All_Allies (bool 0x178)


## System Spy own range (built 2026-11-17, ZZ_SWFOC_spy_range.dll)
`galactic_ranges on` + `zz_galactic_ranges.txt` (NAME RANGE; NAME = System_Spy_Ability Name= or unit type). The two reads of
+0x1a00 in System Spy's slot-21 method are redirected; the ability entry name is read from the MSVC string at ability +0x18
(base ctor 0x14048c780 initialises it; to be confirmed by the log line "galactic range: System Spy on ... entry ...").
