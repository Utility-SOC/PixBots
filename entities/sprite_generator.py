import pygame
import random
import math

class ProceduralBotGenerator:
    def __init__(self):
        pass

    def _draw_ngon(self, surface, color, center, radius, n, width=0):
        points = []
        for i in range(n):
            angle = math.radians(i * (360/n) - 90)
            x = center[0] + math.cos(angle) * radius
            y = center[1] + math.sin(angle) * radius
            points.append((x, y))
        pygame.draw.polygon(surface, color, points, width)

    def generate_grunt(self, seed=None):
        if seed is not None: random.seed(seed)
        
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        
        # Randomize chassis dimensions
        width = random.randint(14, 18)
        length = random.randint(14, 18)
        
        # Tracks (Dark Grey)
        track_color = (50, 50, 50)
        pygame.draw.rect(surf, track_color, (16-width//2-4, 16-length//2-2, 4, length+4)) # L
        pygame.draw.rect(surf, track_color, (16+width//2, 16-length//2-2, 4, length+4)) # R
        
        # Body Color (Olive/Green variations)
        r = 85 + random.randint(-15, 15)
        g = 107 + random.randint(-15, 15)
        b = 47 + random.randint(-15, 15)
        body_color = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
        
        pygame.draw.rect(surf, body_color, (16-width//2, 16-length//2, width, length))
        pygame.draw.rect(surf, (60, 80, 20), (16-width//2, 16-length//2, width, length), 2)
        
        # Turret Shape
        turret_color = (100, 120, 60)
        turret_type = random.choice(["square", "circle", "hexagon"])
        
        if turret_type == "square":
            pygame.draw.rect(surf, turret_color, (10, 10, 12, 12))
        elif turret_type == "circle":
            pygame.draw.circle(surf, turret_color, (16, 16), 7)
        elif turret_type == "hexagon":
            self._draw_ngon(surf, turret_color, (16, 16), 7, 6)
            
        # Eye/Sensor
        eye_color = (255, 100 + random.randint(-50, 50), 0)
        pygame.draw.circle(surf, eye_color, (16, 16), 3)
        
        # Gun Placement
        gun_color = (30, 30, 30)
        gun_style = random.choice(["center", "offset_r", "offset_l", "double"])
        
        if gun_style == "center":
            pygame.draw.rect(surf, gun_color, (14, 2, 4, 10))
        elif gun_style == "offset_r":
            pygame.draw.rect(surf, gun_color, (18, 4, 3, 8))
        elif gun_style == "offset_l":
            pygame.draw.rect(surf, gun_color, (10, 4, 3, 8))
        elif gun_style == "double":
            pygame.draw.rect(surf, gun_color, (12, 2, 3, 10))
            pygame.draw.rect(surf, gun_color, (17, 2, 3, 10))
            
        return surf

    def generate_sniper(self, seed=None):
        if seed is not None: random.seed(seed)
        
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        
        # Body Shape
        shape_type = random.choice(["standard", "diamond", "narrow", "wide"])
        points = []
        if shape_type == "standard": points = [(16, 2), (28, 28), (4, 28)]
        elif shape_type == "diamond": points = [(16, 2), (30, 20), (16, 28), (2, 20)]
        elif shape_type == "narrow": points = [(16, 2), (24, 28), (8, 28)]
        elif shape_type == "wide": points = [(16, 4), (30, 30), (2, 30)]
        
        # Color (Yellow/Gold variations)
        r = 255
        g = 215 + random.randint(-40, 0)
        b = 0
        body_color = (r, g, b)
        
        pygame.draw.polygon(surf, body_color, points)
        pygame.draw.polygon(surf, (0, 0, 0), points, 2)
        
        # Markings
        marking_type = random.choice(["stripes", "target", "hazard"])
        if marking_type == "stripes":
            pygame.draw.line(surf, (0, 0, 0), (12, 12), (20, 12), 2)
            pygame.draw.line(surf, (0, 0, 0), (10, 18), (22, 18), 2)
        elif marking_type == "target":
            pygame.draw.circle(surf, (0,0,0), (16, 18), 4, 1)
            pygame.draw.line(surf, (0,0,0), (16, 14), (16, 22), 1)
            pygame.draw.line(surf, (0,0,0), (12, 18), (20, 18), 1)
        elif marking_type == "hazard":
            pygame.draw.line(surf, (0,0,0), (8, 24), (24, 24), 2)
            pygame.draw.line(surf, (0,0,0), (10, 20), (22, 20), 2)
            
        # Scope
        pygame.draw.circle(surf, (255, 0, 0), (16, 10), 3)
        
        # Barrel
        barrel_len = random.randint(10, 16)
        pygame.draw.line(surf, (50, 50, 50), (16, 10), (16, 10-barrel_len), 2)
        
        return surf

    def generate_ambusher(self, biome="forest", seed=None):
        if seed is not None: random.seed(seed)
        
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        
        biomes = {
            "forest": (34, 139, 34),
            "desert": (237, 201, 175),
            "ice": (224, 255, 255),
            "volcanic": (40, 40, 40),
            "island": (255, 255, 150),
            "mountainous": (100, 100, 100),
            "beach": (240, 230, 140),
            "meadow": (100, 200, 100)
        }
        
        base_color = biomes.get(biome, (100, 100, 100))
        
        # Shape Variation
        shape_type = random.choice(["star", "x_shape", "shuriken", "spike_ball"])
        
        points = []
        if shape_type == "star":
            points = [(16, 2), (20, 12), (30, 16), (20, 20), (16, 30), (12, 20), (2, 16), (12, 12)]
        elif shape_type == "x_shape":
            points = [(10, 4), (22, 4), (28, 10), (28, 22), (22, 28), (10, 28), (4, 22), (4, 10)]
        elif shape_type == "shuriken":
            points = [(16, 0), (24, 12), (32, 16), (24, 20), (16, 32), (8, 20), (0, 16), (8, 12)]
        elif shape_type == "spike_ball":
            self._draw_ngon(surf, base_color, (16, 16), 10, 8)
            # Add spikes
            for i in range(8):
                angle = math.radians(i * 45)
                ex = 16 + math.cos(angle) * 15
                ey = 16 + math.sin(angle) * 15
                pygame.draw.line(surf, base_color, (16, 16), (ex, ey), 3)
            points = None # Handled above
            
        if points:
            pygame.draw.polygon(surf, base_color, points)
            pygame.draw.polygon(surf, (0, 0, 0), points, 2)
            
        # Eye
        eye_color = (255, 0, 255)
        pygame.draw.circle(surf, eye_color, (16, 16), 4)
        
        return surf

    def generate_boss(self, seed=None):
        if seed is not None: random.seed(seed)
        
        surf = pygame.Surface((128, 128), pygame.SRCALPHA)
        
        boss_type = random.choice(["sun", "ramiel", "monolith", "mech", "tank", "spider"])
        
        cx, cy = 64, 64
        
        if boss_type == "sun":
            pygame.draw.circle(surf, (255, 215, 0), (cx, cy), 50)
            pygame.draw.circle(surf, (0, 0, 0), (cx, cy), 50, 4)
            pygame.draw.circle(surf, (255, 0, 0), (cx, cy), 20)
            for i in range(0, 360, 45):
                rad = math.radians(i)
                ex = cx + math.cos(rad) * 60
                ey = cy + math.sin(rad) * 60
                pygame.draw.line(surf, (255, 100, 0), (cx, cy), (ex, ey), 4)
                
        elif boss_type == "ramiel":
            points = [(cx, 14), (114, cy), (cx, 114), (14, cy)]
            pygame.draw.polygon(surf, (0, 0, 255), points)
            pygame.draw.polygon(surf, (200, 200, 255), points, 4)
            pygame.draw.circle(surf, (255, 0, 0), (cx, cy), 10)
            
        elif boss_type == "monolith":
            self._draw_ngon(surf, (20, 20, 20), (cx, cy), 50, 6)
            self._draw_ngon(surf, (0, 255, 0), (cx, cy), 50, 6, 2)
            for i in range(5):
                y = 30 + i * 15
                pygame.draw.line(surf, (0, 255, 0), (40, y), (88, y), 1)
                
        elif boss_type == "mech":
            pygame.draw.rect(surf, (50, 50, 70), (40, 70, 15, 40))
            pygame.draw.rect(surf, (50, 50, 70), (73, 70, 15, 40))
            pygame.draw.rect(surf, (70, 70, 90), (35, 30, 58, 50))
            pygame.draw.rect(surf, (100, 100, 120), (35, 30, 58, 50), 3)
            pygame.draw.circle(surf, (50, 50, 70), (30, 40), 15)
            pygame.draw.circle(surf, (50, 50, 70), (98, 40), 15)
            pygame.draw.rect(surf, (80, 80, 100), (54, 15, 20, 20))
            pygame.draw.rect(surf, (255, 0, 0), (58, 20, 12, 6))
            pygame.draw.rect(surf, (30, 30, 30), (10, 40, 20, 40))
            pygame.draw.rect(surf, (30, 30, 30), (98, 40, 20, 40))
            
        elif boss_type == "tank":
            pygame.draw.rect(surf, (30, 30, 30), (20, 20, 20, 88))
            pygame.draw.rect(surf, (30, 30, 30), (88, 20, 20, 88))
            pygame.draw.rect(surf, (60, 70, 50), (40, 30, 48, 68))
            pygame.draw.circle(surf, (50, 60, 40), (cx, cy), 30)
            pygame.draw.rect(surf, (20, 20, 20), (60, 10, 8, 54))
            
        elif boss_type == "spider":
            for i in range(8):
                angle = math.radians(i * (360/8))
                ex = cx + math.cos(angle) * 55
                ey = cy + math.sin(angle) * 55
                pygame.draw.line(surf, (80, 80, 80), (cx, cy), (ex, ey), 4)
                mx = cx + math.cos(angle) * 30
                my = cy + math.sin(angle) * 30
                pygame.draw.circle(surf, (100, 100, 100), (int(mx), int(my)), 5)
            pygame.draw.circle(surf, (40, 40, 40), (cx, cy), 25)
            pygame.draw.circle(surf, (255, 0, 0), (cx, cy-10), 4)
            pygame.draw.circle(surf, (255, 0, 0), (cx-8, cy-5), 3)
            pygame.draw.circle(surf, (255, 0, 0), (cx+8, cy-5), 3)
            
        return surf
