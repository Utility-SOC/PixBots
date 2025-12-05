import pygame
import os
import sys

# Mock pygame setup
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((1,1))

from entities.enemy import Enemy

def test_generation():
    print("Testing procedural generation...")
    
    try:
        # Test Grunt
        grunt = Enemy("Grunt", 0, 0, ai_class="grunt")
        if grunt.sprite: print("Grunt generated successfully.")
        
        # Test Sniper
        sniper = Enemy("Sniper", 0, 0, ai_class="sniper")
        if sniper.sprite: print("Sniper generated successfully.")
        
        # Test Ambusher
        ambusher = Enemy("Ambusher", 0, 0, ai_class="ambusher", biome="desert")
        if ambusher.sprite: print("Ambusher generated successfully.")
        
        # Test Boss
        boss = Enemy("Boss", 0, 0, ai_class="Boss")
        if boss.sprite: print("Boss generated successfully.")
        
        print("All procedural tests passed!")
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_generation()
