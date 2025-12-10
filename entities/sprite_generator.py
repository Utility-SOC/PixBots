import pygame
import random
import math

class ProceduralBotGenerator:
    def __init__(self):
        pass

    def _draw_ngon(self, surface, color, center, radius, n, width=0, angle_offset=0):
        points = []
        for i in range(n):
            angle = math.radians(i * (360/n) - 90 + angle_offset)
            x = center[0] + math.cos(angle) * radius
            y = center[1] + math.sin(angle) * radius
            points.append((x, y))
        pygame.draw.polygon(surface, color, points, width)

    def _get_random_color(self, rng, theme="military"):
        if theme == "military":
            return (rng.randint(50, 100), rng.randint(80, 120), rng.randint(40, 80))
        elif theme == "scifi":
            return (rng.randint(200, 255), rng.randint(200, 255), rng.randint(200, 255))
        elif theme == "infernal":
            return (rng.randint(150, 255), rng.randint(0, 50), rng.randint(0, 50))
        elif theme == "void":
            return (rng.randint(20, 50), rng.randint(0, 20), rng.randint(50, 100))
        elif theme == "industrial":
            val = rng.randint(100, 180)
            return (val, val, val)
        elif theme == "neon":
            # High saturation colors
            return (rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))
        return (rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))

    def generate_grunt(self, seed=None):
        rng = random.Random(seed) if seed is not None else random.Random()
        
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        
        # Chassis
        width = rng.randint(14, 20)
        length = rng.randint(14, 20)
        
        # Color Theme
        theme = rng.choice(["military", "industrial", "scifi"])
        body_color = self._get_random_color(rng, theme)
        detail_color = (max(0, body_color[0]-40), max(0, body_color[1]-40), max(0, body_color[2]-40))
        
        # Tracks/Legs
        move_type = rng.choice(["tracks", "legs", "hover"])
        if move_type == "tracks":
            pygame.draw.rect(surf, (30, 30, 30), (16-width//2-2, 16-length//2, 2, length))
            pygame.draw.rect(surf, (30, 30, 30), (16+width//2, 16-length//2, 2, length))
        elif move_type == "legs":
            for i in range(4):
                angle = math.radians(45 + i*90)
                ex = 16 + math.cos(angle) * (width/1.5)
                ey = 16 + math.sin(angle) * (length/1.5)
                pygame.draw.line(surf, (50, 50, 50), (16, 16), (ex, ey), 2)
        
        # Main Body
        shape = rng.choice(["rect", "circle", "hex"])
        if shape == "rect":
            pygame.draw.rect(surf, body_color, (16-width//2, 16-length//2, width, length))
            pygame.draw.rect(surf, detail_color, (16-width//2, 16-length//2, width, length), 1)
        elif shape == "circle":
            pygame.draw.circle(surf, body_color, (16, 16), width//2)
            pygame.draw.circle(surf, detail_color, (16, 16), width//2, 1)
        elif shape == "hex":
            self._draw_ngon(surf, body_color, (16, 16), width//2, 6)
            self._draw_ngon(surf, detail_color, (16, 16), width//2, 6, 1)

        # Turret/Head
        turret_color = self._get_random_color(rng, theme)
        pygame.draw.circle(surf, turret_color, (16, 16), rng.randint(4, 8))
        
        # Gun
        gun_len = rng.randint(6, 12)
        pygame.draw.line(surf, (20, 20, 20), (16, 16), (16, 16-gun_len), 3)
            
        return surf, None

    def generate_sniper(self, seed=None):
        rng = random.Random(seed) if seed is not None else random.Random()
        
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        
        # Triangular / Sharp shapes
        body_color = self._get_random_color(rng, "military")
        if rng.random() < 0.3: body_color = self._get_random_color(rng, "void") # Rare void sniper
        
        points = [(16, 2), (28, 28), (4, 28)]
        pygame.draw.polygon(surf, body_color, points)
        pygame.draw.polygon(surf, (0, 0, 0), points, 1)
        
        # Long Barrel
        pygame.draw.line(surf, (10, 10, 10), (16, 10), (16, 2), 2)
        
        # Scope
        pygame.draw.circle(surf, (255, 0, 0), (16, 14), 2)
        
        # Camo pattern (simple lines)
        for _ in range(3):
            p1 = (rng.randint(8, 24), rng.randint(10, 26))
            p2 = (p1[0] + rng.randint(-4, 4), p1[1] + rng.randint(-4, 4))
            pygame.draw.line(surf, (30, 40, 20), p1, p2, 1)
            
        return surf

    def generate_ambusher(self, biome="forest", seed=None):
        rng = random.Random(seed) if seed is not None else random.Random()
        
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        
        # Ghillie / Organic look
        # Base color depends on biome
        if biome == "forest": base = (34, 139, 34)
        elif biome == "desert": base = (210, 180, 140)
        elif biome == "ice": base = (200, 240, 255)
        else: base = (100, 100, 100)
        
        # Jittery circle for organic feel
        center = (16, 16)
        points = []
        for i in range(0, 360, 20):
            r = rng.randint(10, 14)
            angle = math.radians(i)
            x = center[0] + math.cos(angle) * r
            y = center[1] + math.sin(angle) * r
            points.append((x, y))
            
        pygame.draw.polygon(surf, base, points)
        
        # "Leaves" or texture
        for _ in range(10):
            lx = rng.randint(4, 28)
            ly = rng.randint(4, 28)
            c = (max(0, base[0]-20), max(0, base[1]-20), max(0, base[2]-20))
            pygame.draw.circle(surf, c, (lx, ly), 2)
            
        # Hidden Eye
        pygame.draw.circle(surf, (255, 255, 0), (16, 16), 3)
        
        return surf

    def _generate_mech_boss(self, rng):
        surf = pygame.Surface((192, 192), pygame.SRCALPHA)
        cx, cy = 96, 96
        
        # Theme & Colors
        theme = rng.choice(["military", "industrial", "scifi", "void", "neon", "infernal"])
        primary = self._get_random_color(rng, theme)
        secondary = self._get_random_color(rng, theme)
        dark = (max(0, primary[0]-50), max(0, primary[1]-50), max(0, primary[2]-50))
        
        # 1. Legs / Chassis
        leg_type = rng.choice(["biped", "quad", "treads", "hover"])
        if leg_type == "biped":
            # Two large legs
            pygame.draw.rect(surf, dark, (cx-30, cy+10, 20, 40))
            pygame.draw.rect(surf, dark, (cx+10, cy+10, 20, 40))
            pygame.draw.rect(surf, secondary, (cx-32, cy+40, 24, 10)) # Feet
            pygame.draw.rect(surf, secondary, (cx+8, cy+40, 24, 10))
        elif leg_type == "quad":
            # Four spider-like legs
            for i in range(4):
                angle = math.radians(45 + i*90)
                ex = cx + math.cos(angle) * 50
                ey = cy + math.sin(angle) * 50
                pygame.draw.line(surf, dark, (cx, cy), (ex, ey), 8)
                pygame.draw.circle(surf, secondary, (int(ex), int(ey)), 10)
        elif leg_type == "treads":
            # Tank treads
            pygame.draw.rect(surf, (40, 40, 40), (cx-40, cy-40, 20, 80))
            pygame.draw.rect(surf, (40, 40, 40), (cx+20, cy-40, 20, 80))
            # Tread details
            for i in range(0, 80, 10):
                pygame.draw.line(surf, (20, 20, 20), (cx-40, cy-40+i), (cx-20, cy-40+i), 2)
                pygame.draw.line(surf, (20, 20, 20), (cx+20, cy-40+i), (cx+40, cy-40+i), 2)
        elif leg_type == "hover":
            # Hover skirt
            pygame.draw.circle(surf, (30, 30, 30), (cx, cy), 50)
            pygame.draw.circle(surf, (0, 200, 255), (cx, cy), 45, 2)
            
        # 2. Torso
        torso_shape = rng.choice(["block", "round", "hex"])
        if torso_shape == "block":
            pygame.draw.rect(surf, primary, (cx-25, cy-30, 50, 60))
            pygame.draw.rect(surf, secondary, (cx-25, cy-30, 50, 60), 4)
            # Chest vents
            pygame.draw.line(surf, (20, 20, 20), (cx-15, cy-10), (cx+15, cy-10), 2)
            pygame.draw.line(surf, (20, 20, 20), (cx-15, cy), (cx+15, cy), 2)
        elif torso_shape == "round":
            pygame.draw.circle(surf, primary, (cx, cy), 35)
            pygame.draw.circle(surf, secondary, (cx, cy), 35, 4)
        elif torso_shape == "hex":
            self._draw_ngon(surf, primary, (cx, cy), 35, 6)
            self._draw_ngon(surf, secondary, (cx, cy), 35, 6, 4)

        # 3. Head
        head_type = rng.choice(["cockpit", "sensor", "dome"])
        hy = cy - 15 # Default head y
        if torso_shape == "block": hy = cy - 40
        
        if head_type == "cockpit":
            pygame.draw.rect(surf, secondary, (cx-10, hy-10, 20, 20))
            pygame.draw.rect(surf, (0, 255, 255), (cx-8, hy-8, 16, 10)) # Glass
        elif head_type == "sensor":
            pygame.draw.rect(surf, secondary, (cx-12, hy-8, 24, 16))
            pygame.draw.circle(surf, (255, 0, 0), (cx, hy), 5) # Red eye
        elif head_type == "dome":
            pygame.draw.circle(surf, secondary, (cx, hy), 12)
            pygame.draw.arc(surf, (255, 255, 255), (cx-10, hy-10, 20, 20), 0, 3.14, 2)

        # 4. Arms / Weapons
        weapons = []
        
        # Left Arm
        pygame.draw.circle(surf, dark, (cx-35, cy-10), 10) # Shoulder
        l_weapon = rng.choice(["gun", "claw", "missile"])
        if l_weapon == "gun":
            pygame.draw.rect(surf, (50, 50, 50), (cx-55, cy-5, 20, 10)) # Arm
            pygame.draw.rect(surf, (20, 20, 20), (cx-65, cy-8, 10, 16)) # Muzzle
            weapons.append({"type": "gun", "damage": 15, "speed": 400, "cooldown": 0.5, "synergy": "kinetic"})
        elif l_weapon == "claw":
            pygame.draw.line(surf, secondary, (cx-35, cy-10), (cx-55, cy+10), 6)
            pygame.draw.line(surf, (200, 200, 200), (cx-55, cy+10), (cx-60, cy+20), 3)
            pygame.draw.line(surf, (200, 200, 200), (cx-55, cy+10), (cx-50, cy+20), 3)
            weapons.append({"type": "claw", "damage": 40, "speed": 0, "cooldown": 1.5, "synergy": "kinetic"}) # Melee?
        elif l_weapon == "missile":
            pygame.draw.rect(surf, secondary, (cx-60, cy-20, 25, 20))
            for i in range(3):
                pygame.draw.circle(surf, (255, 255, 255), (cx-55+i*8, cy-10), 3)
            weapons.append({"type": "missile", "damage": 30, "speed": 200, "cooldown": 3.0, "synergy": "explosion"})

        # Right Arm
        pygame.draw.circle(surf, dark, (cx+35, cy-10), 10) # Shoulder
        r_weapon = rng.choice(["gun", "claw", "missile"])
        if r_weapon == "gun":
            pygame.draw.rect(surf, (50, 50, 50), (cx+35, cy-5, 20, 10))
            pygame.draw.rect(surf, (20, 20, 20), (cx+55, cy-8, 10, 16))
            weapons.append({"type": "gun", "damage": 15, "speed": 400, "cooldown": 0.5, "synergy": "kinetic"})
        elif r_weapon == "claw":
            pygame.draw.line(surf, secondary, (cx+35, cy-10), (cx+55, cy+10), 6)
            pygame.draw.line(surf, (200, 200, 200), (cx+55, cy+10), (cx+60, cy+20), 3)
            pygame.draw.line(surf, (200, 200, 200), (cx+55, cy+10), (cx+50, cy+20), 3)
            weapons.append({"type": "claw", "damage": 40, "speed": 0, "cooldown": 1.5, "synergy": "kinetic"})
        elif r_weapon == "missile":
            pygame.draw.rect(surf, secondary, (cx+35, cy-20, 25, 20))
            for i in range(3):
                pygame.draw.circle(surf, (255, 255, 255), (cx+40+i*8, cy-10), 3)
            weapons.append({"type": "missile", "damage": 30, "speed": 200, "cooldown": 3.0, "synergy": "explosion"})

        return surf, {"weapons": weapons}

    def generate_boss(self, seed=None):
        rng = random.Random(seed) if seed is not None else random.Random()
        
        # 70% Chance for Mech Boss (Robot Shaped)
        if rng.random() < 0.7:
            return self._generate_mech_boss(rng)
            
        # 30% Chance for Abstract/Construct Boss (Original Style)
        surf = pygame.Surface((192, 192), pygame.SRCALPHA)
        cx, cy = 96, 96
        
        # 1. Theme Selection
        theme = rng.choice(["scifi", "void", "infernal", "industrial"])
        primary_color = self._get_random_color(rng, theme)
        secondary_color = self._get_random_color(rng, theme)
        
        # 2. Body Shape Composition
        shape_type = rng.choice(["circle", "square", "hex", "star", "complex"])
        radius = rng.randint(40, 55)
        
        if shape_type == "circle":
            pygame.draw.circle(surf, primary_color, (cx, cy), radius)
            pygame.draw.circle(surf, secondary_color, (cx, cy), radius, 4)
        elif shape_type == "square":
            rect = (cx-radius, cy-radius, radius*2, radius*2)
            pygame.draw.rect(surf, primary_color, rect)
            pygame.draw.rect(surf, secondary_color, rect, 4)
        elif shape_type == "hex":
            self._draw_ngon(surf, primary_color, (cx, cy), radius, 6)
            self._draw_ngon(surf, secondary_color, (cx, cy), radius, 6, 4)
        elif shape_type == "star":
            self._draw_ngon(surf, primary_color, (cx, cy), radius, 5)
            self._draw_ngon(surf, secondary_color, (cx, cy), radius, 5, 2)
            # Inner star
            self._draw_ngon(surf, secondary_color, (cx, cy), radius*0.6, 5, 0, 36)
        elif shape_type == "complex":
            # Overlapping shapes
            self._draw_ngon(surf, primary_color, (cx, cy), radius, 8)
            pygame.draw.circle(surf, secondary_color, (cx, cy), radius*0.7)
            self._draw_ngon(surf, primary_color, (cx, cy), radius*0.4, 4)

        # 3. Attachments / Turrets
        num_hardpoints = rng.randint(2, 6)
        for i in range(num_hardpoints):
            angle = math.radians(i * (360/num_hardpoints))
            dist = radius * rng.uniform(0.8, 1.2)
            ax = cx + math.cos(angle) * dist
            ay = cy + math.sin(angle) * dist
            
            # Weapon pod
            pod_size = rng.randint(8, 15)
            pygame.draw.circle(surf, (50, 50, 50), (ax, ay), pod_size)
            pygame.draw.circle(surf, secondary_color, (ax, ay), pod_size-2)
            
            # Barrel
            bx = ax + math.cos(angle) * (pod_size + 5)
            by = ay + math.sin(angle) * (pod_size + 5)
            pygame.draw.line(surf, (20, 20, 20), (ax, ay), (bx, by), 4)

        # 4. Core / Eye
        core_type = rng.choice(["eye", "reactor", "void_hole"])
        if core_type == "eye":
            pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 15)
            pygame.draw.circle(surf, (255, 0, 0), (cx, cy), 8) # Pupil
        elif core_type == "reactor":
            pygame.draw.circle(surf, (0, 255, 255), (cx, cy), 12)
            for i in range(3):
                pygame.draw.arc(surf, (255, 255, 255), (cx-12, cy-12, 24, 24), i*2, i*2+1, 2)
        elif core_type == "void_hole":
            pygame.draw.circle(surf, (0, 0, 0), (cx, cy), 18)
            pygame.draw.circle(surf, (100, 0, 100), (cx, cy), 18, 2)

        # 5. Surface Details
        if rng.random() < 0.5:
            # Stripes
            for i in range(-2, 3):
                pygame.draw.line(surf, secondary_color, (cx-20, cy+i*10), (cx+20, cy+i*10), 2)
        
        # Construct Boss Weapons (Abstract)
        weapons = []
        # Main weapon
        weapons.append({"type": "main_cannon", "damage": 20, "speed": 300, "cooldown": 1.0, "synergy": rng.choice(["fire", "ice", "vortex"])})
        # Secondary
        if rng.random() < 0.5:
             weapons.append({"type": "turret", "damage": 10, "speed": 400, "cooldown": 0.5, "synergy": "kinetic"})
        
        return surf, {"weapons": weapons}
