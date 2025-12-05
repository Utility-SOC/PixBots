import pygame
import os

def create_placeholder(path, width, height, color, shape="rect"):
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    if shape == "rect":
        pygame.draw.rect(surface, color, (0, 0, width, height))
        pygame.draw.rect(surface, (0,0,0), (0, 0, width, height), 2) # Border
    elif shape == "circle":
        pygame.draw.circle(surface, color, (width//2, height//2), min(width, height)//2)
        pygame.draw.circle(surface, (0,0,0), (width//2, height//2), min(width, height)//2, 2)
        
    # Ensure directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pygame.image.save(surface, path)
    print(f"Created {path}")

def main():
    pygame.init()
    
    # Barrels
    create_placeholder("assets/parts/barrel_basic.png", 20, 6, (150, 150, 150))
    create_placeholder("assets/parts/barrel_sniper.png", 40, 4, (100, 100, 100))
    create_placeholder("assets/parts/barrel_scatter.png", 15, 10, (120, 120, 120))
    
    # Bodies
    create_placeholder("assets/parts/body_basic.png", 20, 12, (100, 100, 150))
    create_placeholder("assets/parts/body_tech.png", 24, 14, (100, 150, 200))
    
    # Stocks
    create_placeholder("assets/parts/stock_basic.png", 10, 8, (100, 80, 50))
    create_placeholder("assets/parts/stock_heavy.png", 12, 10, (80, 60, 40))

if __name__ == "__main__":
    main()
