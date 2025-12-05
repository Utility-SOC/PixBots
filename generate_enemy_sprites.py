import pygame
import os
import random
import math

def generate_enemy_sprites():
    pygame.init()
    
    sprites_dir = os.path.join("assets", "sprites", "bots")
    os.makedirs(sprites_dir, exist_ok=True)
    
    # --- Helper Functions ---
    def draw_ngon(surface, color, center, radius, n, width=0):
        points = []
        for i in range(n):
            angle = math.radians(i * (360/n) - 90)
            x = center[0] + math.cos(angle) * radius
            y = center[1] + math.sin(angle) * radius
            points.append((x, y))
        pygame.draw.polygon(surface, color, points, width)

    # 1. Grunt Variants (Tank-like)
    for i in range(4):
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        # Randomize chassis slightly
        width = random.randint(14, 18)
        length = random.randint(14, 18)
        
        # Tracks
        pygame.draw.rect(surf, (50, 50, 50), (16-width//2-4, 16-length//2-2, 4, length+4)) # L
        pygame.draw.rect(surf, (50, 50, 50), (16+width//2, 16-length//2-2, 4, length+4)) # R
        
        # Body
        body_color = (85 + random.randint(-10, 10), 107 + random.randint(-10, 10), 47 + random.randint(-10, 10))
        pygame.draw.rect(surf, body_color, (16-width//2, 16-length//2, width, length))
        pygame.draw.rect(surf, (60, 80, 20), (16-width//2, 16-length//2, width, length), 2)
        
        # Turret (Random shape)
        turret_color = (100, 120, 60)
        if i % 2 == 0:
            pygame.draw.rect(surf, turret_color, (10, 10, 12, 12)) # Square
        else:
            pygame.draw.circle(surf, turret_color, (16, 16), 7) # Round
            
        # Eye/Sensor
        eye_color = (255, 100 + random.randint(-50, 50), 0)
        pygame.draw.circle(surf, eye_color, (16, 16), 3)
        
        # Gun (Random position)
        if i == 0: pygame.draw.rect(surf, (30, 30, 30), (14, 2, 4, 10)) # Center
        elif i == 1: pygame.draw.rect(surf, (30, 30, 30), (18, 4, 3, 8)) # Offset R
        elif i == 2: pygame.draw.rect(surf, (30, 30, 30), (10, 4, 3, 8)) # Offset L
        else: 
            pygame.draw.rect(surf, (30, 30, 30), (12, 2, 3, 10)) # Double
            pygame.draw.rect(surf, (30, 30, 30), (17, 2, 3, 10))
            
        pygame.image.save(surf, os.path.join(sprites_dir, f"enemy_grunt_{i}.png"))
        print(f"Generated enemy_grunt_{i}.png")
        
    # Fallback
    pygame.image.save(surf, os.path.join(sprites_dir, "enemy_grunt.png"))


    # 2. Sniper Variants (Triangular)
    for i in range(4):
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        
        # Body Shape variations
        points = []
        if i == 0: points = [(16, 2), (28, 28), (4, 28)] # Standard
        elif i == 1: points = [(16, 2), (30, 20), (16, 28), (2, 20)] # Diamond-ish
        elif i == 2: points = [(16, 2), (24, 28), (8, 28)] # Narrow
        else: points = [(16, 4), (30, 30), (2, 30)] # Wide
        
        pygame.draw.polygon(surf, (255, 215, 0), points) # Gold
        pygame.draw.polygon(surf, (0, 0, 0), points, 2)
        
        # Markings
        if i % 2 == 0:
            pygame.draw.line(surf, (0, 0, 0), (12, 12), (20, 12), 2)
        else:
            pygame.draw.circle(surf, (0,0,0), (16, 18), 4, 1)
            
        # Scope
        pygame.draw.circle(surf, (255, 0, 0), (16, 10), 3)
        
        # Barrel
        pygame.draw.line(surf, (50, 50, 50), (16, 10), (16, 0), 2)
        
        pygame.image.save(surf, os.path.join(sprites_dir, f"enemy_sniper_{i}.png"))
        print(f"Generated enemy_sniper_{i}.png")
        
    # Fallback
    pygame.image.save(surf, os.path.join(sprites_dir, "enemy_sniper.png"))


    # 3. Ambusher Variants (Spiky/Stealth)
    biomes = {
        "forest": (34, 139, 34),
        "desert": (237, 201, 175),
        "ice": (224, 255, 255),
        "volcanic": (40, 40, 40)
    }
    
    for biome, base_color in biomes.items():
        # Generate 2 variants per biome
        for i in range(2):
            surf = pygame.Surface((32, 32), pygame.SRCALPHA)
            
            # Variant shapes
            if i == 0:
                # 4-Point Star
                points = [(16, 2), (20, 12), (30, 16), (20, 20), (16, 30), (12, 20), (2, 16), (12, 12)]
            else:
                # X-Shape
                points = [(10, 4), (22, 4), (28, 10), (28, 22), (22, 28), (10, 28), (4, 22), (4, 10)]
                
            pygame.draw.polygon(surf, base_color, points)
            pygame.draw.polygon(surf, (0, 0, 0), points, 2)
            
            # Eye
            pygame.draw.circle(surf, (255, 0, 255), (16, 16), 4)
            
            pygame.image.save(surf, os.path.join(sprites_dir, f"enemy_ambusher_{biome}_{i}.png"))
            print(f"Generated enemy_ambusher_{biome}_{i}.png")
            
        # Fallback (use variant 0)
        pygame.image.save(surf, os.path.join(sprites_dir, f"enemy_ambusher_{biome}.png"))

    # Default ambusher fallback
    surf = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.circle(surf, (100, 0, 100), (16, 16), 10)
    pygame.image.save(surf, os.path.join(sprites_dir, "enemy_ambusher.png"))


    # 4. Boss: Mixed (Abstract + Robotic)
    # ... (Keep existing boss logic, it's already good)
    # Abstract 1: Sun/Eye (Gold/Red)
    surf = pygame.Surface((128, 128), pygame.SRCALPHA)
    pygame.draw.circle(surf, (255, 215, 0), (64, 64), 50)
    pygame.draw.circle(surf, (0, 0, 0), (64, 64), 50, 4)
    pygame.draw.circle(surf, (255, 0, 0), (64, 64), 20) # Eye
    # Rays
    for i in range(0, 360, 45):
        rad = math.radians(i)
        ex = 64 + math.cos(rad) * 60
        ey = 64 + math.sin(rad) * 60
        pygame.draw.line(surf, (255, 100, 0), (64, 64), (ex, ey), 4)
    pygame.image.save(surf, os.path.join(sprites_dir, "enemy_boss_0.png"))
    
    # Abstract 2: Ramiel (Blue Diamond)
    surf = pygame.Surface((128, 128), pygame.SRCALPHA)
    points = [(64, 14), (114, 64), (64, 114), (14, 64)]
    pygame.draw.polygon(surf, (0, 0, 255), points)
    pygame.draw.polygon(surf, (200, 200, 255), points, 4)
    pygame.draw.circle(surf, (255, 0, 0), (64, 64), 10) # Core
    pygame.image.save(surf, os.path.join(sprites_dir, "enemy_boss_1.png"))
    
    # Abstract 3: Monolith (Black Hexagon)
    surf = pygame.Surface((128, 128), pygame.SRCALPHA)
    draw_ngon(surf, (20, 20, 20), (64, 64), 50, 6)
    draw_ngon(surf, (0, 255, 0), (64, 64), 50, 6, 2) # Green outline
    # Matrix code?
    for i in range(5):
        y = 30 + i * 15
        pygame.draw.line(surf, (0, 255, 0), (40, y), (88, y), 1)
    pygame.image.save(surf, os.path.join(sprites_dir, "enemy_boss_2.png"))
    
    # Robotic 1: Mech (Humanoid)
    surf = pygame.Surface((128, 128), pygame.SRCALPHA)
    # Legs
    pygame.draw.rect(surf, (50, 50, 70), (40, 70, 15, 40))
    pygame.draw.rect(surf, (50, 50, 70), (73, 70, 15, 40))
    # Torso
    pygame.draw.rect(surf, (70, 70, 90), (35, 30, 58, 50))
    pygame.draw.rect(surf, (100, 100, 120), (35, 30, 58, 50), 3)
    # Shoulders
    pygame.draw.circle(surf, (50, 50, 70), (30, 40), 15)
    pygame.draw.circle(surf, (50, 50, 70), (98, 40), 15)
    # Head
    pygame.draw.rect(surf, (80, 80, 100), (54, 15, 20, 20))
    pygame.draw.rect(surf, (255, 0, 0), (58, 20, 12, 6)) # Visor
    # Arms (Cannons)
    pygame.draw.rect(surf, (30, 30, 30), (10, 40, 20, 40))
    pygame.draw.rect(surf, (30, 30, 30), (98, 40, 20, 40))
    pygame.image.save(surf, os.path.join(sprites_dir, "enemy_boss_3.png"))
    
    # Robotic 2: Tank (Treads + Turret)
    surf = pygame.Surface((128, 128), pygame.SRCALPHA)
    # Treads
    pygame.draw.rect(surf, (30, 30, 30), (20, 20, 20, 88)) # L
    pygame.draw.rect(surf, (30, 30, 30), (88, 20, 20, 88)) # R
    # Main Body
    pygame.draw.rect(surf, (60, 70, 50), (40, 30, 48, 68))
    # Turret
    pygame.draw.circle(surf, (50, 60, 40), (64, 64), 30)
    pygame.draw.rect(surf, (20, 20, 20), (60, 10, 8, 54)) # Barrel
    pygame.image.save(surf, os.path.join(sprites_dir, "enemy_boss_4.png"))
    
    # Robotic 3: Spider (Multi-legged)
    surf = pygame.Surface((128, 128), pygame.SRCALPHA)
    cx, cy = 64, 64
    # Legs
    for i in range(8):
        angle = math.radians(i * (360/8))
        ex = cx + math.cos(angle) * 55
        ey = cy + math.sin(angle) * 55
        pygame.draw.line(surf, (80, 80, 80), (cx, cy), (ex, ey), 4)
        # Joints
        mx = cx + math.cos(angle) * 30
        my = cy + math.sin(angle) * 30
        pygame.draw.circle(surf, (100, 100, 100), (int(mx), int(my)), 5)
    # Body
    pygame.draw.circle(surf, (40, 40, 40), (cx, cy), 25)
    pygame.draw.circle(surf, (255, 0, 0), (cx, cy-10), 4) # Eyes
    pygame.draw.circle(surf, (255, 0, 0), (cx-8, cy-5), 3)
    pygame.draw.circle(surf, (255, 0, 0), (cx+8, cy-5), 3)
    pygame.image.save(surf, os.path.join(sprites_dir, "enemy_boss_5.png"))
    
    # Default boss
    surf = pygame.Surface((128, 128), pygame.SRCALPHA)
    pygame.draw.circle(surf, (255, 215, 0), (64, 64), 50)
    pygame.image.save(surf, os.path.join(sprites_dir, "enemy_boss.png"))

if __name__ == "__main__":
    generate_enemy_sprites()

if __name__ == "__main__":
    generate_enemy_sprites()
