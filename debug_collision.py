import sys
import os
import math

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import constants
from entities.bot import Bot

def debug_collision():
    print("Initializing Bot...")
    bot = Bot("TestBot", 0, 0)
    bot.velocity_x = 500 # High speed
    bot.max_hp = 100
    bot.hp = 100
    print(f"Initial State: HP={bot.hp}, VelX={bot.velocity_x}, X={bot.x}")
    
    # Mock GameMap
    class MockMap:
        def __init__(self):
            self.width = 10
            self.height = 10
            self.terrain = [[constants.GRASS for _ in range(10)] for _ in range(10)]
            self.obstacles = set()
            
    game_map = MockMap()
    # Place obstacle at (1, 0)
    game_map.obstacles.add((1, 0))
    print(f"Obstacle placed at (1, 0). TILE_SIZE={constants.TILE_SIZE}")
    
    # Update movement with collision
    # dt=0.1 -> move 50 units. TILE_SIZE is usually 32. 50 > 32.
    # Should hit (1,0)
    print("Calling update_movement(1, 0, 0.1, game_map)...")
    bot.update_movement(1, 0, 0.1, game_map)
    
    print(f"Final State: HP={bot.hp}, VelX={bot.velocity_x}, X={bot.x}")
    
    if bot.hp < 100:
        print("SUCCESS: Damage taken.")
    else:
        print("FAILURE: No damage taken.")

if __name__ == "__main__":
    debug_collision()
