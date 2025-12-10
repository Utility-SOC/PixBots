
import unittest
import sys
from unittest.mock import MagicMock

# Mock pygame before importing modules that use it
sys.modules["pygame"] = MagicMock()

from equipment.component import ComponentEquipment
from hex_system.hex_tile import BasicConduitTile, WeaponMountTile, TileCategory
from hex_system.hex_coord import HexCoord
from hex_system.energy_packet import ProjectileContext, SynergyType

class TestWeaponFire(unittest.TestCase):
    def test_weapon_capture(self):
        comp = ComponentEquipment(name="TestComp", slot="right_arm", grid_width=3, grid_height=3)
        comp.valid_coords = {HexCoord(0,0), HexCoord(1,0)}
        conduit = BasicConduitTile("Conduit", TileCategory.CONDUIT)
        comp.tile_slots[HexCoord(0,0)] = conduit
        weapon = WeaponMountTile("Gun", TileCategory.OUTPUT)
        comp.tile_slots[HexCoord(1,0)] = weapon
        
        ctx = ProjectileContext(synergies={SynergyType.RAW: 100.0})
        # Simulate flow usually looks for 'entry' hexes if input_context is provided but start_coord is not.
        # But simulate_flow defaults start_coord to get_entry_exit_hexes() entry.
        # We need to make sure (0,0) is recognized as entry.
        # Component.get_entry_exit_hexes depends on slot.
        # Let's manually invoke simulate_flow loop logic concept or just rely on standard behavior?
        # Component.simulate_flow() finds entry based on slot. "test_arm" might default?
        # Let's force start_coord logic by subclassing or mocking?
        # Actually, simulate_flow iterates `self.tile_slots` to find defaults if not specific.
        # Let's just pass `input_context` and let it find entry?
        # No, simulate_flow logic: 
        # "entry_hex, exit_hex = self.get_entry_exit_hexes()"
        # "if entry_hex: queue.append((entry_hex, input_direction, input_context))"
        
        # We need to ensure get_entry_exit_hexes returns (0,0).
        # It relies on min_q/max_q.
        # (0,0) is min_q for this grid.
        
        _, stats, _ = comp.simulate_flow(input_context=ctx, input_direction=3)
        print(f"Stats: {stats}")
        self.assertGreater(stats["weapon_damage"], 0, "Weapon damage should be > 0")
        self.assertEqual(stats["weapon_damage"], 100.0, "Should capture full 100 damage")

    def test_internal_fizzle_fix(self):
        # Use a valid slot so get_entry_exit_hexes works, or manually ensure entry
        comp = ComponentEquipment(name="TestInternal", slot="right_arm", grid_width=5, grid_height=5)
        
        # Setup: Conduit at (2,1) -> Weapon at (2,2)
        # For right_arm, entry is min_q. (0,y).
        # Let's just manually force the flow by ensuring we have a path from entry.
        # Or simpler: Just use a conduit at (0,2) -> (1,2) -> (2,2) Weapon.
        
        conduit1 = BasicConduitTile("C1", TileCategory.CONDUIT)
        conduit2 = BasicConduitTile("C2", TileCategory.CONDUIT)
        weapon = WeaponMountTile("Gun", TileCategory.OUTPUT)
        
        comp.tile_slots[HexCoord(0,2)] = conduit1
        comp.tile_slots[HexCoord(1,2)] = conduit2
        comp.tile_slots[HexCoord(2,2)] = weapon
        
        # Ensure valid coords exist
        comp.valid_coords = {HexCoord(0,2), HexCoord(1,2), HexCoord(2,2)}
        
        ctx = ProjectileContext(synergies={SynergyType.FIRE: 50.0})
        
        # Input at (0,2) from West (3)
        _, stats, _ = comp.simulate_flow(input_context=ctx, input_direction=3)
        print(f"Internal Stats: {stats}")
        self.assertEqual(stats["weapon_damage"], 50.0, "Internal weapon should capture damage")

if __name__ == '__main__':
    try:
        t = TestWeaponFire()
        print("Running test_weapon_capture...")
        t.test_weapon_capture()
        print("test_weapon_capture PASS")
        
        print("Running test_internal_fizzle_fix...")
        t.test_internal_fizzle_fix()
        print("test_internal_fizzle_fix PASS")
    except Exception as e:
        import traceback
        traceback.print_exc()
