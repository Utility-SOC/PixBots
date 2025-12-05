import pygame
import os

pygame.init()

# Check existing image size if possible
path = r"g:\work\pixelbots\assets\sprites\bots\enemy_bot.png"
if os.path.exists(path):
    try:
        img = pygame.image.load(path)
        print(f"Current image size: {img.get_size()}")
    except:
        print("Could not load existing image.")

# Create new 32x32 surface with alpha
surface = pygame.Surface((32, 32), pygame.SRCALPHA)

# Draw a menacing robot
# Colors
DARK_GREY = (50, 50, 50)
RED = (200, 0, 0)
GLOW_RED = (255, 50, 50)
BLACK = (0, 0, 0)

# Body
pygame.draw.rect(surface, DARK_GREY, (8, 8, 16, 14)) # Torso
pygame.draw.rect(surface, RED, (11, 11, 10, 8)) # Chest plate

# Head
pygame.draw.rect(surface, DARK_GREY, (10, 1, 12, 7)) # Head
pygame.draw.rect(surface, GLOW_RED, (11, 3, 4, 2)) # Eye 1
pygame.draw.rect(surface, GLOW_RED, (17, 3, 4, 2)) # Eye 2

# Arms (holding weapons?)
pygame.draw.rect(surface, DARK_GREY, (3, 8, 5, 10)) # Left Arm
pygame.draw.rect(surface, DARK_GREY, (24, 8, 5, 10)) # Right Arm
pygame.draw.circle(surface, GLOW_RED, (5, 18), 2) # Weapon glow L
pygame.draw.circle(surface, GLOW_RED, (26, 18), 2) # Weapon glow R

# Legs
pygame.draw.rect(surface, DARK_GREY, (9, 22, 5, 10)) # Left Leg
pygame.draw.rect(surface, DARK_GREY, (18, 22, 5, 10)) # Right Leg

# Save
pygame.image.save(surface, path)
print(f"Saved new 32x32 sprite to {path}")
