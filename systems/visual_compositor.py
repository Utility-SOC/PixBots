import pygame
import json
import os
from typing import Dict, Tuple, Optional

class VisualCompositor:
    """
    Composes visual assets for equipment based on parts and configuration.
    Applies SNES-style pixelation and effects.
    """
    
    def __init__(self, asset_manager):
        self.asset_manager = asset_manager
        self.parts_data = {}
        self.loaded_images = {}
        self.load_parts_data()
        
    def load_parts_data(self):
        """Loads weapon parts definition from JSON."""
        try:
            with open("data/weapon_parts.json", "r") as f:
                self.parts_data = json.load(f)
        except FileNotFoundError:
            print("Error: data/weapon_parts.json not found.")
            self.parts_data = {"barrels": {}, "bodies": {}, "stocks": {}}

    def get_image(self, path: str) -> pygame.Surface:
        """Loads and caches an image."""
        if path not in self.loaded_images:
            try:
                img = pygame.image.load(path).convert_alpha()
                self.loaded_images[path] = img
            except Exception as e:
                print(f"Failed to load image {path}: {e}")
                # Return magenta placeholder
                s = pygame.Surface((16, 16))
                s.fill((255, 0, 255))
                self.loaded_images[path] = s
        return self.loaded_images[path]

    def compose_weapon(self, barrel_id: str, body_id: str, stock_id: str, color_tint: Tuple[int, int, int] = None) -> pygame.Surface:
        """
        Composes a weapon sprite from parts.
        """
        body_def = self.parts_data["bodies"].get(body_id)
        barrel_def = self.parts_data["barrels"].get(barrel_id)
        stock_def = self.parts_data["stocks"].get(stock_id)
        
        if not body_def: return self.get_placeholder()
        
        # Base canvas size (arbitrary large enough)
        canvas = pygame.Surface((64, 32), pygame.SRCALPHA)
        
        # Calculate positions
        # Center the body roughly
        body_x, body_y = 20, 10
        
        # Draw Stock (behind body)
        if stock_def:
            stock_img = self.get_image(stock_def["image_path"])
            # Stock attaches to body's stock_mount
            # Stock's attachment_point matches body's stock_mount
            bx, by = body_def.get("stock_mount", [0, 0])
            sx, sy = stock_def.get("attachment_point", [0, 0])
            
            dest_x = body_x + bx - sx
            dest_y = body_y + by - sy
            canvas.blit(stock_img, (dest_x, dest_y))
            
        # Draw Barrel (behind body? or in front? usually in front)
        if barrel_def:
            barrel_img = self.get_image(barrel_def["image_path"])
            bx, by = body_def.get("barrel_mount", [10, 0])
            sx, sy = barrel_def.get("attachment_point", [0, 0])
            
            dest_x = body_x + bx - sx
            dest_y = body_y + by - sy
            canvas.blit(barrel_img, (dest_x, dest_y))
            
        # Draw Body
        body_img = self.get_image(body_def["image_path"])
        canvas.blit(body_img, (body_x, body_y))
        
        # Apply Tint if provided
        if color_tint:
            canvas = self.apply_tint(canvas, color_tint)
            
        # Apply SNES Pixelation Effect
        canvas = self.apply_snes_effect(canvas)
        
        return canvas

    def apply_tint(self, surface: pygame.Surface, color: Tuple[int, int, int]) -> pygame.Surface:
        """Applies a color tint to the surface."""
        tinted = surface.copy()
        # Create a color surface
        color_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        color_surf.fill((*color, 100)) # Semi-transparent tint
        
        # Blit using special flags to keep alpha
        tinted.blit(color_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return tinted

    def apply_snes_effect(self, surface: pygame.Surface) -> pygame.Surface:
        """
        Applies a pixelation/posterization effect to simulate SNES graphics.
        """
        # 1. Quantize colors (Posterize)
        # Simple approach: reduce color depth
        # This is slow in python per-pixel, so we use pygame transform if possible
        # or just leave it for now as the assets are already pixel art.
        
        # 2. Outline
        # Create a mask from the alpha channel
        mask = pygame.mask.from_surface(surface)
        outline = mask.to_surface(setcolor=(0, 0, 0, 255), unsetcolor=(0, 0, 0, 0))
        
        final = pygame.Surface((surface.get_width() + 2, surface.get_height() + 2), pygame.SRCALPHA)
        
        # Draw outline shifted in 4 directions
        final.blit(outline, (0, 1))
        final.blit(outline, (2, 1))
        final.blit(outline, (1, 0))
        final.blit(outline, (1, 2))
        
        # Draw original in center
        final.blit(surface, (1, 1))
        
        return final

    def get_placeholder(self) -> pygame.Surface:
        s = pygame.Surface((32, 32))
        s.fill((255, 0, 255))
        return s
