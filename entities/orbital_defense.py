import math
from entities.projectile import Projectile
import constants

class Orbital(Projectile):
    def __init__(self, owner_entity, config, effects=None):
        # Config has: radius, speed, period (offset)
        self.owner_entity = owner_entity
        self.radius = config.get("radius", 100.0)
        self.orbit_speed = config.get("speed", 1.0)
        self.angle_offset = config.get("angle_offset", 0.0)
        
        # Calculate initial position
        x = owner_entity.x + math.cos(self.angle_offset) * self.radius
        y = owner_entity.y + math.sin(self.angle_offset) * self.radius
        
        # Initialize as Projectile
        # Speed=0 because we manage movement. Damage?
        # Damage should come from config or default or context.
        # Assuming context has damage.
        damage = config.get("damage", 10.0)
        
        super().__init__(x, y, 0, 0, damage, "energy", "player", effects)
        
        self.lifetime = 9999.0 # Effectively infinite while active
        self.current_angle = self.angle_offset
        
        # S6: Periodic Damage Logic
        self.pierce_count = 9999
        self.damage_tick_rate = 0.5 # Seconds between hits on same target
        self.tick_timer = 0.0

    def release(self):
        """Releases the projectile from orbit to fly tangentially."""
        self.active_orbit = False
        import math
        # Tangent velocity: (-sin, cos) * speed
        # Ensure we use world coordinates for vector
        # speed is atomic units, we need pixels/sec. 
        # But 'orbit_speed' is radians/sec. 1 radian * radius = arc length.
        # Linear speed = orbit_speed * radius
        linear_speed = self.orbit_speed * self.radius
        
        # Tangent angle = current_angle + 90 deg (pi/2)
        move_angle = self.current_angle + (math.pi / 2)
        
        self.vx = math.cos(move_angle) * linear_speed
        self.vy = math.sin(move_angle) * linear_speed
        
        # Increase lifetime on release as requested
        self.lifetime = 5.0 

    def update(self, dt):
        # Check if owner is alive
        if self.owner_entity.hp <= 0:
            self.active = False
            return
            
        # Manage Damage Ticks
        self.tick_timer -= dt
        if self.tick_timer <= 0:
            self.hit_list.clear() # Reset hit list to allow re-hitting enemies
            self.pierce_count = 9999 # Reset pierce count
            self.tick_timer = self.damage_tick_rate

        if getattr(self, "active_orbit", True):
            # Update Angle
            self.current_angle += self.orbit_speed * dt
            
            # Update Position relative to owner
            self.x = self.owner_entity.x + math.cos(self.current_angle) * self.radius
            self.y = self.owner_entity.y + math.sin(self.current_angle) * self.radius
            
            # We generally do NOT call super().update(dt) because it moves x,y linearly and checks lifetime.
            # We manually check lifetime if we used it (but we set it to infinite).
            # However, checking max lifetime is fine.
            self.lifetime -= dt
        else:
            # Released: Fly linearly
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.lifetime -= dt
            
        if self.lifetime <= 0:
            self.active = False

    def render(self, screen, camera_x, camera_y):
        # Override render to look like an orbital
        import pygame
        cx = self.x + camera_x
        cy = self.y + camera_y
        
        # Draw glowing orb
        color = (100, 255, 255)
        pygame.draw.circle(screen, color, (int(cx), int(cy)), 8)
        pygame.draw.circle(screen, (255, 255, 255), (int(cx), int(cy)), 4)
