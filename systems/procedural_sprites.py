# pixbots_enhanced/systems/procedural_sprites.py
# Source: Version 2's complete_procedural_sprite_generator.py
# Description: Generates unique, themed sprites for bots, weapons, and parts.

import pygame
import random
import math

class ProceduralSpriteGenerator:
    def __init__(self, seed=None):
        if seed: random.seed(seed)
        self.base_size = 256
        self.palettes = {
            "tech_blue": {"primary": (50, 70, 140), "accent": (100, 140, 240)},
            "military_green": {"primary": (70, 90, 50), "accent": (120, 140, 100)},
        }

    def generate_bot_sprite(self, bot_name: str, palette_name: str, seed: int = None) -> pygame.Surface:
        if seed: random.seed(seed)
        surface = pygame.Surface((self.base_size, self.base_size), pygame.SRCALPHA)
        palette = self.palettes.get(palette_name, self.palettes["tech_blue"])
        
        # Draw a simple shape for the body
        center_x, center_y = self.base_size // 2, self.base_size // 2
        body_size = random.randint(80, 120)
        body_rect = pygame.Rect(center_x - body_size//2, center_y - body_size//2, body_size, body_size)
        pygame.draw.rect(surface, palette["primary"], body_rect)
        
        # Add some details
        for _ in range(3):
            detail_size = random.randint(10, 30)
            detail_x = center_x + random.randint(-40, 40)
            detail_y = center_y + random.randint(-40, 40)
            detail_rect = pygame.Rect(detail_x - detail_size//2, detail_y - detail_size//2, detail_size, detail_size)
            pygame.draw.rect(surface, palette["accent"], detail_rect)
            
        return surface