import sys
import os
import json
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import constants
from entities.player import Player
from equipment.component import create_starter_torso, create_starter_arm
from systems.saveload import SaveLoadSystem
from hex_system.hex_coord import HexCoord

def verify_persistence():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("PersistenceTest")
    
    # Setup
    save_dir = "tests/saves"
    data_dir = "tests/data"
    sl_system = SaveLoadSystem(save_dir, data_dir)
    profile = "test_profile"
    
    # Create Player
    player = Player("TestHero", 100, 100)
    player.hp = 80
    
    # Equip items
    torso = create_starter_torso()
    torso.level = 5
    player.equip_component(torso)
    
    arm = create_starter_arm("right_arm")
    arm.quality = "Rare"
    player.equip_component(arm)
    
    # Add to inventory
    extra_arm = create_starter_arm("left_arm")
    player.add_to_inventory(extra_arm)
    
    # Save
    logger.info("Saving game...")
    success = sl_system.save_game(profile, player)
    if not success:
        logger.error("Failed to save game")
        return False
        
    # Load
    logger.info("Loading game...")
    loaded_player = sl_system.load_game(profile)
    if not loaded_player:
        logger.error("Failed to load game")
        return False
        
    # Verify
    logger.info("Verifying data...")
    
    # Check basic stats
    if loaded_player.name != player.name:
        logger.error(f"Name mismatch: {loaded_player.name} != {player.name}")
        return False
    if loaded_player.hp != player.hp:
        logger.error(f"HP mismatch: {loaded_player.hp} != {player.hp}")
        return False
        
    # Check components
    loaded_torso = loaded_player.components.get("torso")
    if not loaded_torso:
        logger.error("Torso missing in loaded player")
        return False
    if loaded_torso.level != torso.level:
        logger.error(f"Torso level mismatch: {loaded_torso.level} != {torso.level}")
        return False
        
    loaded_arm = loaded_player.components.get("right_arm")
    if not loaded_arm:
        logger.error("Right arm missing in loaded player")
        return False
    if loaded_arm.quality != arm.quality:
        logger.error(f"Arm quality mismatch: {loaded_arm.quality} != {arm.quality}")
        return False
        
    # Check inventory
    if len(loaded_player.inventory) != len(player.inventory):
        logger.error(f"Inventory size mismatch: {len(loaded_player.inventory)} != {len(player.inventory)}")
        return False
        
    logger.info("Persistence verification PASSED!")
    return True

if __name__ == "__main__":
    if verify_persistence():
        sys.exit(0)
    else:
        sys.exit(1)
