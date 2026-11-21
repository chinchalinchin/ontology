
##### Bug B044: `CursorProperties.weapon` Schema Mismatch Allows Unvalidated Weapon Bindings and Prevents Many-to-One Sharing

**STATUS**: OPEN
**SEVERITY**: LOW

**Description**

Per Phase 03.04 Specification §1, `CursorProperties` (`src/app/models/properties/assets.py`) should declare `weapons: List[Enumerated[WeaponPalette]] = field(default_factory=list)` and `rotation: int = 90` so that:
1. All weapon foreign keys are validated against `WeaponPalette` at boot via Pydantic `TypeAdapter`.
2. Multiple weapons (e.g., `shortbow` and `longbow`) can share a single projectile asset (`arrow`), while unbound projectiles (e.g., `cannonball`) default to `[]`.

Currently, `CursorProperties` defines `weapon: Optional[str] = None` and `rotation: Optional[int] = None`, `ProjectileIndex.from_properties()` reads singular `props.weapon`, and `src/assets/cursors/main.yaml` declares `cannonball.weapon: cannon`, which is a dangling weapon key absent from `src/assets/sheets/equipment/weapons/main.yaml`. Because `weapon` is an unvalidated `Optional[str]`, invalid or misspelled weapon references silently pass boot validation.

**Steps to Replicate**

1. Inspect `src/app/models/properties/assets.py` (`CursorProperties.weapon: Optional[str] = None`) and `src/assets/cursors/main.yaml` (`cannonball.weapon: cannon`).
2. Load properties via `Loader.load_properties()` and compile `ProjectileIndex.from_properties(properties.cursors.projectiles)`.
3. Observe that `ProjectileIndex.resolve("cannon")` returns `"cannonball"` even though `"cannon"` is neither in `WeaponPalette` nor defined in `src/assets/sheets/equipment/weapons/main.yaml`, and no mechanism exists to bind a second weapon to `"arrow"`.

**Proposed Remediation**

Update `CursorProperties` to `rotation: int = 90` and `weapons: List[Enumerated[WeaponPalette]] = field(default_factory=list)`, align `src/assets/cursors/main.yaml` (`arrow.weapons: [longbow]`, `bolt.weapons: [crossbow]`, `cannonball.weapons: []`), and iterate `for weapon_id in props.weapons:` inside `ProjectileIndex.from_properties()`. (If kept as-is until `cannon` is added as a weapon, update `test_projectiles.py` accordingly when migrating to `weapons`.)


