import sys
import os
import logging
from unittest.mock import MagicMock

sys.path.append(os.getcwd())
sys.modules["pygame"] = MagicMock()

from hex_system.energy_packet import ProjectileContext, SynergyType
from equipment.component import ComponentEquipment
from hex_system.hex_tile import SplitterTile, BasicConduitTile
from hex_system.hex_coord import HexCoord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifySplitterFix")

def test_splitter_fix():
    logger.info("Testing Splitter Logic...")
    
    comp = ComponentEquipment(name="Splitter Fix Test", slot="right_arm", quality="Common")
    comp.valid_coords = {HexCoord(0,0), HexCoord(1,0), HexCoord(0,1)}
    
    # Splitter at (0,0)
    # Input from West (3).
    # Exit 1: East (0) -> (1,0)
    # Exit 2: SE (5) -> (0,1)
    splitter = SplitterTile(split_count=2)
    splitter.set_exit_direction(0, 0)
    splitter.set_exit_direction(1, 5)
    comp.place_tile(HexCoord(0,0), splitter)
    
    # Conductor at (1,0) (NE neighbor)
    comp.place_tile(HexCoord(1,0), BasicConduitTile())
    
    # Conductor at (0,1) (SE neighbor)
    comp.place_tile(HexCoord(0,1), BasicConduitTile())
    
    # Simulate
    context = ProjectileContext(synergies={SynergyType.RAW: 100.0})
    _, stats, _ = comp.simulate_flow(input_context=context, input_direction=3)
    
    active_tiles = stats.get("active_tiles", 0)
    logger.info(f"Active Tiles: {active_tiles}")
    
    if active_tiles == 3:
        print("VERIFICATION SUCCESS: Splitter working (3 active tiles).")
    else:
        print(f"VERIFICATION FAILURE: Splitter broken (Expected 3, got {active_tiles}).")

if __name__ == "__main__":
    test_splitter_fix()
