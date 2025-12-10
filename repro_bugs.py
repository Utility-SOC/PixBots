
import unittest
import sys
from unittest.mock import MagicMock

# Mock pygame
sys.modules["pygame"] = MagicMock()

from equipment.component import ComponentEquipment
from hex_system.hex_tile import WeaponMountTile, TileCategory, BasicConduitTile
from hex_system.hex_coord import HexCoord
from hex_system.energy_packet import ProjectileContext, SynergyType

class TestBugs(unittest.TestCase):
    def test_kinetic_magnitudes(self):
        """Test that kinetic synergy magnitude is correctly reported in stats."""
        print("\n--- Testing Kinetic Magnitude ---")
        comp = ComponentEquipment(name="KineticGun", slot="right_arm", grid_width=3, grid_height=3)
        comp.valid_coords = {HexCoord(0,0), HexCoord(1,0)}
        
        # Setup: Input -> Weapon
        # Input at (0,0), Weapon at (1,0)
        comp.tile_slots[HexCoord(0,0)] = BasicConduitTile("Conduit", TileCategory.CONDUIT)
        comp.tile_slots[HexCoord(1,0)] = WeaponMountTile("Gun", TileCategory.OUTPUT)
        
        # Input 100 Kinetic
        ctx = ProjectileContext(synergies={SynergyType.KINETIC: 100.0})
        
        # Simulate
        _, stats, _ = comp.simulate_flow(input_context=ctx, input_direction=3)
        
        print(f"Stats Synergy Magnitudes: {stats.get('synergy_magnitudes')}")
        
        # Check if kinetic is present and correct
        magnitudes = stats.get("synergy_magnitudes", {})
        kinetic_val = magnitudes.get("kinetic", 0.0)
        
        self.assertGreater(kinetic_val, 0, "Kinetic magnitude should be > 0")
        self.assertEqual(kinetic_val, 100.0, "Kinetic magnitude should be 100.0")

    def test_vampirism_power(self):
        """Test that vampiric power is passed to effects."""
        print("\n--- Testing Vampirism Power ---")
        comp = ComponentEquipment(name="VampGun", slot="right_arm", grid_width=3, grid_height=3)
        comp.valid_coords = {HexCoord(0,0), HexCoord(1,0)}
        
        comp.tile_slots[HexCoord(0,0)] = BasicConduitTile("Conduit", TileCategory.CONDUIT)
        comp.tile_slots[HexCoord(1,0)] = WeaponMountTile("Gun", TileCategory.OUTPUT)
        
        # Input 100 Vampiric
        ctx = ProjectileContext(synergies={SynergyType.VAMPIRIC: 100.0})
        
        _, stats, _ = comp.simulate_flow(input_context=ctx, input_direction=3)
        
        effects = stats.get("active_synergy_effects", {})
        print(f"Active Synergy Effects: {effects}")
        
        # Check for vampiric_power
        self.assertIn("vampiric_power", effects, "vampiric_power should be in effects")
        self.assertEqual(effects["vampiric_power"], 100.0, "vampiric_power should be 100.0")

if __name__ == '__main__':
    unittest.main()
