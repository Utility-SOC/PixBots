import pygame
import random
from entities.sprite_generator import ProceduralBotGenerator
import os

# Mock pygame setup
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((1,1))

def test_generation():
    generator = ProceduralBotGenerator()
    
    print("Generating 5 bosses...")
    hashes = []
    for i in range(5):
        # Simulate Enemy.__init__ logic
        seed = random.randint(0, 999999)
        print(f"Boss {i} Seed: {seed}")
        
        surf = generator.generate_boss(seed)
        
        # Simple hash of surface data
        data = pygame.image.tostring(surf, 'RGBA')
        h = hash(data)
        hashes.append(h)
        print(f"Boss {i} Hash: {h}")
        
    if len(set(hashes)) < 5:
        print("FAIL: Duplicate bosses generated!")
    else:
        print("PASS: All bosses unique.")

if __name__ == "__main__":
    test_generation()
