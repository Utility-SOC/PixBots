import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging_setup
logging_setup.configure_logging()

from world.biome import BiomeManager

def test_crash():
    seed = 419617
    print(f"Testing BiomeManager with seed {seed}...")
    try:
        bm = BiomeManager(seed=seed)
        print("BiomeManager initialized.")
        
        # Simulate some calls
        for x in range(0, 100, 10):
            for y in range(0, 100, 10):
                bt = bm.get_biome_type(x, y)
                tt = bm.get_terrain_type(x, y)
                col = bm.get_biome_color(x, y)
                obs = bm.should_spawn_obstacle(x, y)
                if obs:
                    ot = bm.get_obstacle_type(x, y)
        
        print("Test completed without crash.")
    except Exception as e:
        print(f"CRASH CAUGHT: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_crash()
