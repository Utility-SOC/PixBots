import pygame
import math
import random
import constants
import json
import os
from typing import Tuple, Dict, Optional

class ProceduralGenerator:
    """Generates procedural graphics for the game."""
    
    RARITY_COLORS = {
        "Common": (100, 100, 100),
        "Uncommon": (50, 200, 50),
        "Rare": (50, 50, 200),
        "Epic": (150, 50, 200),
        "Legendary": (255, 165, 0)
    }

    def __init__(self, asset_manager=None):
        self.asset_manager = asset_manager
        self.parts_data = {}
        self.loaded_images = {}
        self.load_parts_data()

    def load_parts_data(self):
        try:
            with open("data/weapon_parts.json", "r") as f:
                self.parts_data = json.load(f)
        except Exception:
            self.parts_data = {"barrels": {}, "bodies": {}, "stocks": {}}

    def get_image(self, path: str) -> pygame.Surface:
        if path not in self.loaded_images:
            try:
                img = pygame.image.load(path).convert_alpha()
                self.loaded_images[path] = img
            except Exception:
                s = pygame.Surface((16, 16))
                s.fill((255, 0, 255))
                self.loaded_images[path] = s
        return self.loaded_images[path]

    @staticmethod
    def apply_snes_effect(surface: pygame.Surface) -> pygame.Surface:
        mask = pygame.mask.from_surface(surface)
        outline = mask.to_surface(setcolor=(0, 0, 0, 255), unsetcolor=(0, 0, 0, 0))
        final = pygame.Surface((surface.get_width() + 2, surface.get_height() + 2), pygame.SRCALPHA)
        final.blit(outline, (0, 1))
        final.blit(outline, (2, 1))
        final.blit(outline, (1, 0))
        final.blit(outline, (1, 2))
        final.blit(surface, (1, 1))
        return final

    def compose_weapon(self, barrel_id: str, body_id: str, stock_id: str, color_tint: Tuple[int, int, int] = None) -> pygame.Surface:
        body_def = self.parts_data["bodies"].get(body_id)
        barrel_def = self.parts_data["barrels"].get(barrel_id)
        stock_def = self.parts_data["stocks"].get(stock_id)
        
        if not body_def: 
            s = pygame.Surface((32, 32))
            s.fill((255, 0, 255))
            return s
            
        canvas = pygame.Surface((64, 32), pygame.SRCALPHA)
        body_x, body_y = 20, 10
        
        if stock_def:
            stock_img = self.get_image(stock_def["image_path"])
            bx, by = body_def.get("stock_mount", [0, 0])
            sx, sy = stock_def.get("attachment_point", [0, 0])
            canvas.blit(stock_img, (body_x + bx - sx, body_y + by - sy))
            
        if barrel_def:
            barrel_img = self.get_image(barrel_def["image_path"])
            bx, by = body_def.get("barrel_mount", [10, 0])
            sx, sy = barrel_def.get("attachment_point", [0, 0])
            canvas.blit(barrel_img, (body_x + bx - sx, body_y + by - sy))
            
        body_img = self.get_image(body_def["image_path"])
        canvas.blit(body_img, (body_x, body_y))
        
        if color_tint:
            canvas = ProceduralGenerator.tint_surface(canvas, color_tint)
            
        canvas = ProceduralGenerator.apply_snes_effect(canvas)
        return canvas

    @classmethod
    def generate_hex_background(cls, item_type: str, rarity: str, size: int = 64, instance=None) -> pygame.Surface:
        """Generates a background for a hex item based on type and rarity."""
        
        if item_type == "weapon" and instance:
            try:
                
                color = cls.RARITY_COLORS.get(rarity, (100, 100, 100))
                barrel = "basic_barrel"
                body = "basic_body"
                stock = "basic_stock"
                if rarity in ["Rare", "Epic", "Legendary"]:
                    body = "tech_body"
                    barrel = "sniper_barrel"
                
                img = instance.compose_weapon(barrel, body, stock, color)
                scaled = pygame.transform.scale(img, (size - 10, size // 2))
                surface = pygame.Surface((size, size), pygame.SRCALPHA)
                base_color = cls.RARITY_COLORS.get(rarity, (100, 100, 100))
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
