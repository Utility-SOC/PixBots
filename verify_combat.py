import pygame
import math
import sys
import os

# Mock environment
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((1,1))

from systems.combat_system import CombatSystem
from entities.bot import Bot
import constants

# Mock Asset Manager
class MockAssetManager:
    def get_image(self, name):
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 0, 0), (16, 16), 16) # Circle mask
        return surf

# Mock Map
class MockMap:
    def __init__(self):
        self.width = 100
        self.height = 100
        self.terrain = [[0 for _ in range(100)] for _ in range(100)]
        self.obstacles = set()

def test_combat():
    print("Testing Combat System...")
    
    asset_manager = MockAssetManager()
    combat = CombatSystem(asset_manager)
    game_map = MockMap()
    
    # Create Bots
    player = Bot("Player", 100, 100, hp=100)
    player.sprite = asset_manager.get_image("player")
    player.mask = pygame.mask.from_surface(player.sprite)
    
    enemy1 = Bot("Enemy1", 200, 200, hp=100) # Target
    enemy1.sprite = asset_manager.get_image("enemy")
    enemy1.mask = pygame.mask.from_surface(enemy1.sprite)
    
    enemy2 = Bot("Enemy2", 300, 300, hp=100) # Shooter
    
    all_bots = [player, enemy1, enemy2]
    
    # Test 1: Enemy shoots Enemy (Friendly Fire Check)
    print("\nTest 1: Enemy Friendly Fire (Projectile)")
    combat.spawn_projectile(200, 200, 0, 0, 10, "energy", "enemy") # Spawn ON TOP of enemy1
    combat.update(0.1, game_map, all_bots)
    
    if enemy1.hp < 100:
        print("FAILED: Enemy took damage from enemy projectile!")
    else:
        print("PASSED: Enemy ignored enemy projectile.")
        
    # Test 2: Enemy shoots Player
    print("\nTest 2: Enemy hits Player")
    combat.projectiles = []
    combat.spawn_projectile(100, 100, 0, 0, 10, "energy", "enemy") # Spawn ON TOP of player
    combat.update(0.1, game_map, all_bots)
    
    if player.hp < 100:
        print("PASSED: Player took damage from enemy projectile.")
    else:
        print("FAILED: Player ignored enemy projectile!")

    # Test 3: Mask Collision (Pixel Perfect)
    print("\nTest 3: Mask Collision")
    combat.projectiles = []
    # Spawn projectile at (200, 200) which is center of enemy1 (Hit)
    combat.spawn_projectile(200, 200, 0, 0, 10, "energy", "player") 
    combat.update(0.1, game_map, all_bots)
    if enemy1.hp < 100:
        print("PASSED: Center hit registered.")
    else:
        print("FAILED: Center hit missed!")
        
    # Reset HP
    enemy1.hp = 100
    combat.projectiles = []
    
    # Spawn projectile at (184, 184) -> Top-left corner of 32x32 sprite centered at 200,200
    # Sprite is circle, so corners are empty. Should MISS.
    # Center is 200,200. Radius 16.
    # Top-Left bounds: 184, 184.
    # Point 185, 185 is inside bounds but outside circle.
    combat.spawn_projectile(185, 185, 0, 0, 10, "energy", "player")
    combat.update(0.1, game_map, all_bots)
    
    if enemy1.hp < 100:
        print("FAILED: Corner hit registered (Mask check failed)!")
    else:
        print("PASSED: Corner hit ignored (Mask check worked).")

    # Test 4: Vortex Smash Friendly Fire
    print("\nTest 4: Vortex Smash Friendly Fire")
    combat.projectiles = []
    # Spawn Enemy Vortex near Enemy1
    combat.spawn_projectile(210, 210, 0, 0, 10, "energy", "enemy", effects={"synergy_name": "vortex"})
    
    # Move Enemy2 close to Enemy1
    enemy2.x = 210
    enemy2.y = 210
    
    hp_before = enemy1.hp
    combat.update(0.1, game_map, all_bots)
    
    if enemy1.hp < hp_before:
        print("FAILED: Enemy took smash damage from enemy vortex!")
    else:
        print("PASSED: Enemy ignored enemy vortex smash.")

if __name__ == "__main__":
    test_combat()
