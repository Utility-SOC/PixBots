import sys
import os
import logging
from unittest.mock import MagicMock

sys.path.append(os.getcwd())
sys.modules["pygame"] = MagicMock()

from hex_system.energy_packet import ProjectileContext, SynergyType
from equipment.component import ComponentEquipment
from hex_system.hex_tile import ReflectorTile, BasicConduitTile
from hex_system.hex_coord import HexCoord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ReflectorCrashTest")

def test_reflector_crash():
    logger.info("Testing Reflector Logic...")
    
    comp = ComponentEquipment(name="Reflector Test", slot="right_arm", quality="Common")
    comp.valid_coords = {HexCoord(0,0), HexCoord(1,0), HexCoord(2,0)}
    
    # 1. Reflector at (1,0)
    # Target: FIRE. Offset: 1.
    reflector = ReflectorTile(target_synergy="fire", reflection_offset=1)
    comp.place_tile(HexCoord(1,0), reflector)
    
    # 2. Conductor at (2,0) (East of Reflector) -> Straight path
    cond1 = BasicConduitTile()
    comp.place_tile(HexCoord(2,0), cond1)
    
    # 3. Conductor at (1,1) (SE of Reflector) -> Reflected path (if input from West)
    # Wait, (1,1) is SE of (1,0) in axial?
    # (1,0) neighbors:
    # 0: (2,0) E
    # 1: (2,-1) NE
    # 2: (1,-1) NW
    # 3: (0,0) W
    # 4: (0,1) SW
    # 5: (1,1) SE
    
    # If input from West (3), straight exit is East (0).
    # Reflected offset 1 -> (0+1)%6 = 1 (NE).
    # So reflected path should go to (2,-1).
    
    # Let's place tiles at all neighbors to be safe
    
    # Simulate Input from West (3)
    # Mix of FIRE and ICE
    context = ProjectileContext(synergies={
        SynergyType.FIRE: 50.0,
        SynergyType.ICE: 50.0
    })
    
    logger.info("Simulating flow...")
    try:
        # Input direction 3 (West side of tile)
        _, stats, _ = comp.simulate_flow(input_context=context, input_direction=3)
        logger.info("Simulation completed successfully.")
        logger.info(f"Stats: {stats}")
    except Exception as e:
        logger.error(f"CRASH DETECTED: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    test_reflector_crash()
