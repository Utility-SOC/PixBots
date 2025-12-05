# pixbots_enhanced/entities/sprite_generator.py
# Source: Extracted from your pixbots_game.py
# Description: Generates unique, procedural robot sprites.

import pygame
import random

def generate_robot_sprite(bot_name: str, size: int = 32) -> pygame.Surface:
    """
    Generates a placeholder pixel-art sprite (16x16 pixels, mirrored for symmetry)
    and scales it up. The sprite is deterministic based on the bot's name.
    """
    width = height = 16
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Use the bot's name to seed the random number generator for deterministic sprites
    rng = random.Random(bot_name)
    
    # Choose a primary color based on the name hash
    hue = abs(hash(bot_name))
    primary_color = pygame.Color(0)
    # Use high saturation and value for vibrant colors
    primary_color.hsva = (hue % 360, 85, 95, 100)
    
    # Create a simple palette from the primary color
    colors = [
        primary_color,
        (primary_color.r // 2, primary_color.g // 2, primary_color.b // 2), # Darker shade for outlines/details
        (min(255, primary_color.r + 60), min(255, primary_color.g + 60), min(255, primary_color.b + 60)) # Lighter shade for highlights
    ]

    # Draw random symmetric pixels to create a robot-like shape
    for y in range(height):
        for x in range(width // 2):
            # Higher chance of pixels in the center and lower down to form a 'body'
            chance = 0.6 - (y / height * 0.4)
            if rng.random() < chance:
                color = rng.choice(colors)
                surface.set_at((x, y), color)
                surface.set_at((width - 1 - x, y), color) # Mirror horizontally

    # Scale the small sprite for visibility, using nearest-neighbor for a crisp pixel look
    sprite_img = pygame.transform.scale(surface, (size, size))
    return sprite_img

