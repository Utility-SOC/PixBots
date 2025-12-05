# pixbots_enhanced/systems/effects.py
# Source: Version 2's effects.py
# Description: Advanced visual effect classes with support for dynamic zoom.

import pygame
import random
import math
import time
import logging
import constants

logger = logging.getLogger(__name__)

class Effect:
    """Base class for all temporary visual effects."""
    def __init__(self, duration):
        self.duration = max(0.01, duration)
        self.start_time = time.time()
        self.expired = False

    def is_expired(self):
        if not self.expired:
            self.expired = time.time() - self.start_time > self.duration
        return self.expired

    def update(self, dt):
        pass

    def render(self, screen, offset_x, offset_y, display_tile_size, asset_manager=None):
        pass

class SparkleEffect(Effect):
    """A simple sparkle effect."""
    def __init__(self, x, y, color, duration=0.5, num_sparkles=5):
        super().__init__(duration)
        self.x, self.y = x, y
        self.color = color
        self.sparkles = [{'offset': (random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)),
                          'size': random.randint(2, 5)} for _ in range(num_sparkles)]

    def render(self, screen, offset_x, offset_y, display_tile_size, asset_manager=None):
        if self.is_expired(): return
        elapsed = time.time() - self.start_time
        alpha = int(255 * (1.0 - (elapsed / self.duration)))
        if alpha <= 0: return

        for sparkle in self.sparkles:
            px = int((self.x + sparkle['offset'][0]) * display_tile_size + offset_x)
            py = int((self.y + sparkle['offset'][1]) * display_tile_size + offset_y)
            final_color = (*self.color[:3], alpha)
            pygame.draw.circle(screen, final_color, (px, py), sparkle['size'])

# --- Factory Function ---
def create_effect(effect_type, **kwargs):
    try:
        if effect_type == "sparkle":
            return SparkleEffect(**kwargs)
        logger.warning(f"Unknown effect type requested: {effect_type}")
        return None
    except Exception as e:
        logger.error(f"Error creating effect '{effect_type}': {e}", exc_info=True)
        return None