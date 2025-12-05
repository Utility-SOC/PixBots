# pixbots_enhanced/ui/hex_editor.py
# FULLY RESTORED AND ENHANCED VERSION

import pygame
import math
from typing import Dict, Optional

from hex_system.hex_coord import HexCoord, pixel_to_hex
from hex_system.hex_tile import (
    HexTile, BasicConduitTile, AmplifierTile, ResonatorTile,
    SplitterTile, WeaponMountTile, ReflectorTile, FilterTile,
    TileCategory
)
from hex_system.hex_renderer import HexRenderer
from equipment.component import ComponentEquipment

class TilePalette:
    """Manages available tiles for placement."""
    def __init__(self):
        # Create tile instances for the palette to get their properties
        self.tiles = [
            ("1", "Conduit", BasicConduitTile(tile_type="Conduit", category=TileCategory.CONDUIT)),
            ("2", "Amplifier", AmplifierTile(tile_type="Amplifier", category=TileCategory.PROCESSOR, description="Boosts energy.")),
            ("3", "Resonator", ResonatorTile(tile_type="Resonator", category=TileCategory.PROCESSOR, description="Adds synergy.")),
            ("4", "Splitter", SplitterTile(tile_type="Splitter", category=TileCategory.ROUTER, description="Splits energy.")),
            ("5", "Reflector", ReflectorTile(tile_type="Reflector", category=TileCategory.ROUTER, description="Redirects energy.")),
            ("6", "Weapon", WeaponMountTile(tile_type="Weapon", category=TileCategory.OUTPUT, description="Fires energy.")),
        ]
        self.selected_index = 0

    def get_selected(self) -> HexTile:
        # Return a copy of the selected tile prototype
        return self.tiles[self.selected_index][2]

    def select_by_key(self, key: int):
        num_key = key - pygame.K_0
        if 1 <= num_key <= len(self.tiles):
            self.selected_index = num_key - 1

class ComponentHexEditor:
    """Embedded hex editor with full UI features restored."""
    def __init__(self, component: ComponentEquipment, screen: pygame.Surface):
        self.screen = screen
        self.component = component
        self.renderer = HexRenderer(screen.get_width(), screen.get_height(), hex_size=40) # Larger hexes
        self.palette = TilePalette()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 48)
        self.instruction_font = pygame.font.Font(None, 20)
        self.mouse_hex: Optional[HexCoord] = None
        self.tile_grid = self.component.tile_slots.copy()

    def get_mouse_hex(self) -> Optional[HexCoord]:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_x = mouse_x - self.renderer.camera_x
        world_y = mouse_y - self.renderer.camera_y
        
        hex_coord = pixel_to_hex(world_x, world_y, self.renderer.hex_size)
        
        # Check if the coordinate is within the component's grid bounds
        if 0 <= hex_coord.q < self.component.grid_width and \
           0 <= hex_coord.r < self.component.grid_height:
            return hex_coord
        return None

    def handle_input(self, event) -> Optional[str]:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: return "close"
            elif pygame.K_1 <= event.key <= pygame.K_6:
                self.palette.select_by_key(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.mouse_hex = self.get_mouse_hex()
            if self.mouse_hex:
                if event.button == 1: self.handle_left_click()
                elif event.button == 3: self.handle_right_click()
        return None
    
    def handle_left_click(self):
        if self.mouse_hex:
            is_core = self.component.core and self.component.core.position == self.mouse_hex
            if not is_core:
                self.tile_grid[self.mouse_hex] = self.palette.get_selected()
    
    def handle_right_click(self):
        if self.mouse_hex and self.mouse_hex in self.tile_grid:
            del self.tile_grid[self.mouse_hex]

    def save_changes(self):
        self.component.tile_slots = self.tile_grid
        self.component.recalculate_stats()

    def update(self):
        self.mouse_hex = self.get_mouse_hex()

    def draw(self):
        self.screen.fill((20, 20, 30))
        self._draw_title_and_instructions()
        self._draw_grid_and_tiles()
        self._draw_palette()
        self._draw_hover_info()

    def _draw_title_and_instructions(self):
        title_surf = self.title_font.render(f"Editing: {self.component.name}", True, (255, 255, 100))
        self.screen.blit(title_surf, title_surf.get_rect(centerx=self.screen.get_width()/2, y=20))
        
        instructions = [
            "Controls:", "  1-6: Select Tile", "  L-Click: Place Tile",
            "  R-Click: Remove Tile", "  ESC: Save & Exit"
        ]
        for i, line in enumerate(instructions):
            inst_surf = self.instruction_font.render(line, True, (200, 200, 200))
            self.screen.blit(inst_surf, (20, 100 + i * 22))

    def _draw_grid_and_tiles(self):
        # Draw grid boundary first
        for q in range(self.component.grid_width):
            for r in range(self.component.grid_height):
                self.renderer.draw_hex_outline(HexCoord(q,r), self.renderer.grid_color)
        
        # Draw placed tiles with text
        self.renderer.draw_grid(self.tile_grid, [self.mouse_hex] if self.mouse_hex else [])

        # Highlight the core
        if self.component.core and self.component.core.position:
            core_pos = self.component.core.position
            self.renderer.draw_hex_filled(core_pos, (255, 50, 50))
            self.renderer.draw_hex_text(core_pos, "Core", (255, 255, 255))

    def _draw_palette(self):
        px = 20
        py = self.screen.get_height() - 100
        for i, (key, name, tile) in enumerate(self.palette.tiles):
            rect = pygame.Rect(px + i * 110, py, 100, 80)
            is_selected = i == self.palette.selected_index
            
            border_color = (255, 255, 100) if is_selected else (80, 80, 120)
            pygame.draw.rect(self.screen, (40, 40, 50), rect)
            pygame.draw.rect(self.screen, border_color, rect, 2)
            
            key_surf = self.font.render(key, True, (255, 255, 255))
            self.screen.blit(key_surf, (rect.x + 5, rect.y + 5))
            
            name_surf = self.instruction_font.render(name, True, (200, 200, 200))
            self.screen.blit(name_surf, name_surf.get_rect(centerx=rect.centerx, y=rect.y + 30))

    def _draw_hover_info(self):
        if not self.mouse_hex: return

        box_w, box_h = 280, 150
        box_x, box_y = self.screen.get_width() - box_w - 20, 100
        
        info_lines = [f"Hex Coordinate: ({self.mouse_hex.q}, {self.mouse_hex.r})"]
        tile = self.tile_grid.get(self.mouse_hex)
        
        if self.component.core and self.component.core.position == self.mouse_hex:
            info_lines.append("Energy Core")
            info_lines.append("The source of all power.")
        elif tile:
            info_lines.append(f"Tile: {tile.name}")
            info_lines.append(f"Category: {tile.category.value.title()}")
            if tile.description:
                info_lines.append(f"Desc: {tile.description}")
        else:
            info_lines.append("Empty Slot")

        pygame.draw.rect(self.screen, (30, 30, 40, 200), (box_x, box_y, box_w, box_h))
        pygame.draw.rect(self.screen, (100, 100, 150), (box_x, box_y, box_w, box_h), 2)

        for i, line in enumerate(info_lines):
            line_surf = self.instruction_font.render(line, True, (220, 220, 220))
            self.screen.blit(line_surf, (box_x + 10, box_y + 10 + i * 22))

