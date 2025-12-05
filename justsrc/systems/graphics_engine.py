import pygame
import math
import random
import constants

class ProceduralGenerator:
    """Generates procedural graphics for the game."""
    
    RARITY_COLORS = {
        "Common": (100, 100, 100),
        "Uncommon": (50, 200, 50),
        "Rare": (50, 50, 200),
        "Epic": (150, 50, 200),
        "Legendary": (255, 165, 0)
    }

    @staticmethod
    def generate_hex_background(item_type: str, rarity: str, size: int = 64) -> pygame.Surface:
        """Generates a background for a hex item based on type and rarity."""
        
        # Try to use VisualCompositor for weapons
        if item_type == "weapon":
            try:
                from systems.visual_compositor import VisualCompositor
                
                compositor = VisualCompositor(None) 
                
                color = ProceduralGenerator.RARITY_COLORS.get(rarity, (100, 100, 100))
                
                # Simple mapping for demo
                barrel = "basic_barrel"
                body = "basic_body"
                stock = "basic_stock"
                
                if rarity in ["Rare", "Epic", "Legendary"]:
                    body = "tech_body"
                    barrel = "sniper_barrel"
                
                img = compositor.compose_weapon(barrel, body, stock, color)
                
                # Scale to fit hex
                scaled = pygame.transform.scale(img, (size - 10, size // 2))
                
                # Create background
                surface = pygame.Surface((size, size), pygame.SRCALPHA)
                
                base_color = ProceduralGenerator.RARITY_COLORS.get(rarity, (100, 100, 100))
                cx, cy = size / 2, size / 2
                radius = size / 2 - 2
                points = []
                for i in range(6):
                    angle_deg = 60 * i - 30 
                    angle_rad = math.radians(angle_deg)
                    x = cx + radius * math.cos(angle_rad)
                    y = cy + radius * math.sin(angle_rad)
                    points.append((x, y))
                
                fill_color = (*base_color, 50) # Lower alpha for background
                pygame.draw.polygon(surface, fill_color, points)
                pygame.draw.polygon(surface, base_color, points, 2)
                
                # Blit weapon on top
                w_rect = scaled.get_rect(center=(cx, cy))
                surface.blit(scaled, w_rect)
                
                return surface
                
            except Exception as e:
                print(f"VisualCompositor failed: {e}")
                pass

        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        
        base_color = ProceduralGenerator.RARITY_COLORS.get(rarity, (100, 100, 100))
        
        # Draw Hexagon shape
        # Center is size/2, size/2
        cx, cy = size / 2, size / 2
        radius = size / 2 - 2
        
        points = []
        for i in range(6):
            angle_deg = 60 * i - 30 # Start at -30 to have flat top/bottom? Or point up?
            # Hexagon usually flat topped or pointy. Let's do pointy top.
            angle_rad = math.radians(angle_deg)
            x = cx + radius * math.cos(angle_rad)
            y = cy + radius * math.sin(angle_rad)
            points.append((x, y))
            
        # Fill with semi-transparent base color
        fill_color = (*base_color, 100) # Alpha 100
        pygame.draw.polygon(surface, fill_color, points)
        
        # Border
        pygame.draw.polygon(surface, base_color, points, 2)
        
        # Inner pattern based on type
        if item_type == "weapon":
            # Crosshairs
            pygame.draw.line(surface, (255, 255, 255), (cx - 10, cy), (cx + 10, cy), 1)
            pygame.draw.line(surface, (255, 255, 255), (cx, cy - 10), (cx, cy + 10), 1)
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 8, 1)
        elif item_type == "shield":
            # Inner shield shape
            pygame.draw.rect(surface, (255, 255, 255), (cx - 8, cy - 8, 16, 16), 1)
        elif item_type == "utility":
            # Cog/Gear approximation (circle with dots)
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 10, 1)
            for i in range(0, 360, 45):
                rad = math.radians(i)
                dx = math.cos(rad) * 12
                dy = math.sin(rad) * 12
                pygame.draw.circle(surface, (255, 255, 255), (cx + dx, cy + dy), 2)

        return surface

    @staticmethod
    def tint_surface(surface: pygame.Surface, color: tuple) -> pygame.Surface:
        """Tints a surface with a color."""
        tinted = surface.copy()
        tinted.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT) # Reset alpha? No.
        # Simple tint: fill with color using MULT
        tinted.fill(color[0:3] + (255,), special_flags=pygame.BLEND_RGBA_MULT)
        return tinted
