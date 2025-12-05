import sys
import os
import logging
from unittest.mock import MagicMock

sys.path.append(os.getcwd())
sys.modules["pygame"] = MagicMock()

from hex_system.energy_packet import ProjectileContext, SynergyType
from equipment.component import ComponentEquipment, create_starter_arm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SimpleVerify")

try:
    logger.info("Creating Arm...")
    arm = create_starter_arm("right_arm")
    
    logger.info("Creating Context...")
    context = ProjectileContext()
    context.add_synergy(SynergyType.FIRE, 100.0)
    
    logger.info("Simulating Flow...")
    _, stats, _ = arm.simulate_flow(input_context=context, input_direction=3)
    
    logger.info("Checking Stats...")
    effects = stats.get("active_synergy_effects", {})
    logger.info(f"Effects: {effects}")
    
    if "active_synergies" in effects and "fire" in effects["active_synergies"]:
        print("VERIFICATION SUCCESS")
    else:
        print("VERIFICATION FAILURE: active_synergies missing or incorrect")
        
except Exception as e:
    logger.error(f"CRASH: {e}", exc_info=True)
    print("VERIFICATION CRASHED")
