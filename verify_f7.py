import sys
import os
import logging
from unittest.mock import MagicMock

sys.path.append(os.getcwd())
sys.modules["pygame"] = MagicMock()

from hex_system.energy_packet import ProjectileContext, SynergyType
from equipment.component import ComponentEquipment
from hex_system.hex_tile import WeaponMountTile, TileCategory, SplitterTile, BasicConduitTile
from hex_system.hex_coord import HexCoord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyF7")

def test_f7_logic():
    logger.info("Testing F7 Arm Logic...")
    
    # Recreate the F7 arm setup manually
    comp = ComponentEquipment(name="Multi-Vector Test Arm", slot="right_arm", quality="Legendary")
    comp.valid_coords = {
        HexCoord(0,0), HexCoord(1,0), HexCoord(2,0),
        HexCoord(0,1), HexCoord(1,1), HexCoord(2,1),
        HexCoord(0,2), HexCoord(1,2), HexCoord(2,2)
    }
    
    # 1. Mount at (1,1)
    mount = WeaponMountTile(tile_type="Weapon Mount", category=TileCategory.OUTPUT, weapon_type="beam")
    comp.place_tile(HexCoord(1,1), mount)
    
    # 2. Splitter at Entry (0,1)
    # Input from West (3). Splits to NE (1) and SE (5).
    splitter = SplitterTile(split_count=2)
    splitter.set_exit_direction(0, 1) # NE
    splitter.set_exit_direction(1, 5) # SE
    comp.place_tile(HexCoord(0,1), splitter)
    
    # 3. Conductor at (1,0) (Top)
    # Input from SW (4) (from Splitter NE). Output SE (5) -> Hits Mount (1,1)
    top_cond = BasicConduitTile()
    top_cond.set_exit_direction(5)
    comp.place_tile(HexCoord(1,0), top_cond)
    
    # 4. Conductor at (0,2) (Bottom)
    # Input from NW (2) (from Splitter SE). Output NE (1) -> Hits Mount (1,1)
    bot_cond = BasicConduitTile()
    bot_cond.set_exit_direction(1)
    comp.place_tile(HexCoord(0,2), bot_cond)
    
    # Simulate Input from West (3)
    context = ProjectileContext(synergies={SynergyType.RAW: 100.0})
    
    # Entry is (0,1). Input direction is 3 (West).
    _, stats, _ = comp.simulate_flow(input_context=context, input_direction=3)
    
    weapon_inputs = stats.get("weapon_inputs", set())
    logger.info(f"Weapon Inputs: {weapon_inputs}")
    logger.info(f"Spread Count: {len(weapon_inputs)}")
    
    if len(weapon_inputs) >= 2:
        print("VERIFICATION SUCCESS: Multi-Vector confirmed.")
    else:
        print("VERIFICATION FAILURE: Single vector only.")

if __name__ == "__main__":
    test_f7_logic()
