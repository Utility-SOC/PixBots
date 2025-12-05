import pygame
import math
import constants

class Vortex:
    def __init__(self, x, y, radius, strength, duration, owner):
        self.x = x
        self.y = y
        self.radius = radius
        self.strength = strength  # Positive pulls, negative pushes (Explosion)
        self.duration = duration
        self.owner = owner
        self.active = True
        self.animation_timer = 0.0

    def update(self, dt):
        self.duration -= dt
        self.animation_timer += dt
        if self.duration <= 0:
            self.active = False

    def render(self, screen, camera_x, camera_y):
        if not self.active:
            return

        screen_x = int(self.x + camera_x)
        screen_y = int(self.y + camera_y)
        
        # Visual effect: Rotating spiral or expanding ring
        # For now, simple concentric circles
        
        alpha = int(255 * (self.duration / 2.0)) if self.duration < 2.0 else 255
        alpha = max(0, min(255, alpha))
        
        color = (150, 50, 200, alpha) if self.strength > 0 else (255, 100, 50, alpha)
        
        # Create a surface for transparency
        surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        
        # Draw base circle
        pygame.draw.circle(surf, (*color[:3], 50), (self.radius, self.radius), self.radius)
        
        # Draw animating rings
        ring_radius = (self.animation_timer * 50) % self.radius
        pygame.draw.circle(surf, (*color[:3], 150), (self.radius, self.radius), int(ring_radius), 2)
        
        screen.blit(surf, (screen_x - self.radius, screen_y - self.radius))
