# pixbots_enhanced/hex_system/hex_renderer.py
# UPDATED to support drawing text on hexes.

import pygame
import math
from typing import Dict, List, Tuple
from .hex_coord import HexCoord, hex_to_pixel, hex_corners
from .hex_tile import HexTile

class HexRenderer:
    def __init__(self, screen_width: int, screen_height: int, hex_size: float = 30):
        self.screen = pygame.display.get_surface()
        self.hex_size = hex_size
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.camera_x = screen_width // 2
        self.camera_y = screen_height // 2
        self.bg_color = (20, 20, 30)
        self.grid_color = (50, 50, 60)
        self.highlight_color = (255, 255, 100)
        self.font_small = pygame.font.Font(None, 16) # Smaller font for hex labels

    def world_to_screen(self, hex_coord: HexCoord) -> Tuple[float, float]:
        world_x, world_y = hex_to_pixel(hex_coord, self.hex_size)
        return (world_x + self.camera_x, world_y + self.camera_y)

    def draw_hex_outline(self, hex_coord: HexCoord, color: tuple, width: int = 1):
        center_x, center_y = self.world_to_screen(hex_coord)
        points = hex_corners(center_x, center_y, self.hex_size)
        pygame.draw.polygon(self.screen, color, points, width)

    def draw_hex_filled(self, hex_coord: HexCoord, color: tuple):
        center_x, center_y = self.world_to_screen(hex_coord)
        points = hex_corners(center_x, center_y, self.hex_size)
        pygame.draw.polygon(self.screen, color, points)

    def draw_hex_text(self, hex_coord: HexCoord, text: str, color: tuple):
        """Draws text centered inside a hex."""
        text_surf = self.font_small.render(text, True, color)
        text_rect = text_surf.get_rect()
        center_x, center_y = self.world_to_screen(hex_coord)
        text_rect.center = (int(center_x), int(center_y))
        self.screen.blit(text_surf, text_rect)

    def draw_grid(self, tile_grid: Dict[HexCoord, HexTile], highlight_coords: List[HexCoord]):
        for coord, tile in tile_grid.items():
            is_highlighted = coord in highlight_coords
            outline_color = self.highlight_color if is_highlighted else self.grid_color
            self.draw_hex_filled(coord, tile.base_color)
            self.draw_hex_outline(coord, outline_color, 2)
            # Add tile name to the hex
            self.draw_hex_text(coord, tile.name.split(" ")[0], (0, 0, 0))

