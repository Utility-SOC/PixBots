import sys
import os
import logging

# Add project root to path
sys.path.append(os.getcwd())

import pygame
import systems.music as music
from world.biome import BiomeManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_music_generation():
    logger.info("Initializing Music System...")
    pygame.init()
    music.init()
    
    biomes_to_test = ["grassland", "volcano", "tundra", "mountainous", "beach"]
    
    for biome in biomes_to_test:
        logger.info(f"Testing biome: {biome}")
        music.music_system.set_biome(biome)
        
        # New API uses 'biomes' instead of 'biome_params'
        params = music.music_system.biomes.get(biome)
        if not params:
            logger.error(f"Biome {biome} not found in params!")
            continue
            
        logger.info(f"  Params: {params}")
        
        # Generate a melody to ensure no crashes
        try:
            # New API: _gen_melody takes the config dict directly
            # We access the internal method for verification
            melody = music.music_system._gen_melody(params)
            logger.info(f"  Generated {len(melody)} notes successfully.")
            
            # Verify waveform type (indirectly via sound generation)
            if melody and melody[0].sound:
                logger.info("  Sound object created successfully.")
                
        except Exception as e:
            logger.error(f"  Failed to generate melody for {biome}: {e}")

    music.shutdown()
    pygame.quit()
    logger.info("Verification Complete.")

if __name__ == "__main__":
    verify_music_generation()
