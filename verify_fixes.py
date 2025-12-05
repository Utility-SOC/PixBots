import sys
import os
import logging
import unittest
from unittest.mock import MagicMock

# Setup path
sys.path.append(os.getcwd())
sys.modules["pygame"] = MagicMock()

from hex_system.energy_packet import ProjectileContext, SynergyType
from systems.synergy_manager import SynergyManager
from equipment.component import ComponentEquipment, create_starter_arm
from hex_system.hex_tile import WeaponMountTile, TileCategory
from hex_system.hex_coord import HexCoord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Verification")

class TestFixes(unittest.TestCase):
    def test_component_synergy_effects_population(self):
        logger.info("Testing ComponentEquipment active_synergy_effects population...")
        
        # Mock SynergyManager to return specific effects
        sm = SynergyManager()
        # Ensure data is loaded or defaulted
        
        # Create arm
        arm = create_starter_arm("right_arm")
        
        # Create context with FIRE
        context = ProjectileContext()
        context.add_synergy(SynergyType.FIRE, 100.0)
        
        # Simulate flow
        _, stats, _ = arm.simulate_flow(input_context=context, input_direction=3)
        
        # Check if active_synergy_effects is populated
        effects = stats.get("active_synergy_effects", {})
        logger.info(f"Active Synergy Effects: {effects}")
        
        self.assertIn("active_synergies", effects)
        self.assertIn("fire", effects["active_synergies"])
        
    def test_multi_vector_stats(self):
        logger.info("Testing Multi-Vector stats with Splitters...")
        # Create arm manually
        comp = ComponentEquipment(name="Test Arm", slot="right_arm")
        comp.valid_coords = {HexCoord(0,0), HexCoord(1,0), HexCoord(0,1)}
        comp.max_tile_capacity = 3
        
        # Mount at (1,0)
        mount = WeaponMountTile(tile_type="Weapon Mount", category=TileCategory.OUTPUT, weapon_type="beam")
        comp.place_tile(HexCoord(1,0), mount)
        
        # Splitter at (0,0)
        # Input from West (3). 
        # Output 1: East (0) -> Hits Mount (1,0)
        # Output 2: SE (5) -> Goes to (0,1)
        from hex_system.hex_tile import SplitterTile, BasicConduitTile
        from hex_system.hex_coord import HexCoord
        splitter = SplitterTile(split_count=2)
        splitter.set_exit_direction(0, 0) # East
        splitter.set_exit_direction(1, 5) # SE
        comp.place_tile(HexCoord(0,0), splitter)
        
        # Conductor at (0,1)
        # Input from NW (2). Output NE (1) -> Hits Mount (1,0)
        cond = BasicConduitTile()
        cond.set_exit_direction(1) # NE
        comp.place_tile(HexCoord(0,1), cond)
        
        # Simulate input at (0,0) from West (3)
        context = ProjectileContext()
        context.add_synergy(SynergyType.RAW, 100.0)
        
        _, stats, _ = comp.simulate_flow(input_context=context, input_direction=3)
        
        weapon_inputs = stats.get("weapon_inputs", set())
        logger.info(f"Weapon Inputs: {weapon_inputs}")
        
        # Should have 2 inputs:
        # 1. From Splitter (West side of Mount? No, Splitter is at (0,0), Mount at (1,0). Splitter is West of Mount. So input from West (3)?)
        # Wait, entry_dir is the side of the TILE entered.
        # Flow 1: (0,0) -> (1,0). Moving East. Enters West side (3).
        # Flow 2: (0,0) -> (0,1) -> (1,0).
        # (0,1) is SE of (0,0). (1,0) is NE of (0,1).
        # Moving NE. Enters SW side (4).
        
        # So inputs should be {3, 4}
        self.assertEqual(len(weapon_inputs), 2)
        self.assertIn(3, weapon_inputs)
        self.assertIn(4, weapon_inputs)

if __name__ == '__main__':
    unittest.main()
