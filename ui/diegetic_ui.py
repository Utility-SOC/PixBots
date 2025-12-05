import pygame
import random
import math

class DiegeticUI:
    """Helper class for drawing holographic/diegetic UI elements."""
    
    # Colors
    HOLO_GREEN = (100, 255, 100) # Brighter
    HOLO_GREEN_DIM = (50, 150, 50)
    HOLO_BLUE = (100, 220, 255) # Brighter
    HOLO_BLUE_DIM = (50, 120, 150)
    HOLO_RED = (255, 80, 80)
    HOLO_RED_DIM = (150, 40, 40)
    
    BG_COLOR = (5, 10, 15, 230) # More opaque background
    
    @staticmethod
    def draw_holographic_panel(screen: pygame.Surface, rect: pygame.Rect, color=HOLO_GREEN):
        """Draws a panel with glowing borders and a grid background."""
        # 1. Semi-transparent background
        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        s.fill(DiegeticUI.BG_COLOR)
        screen.blit(s, (rect.x, rect.y))
        
        # 2. Grid lines
        grid_size = 20
        for x in range(0, rect.width, grid_size):
            pygame.draw.line(screen, (color[0], color[1], color[2], 50), 
                             (rect.x + x, rect.y), (rect.x + x, rect.bottom), 1)
        for y in range(0, rect.height, grid_size):
            pygame.draw.line(screen, (color[0], color[1], color[2], 50), 
                             (rect.x, rect.y + y), (rect.right, rect.y + y), 1)
                             
        # 3. Glowing Border
        # Outer glow
        pygame.draw.rect(screen, color, rect, 2)
        # Inner thin line
        pygame.draw.rect(screen, (color[0]//2, color[1]//2, color[2]//2), rect.inflate(-4, -4), 1)
        
        # 4. Corner Accents
        corner_len = 10
        pygame.draw.line(screen, color, rect.topleft, (rect.left + corner_len, rect.top), 3)
        pygame.draw.line(screen, color, rect.topleft, (rect.left, rect.top + corner_len), 3)
        
        pygame.draw.line(screen, color, rect.topright, (rect.right - corner_len, rect.top), 3)
        pygame.draw.line(screen, color, rect.topright, (rect.right, rect.top + corner_len), 3)
        
        pygame.draw.line(screen, color, rect.bottomleft, (rect.left + corner_len, rect.bottom), 3)
        pygame.draw.line(screen, color, rect.bottomleft, (rect.left, rect.bottom - corner_len), 3)
        
        pygame.draw.line(screen, color, rect.bottomright, (rect.right - corner_len, rect.bottom), 3)
        pygame.draw.line(screen, color, rect.bottomright, (rect.right, rect.bottom - corner_len), 3)

    @staticmethod
    def draw_holographic_button(screen: pygame.Surface, rect: pygame.Rect, text: str, font, is_hovered: bool, color=HOLO_GREEN):
        """Draws an interactive holographic button."""
        
        # Hover effect: Brighter background, pulsing text
        if is_hovered:
            bg_color = (color[0], color[1], color[2], 80)
            text_color = (255, 255, 255)
            border_width = 3
        else:
            bg_color = (color[0], color[1], color[2], 30)
            text_color = color
            border_width = 1
            
        # Draw Background
        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        s.fill(bg_color)
        screen.blit(s, (rect.x, rect.y))
        
        # Draw Border
        pygame.draw.rect(screen, color, rect, border_width)
        
        # Draw Text
        text_surf = font.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)
        
        # Scanline effect on button
        if is_hovered:
            y = rect.y + int((pygame.time.get_ticks() / 10) % rect.height)
            pygame.draw.line(screen, (255, 255, 255, 100), (rect.left, y), (rect.right, y), 1)

    @staticmethod
    def draw_scanlines(screen: pygame.Surface):
        """Draws subtle scanlines over the entire screen."""
        height = screen.get_height()
        width = screen.get_width()
        
        # Create a surface for scanlines
        s = pygame.Surface((width, height), pygame.SRCALPHA)
        
        for y in range(0, height, 4):
            pygame.draw.line(s, (0, 0, 0, 50), (0, y), (width, y), 1)
            
        screen.blit(s, (0, 0))
