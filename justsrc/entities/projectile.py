import pygame
import math
import constants

class Projectile:
    def __init__(self, x, y, angle, speed, damage, damage_type, owner):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.damage = damage
        self.damage_type = damage_type
        self.owner = owner  # "player" or "enemy"
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
        
        # Simple circle for now
        screen_x = int(self.x + camera_x)
        screen_y = int(self.y + camera_y)
        
        color = (255, 255, 0) if self.owner == "player" else (255, 0, 0)
        pygame.draw.circle(screen, color, (screen_x, screen_y), 4)
