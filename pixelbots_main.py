# Importing the Pygame library
import pygame

# Initialize Pygame
pygame.init()

# Constants for screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600

# Create the game screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Set the title and icon (icon is optional)
pygame.display.set_caption("Voxel-like Robot Game")
# Uncomment the following line if you have an icon image
# pygame.display.set_icon(your_icon_image)

# Main game loop
running = True
while running:
    # Event loop to catch various events like keypress, mouse movement, etc.
    for event in pygame.event.get():
        # Close the window if the close button is pressed
        if event.type == pygame.QUIT:
            running = False

    # Filling the screen with a color (R, G, B)
    screen.fill((0, 0, 0))

    # Updating the screen
    pygame.display.update()

# Clean up
pygame.quit()
