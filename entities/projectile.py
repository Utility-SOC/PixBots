import pygame
import math
import constants

class Projectile:
    def __init__(self, x, y, angle, speed, damage, damage_type, owner, effects=None):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.damage = damage
        self.damage_type = damage_type
        self.owner = owner  # "player" or "enemy"
        self.effects = effects if effects else {} # Dictionary of effects (e.g. status_effect, aoe)
        self.pierce_count = self.effects.get("pierce", 0)
        self.hit_list = [] # List of entity IDs hit by this projectile
        self.lifetime = constants.PROJECTILE_LIFETIME
        self.active = True
        
        # Calculate velocity components
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False

    def render(self, screen, camera_x, camera_y):
        if not self.active:
            return
        
        screen_x = int(self.x + camera_x)
        screen_y = int(self.y + camera_y)
        
        # Determine active synergies
        active_synergies = self.effects.get("active_synergies", [])
        if not active_synergies and self.effects.get("synergy_name"):
            active_synergies = [self.effects.get("synergy_name")]
            
        # Default if no synergy
        if not active_synergies:
            pygame.draw.circle(screen, (255, 255, 0), (screen_x, screen_y), 4)
            return

        # Color Mapping
        colors = {
            "vortex": (180, 50, 255),    # Bright Purple
            "fire": (255, 80, 0),        # Orange-Red
            "ice": (100, 220, 255),      # Cyan
            "lightning": (200, 200, 255),# White-Blue
            "explosion": (255, 50, 50),  # Red
            "kinetic": (200, 200, 200),  # Grey
            "poison": (50, 255, 50),     # Green
            "pierce": (255, 255, 200),   # Pale Yellow
            "vampiric": (150, 0, 0)      # Blood Red
        }

        # Render Concentric Rings
        base_radius = 6 if "vortex" in active_synergies else 4
        if "explosion" in active_synergies: base_radius = 5
        
        # Ensure minimum visibility (Fix for invisible projectiles)
        # Use damage to scale, but clamp to min 4 and max 15 to avoid huge particles
        damage_radius = max(4, min(15, int(self.damage / 10)))
        base_radius = max(base_radius, damage_radius)
        
        num_synergies = len(active_synergies)
        step = base_radius / num_synergies
        
        for i, synergy in enumerate(active_synergies):
            color = colors.get(synergy, (255, 255, 255))
            if self.owner == "enemy":
                # Tint towards red for enemies
                color = (min(255, color[0] + 50), max(0, color[1] - 50), max(0, color[2] - 50))
                
            radius = base_radius - (i * step * 0.5) # Overlap slightly
            if radius < 1: radius = 1
            
            pygame.draw.circle(screen, color, (screen_x, screen_y), int(radius))
            
            # Special effects for specific synergies (only on the outer layer or specific ones)
            if synergy == "vortex" and i == 0:
                 pygame.draw.circle(screen, (100, 0, 150), (screen_x, screen_y), int(radius) + 2, 1)

        # Debug/Fallback for enemy owner if no synergies
        if self.owner == "enemy" and not active_synergies:
             pygame.draw.circle(screen, (255, 0, 0), (screen_x, screen_y), 4)
