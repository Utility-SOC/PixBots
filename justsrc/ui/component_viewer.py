# pixbots_enhanced/ui/component_viewer.py
# CORRECTED to use the modern, simpler initialization.

import pygame
from typing import List, Optional

from equipment.component import ComponentEquipment
from core.asset_manager import ProceduralAssetManager

class ComponentViewer:
    """UI for viewing equipped components."""
    
    def __init__(self, screen: pygame.Surface, asset_manager: ProceduralAssetManager):
        self.screen = screen
        self.asset_manager = asset_manager
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        self.current_index = 0
        self.components: List[ComponentEquipment] = []
        
        # Visual properties
        self.panel_width = 400
        self.panel_x = (self.screen_width - self.panel_width) // 2
        self.panel_y = 100
        
        # Fonts from Asset Manager
        self.font_title = self.asset_manager.get_font(None, 36)
        self.font_normal = self.asset_manager.get_font(None, 24)
    
    def set_components(self, components: List[ComponentEquipment]):
        self.components = components
        self.current_index = 0
    
    def cycle_component(self, direction: int):
        if not self.components: return
        self.current_index = (self.current_index + direction) % len(self.components)
    
    def get_current_component(self) -> Optional[ComponentEquipment]:
        if self.components and 0 <= self.current_index < len(self.components):
            return self.components[self.current_index]
        return None

    def handle_input(self, event: pygame.event.Event):
        """Handles input events."""
        # Currently handled in main.py, but added for safety/consistency
        pass
    
    def draw(self, screen: pygame.Surface):
        component = self.get_current_component()
        if not component:
            self.draw_no_components(screen)
            return
        
        # Draw background panel
        panel_height = 500
        panel_rect = pygame.Rect(self.panel_x, self.panel_y, self.panel_width, panel_height)
        pygame.draw.rect(screen, (20, 20, 30), panel_rect)
        pygame.draw.rect(screen, (100, 100, 150), panel_rect, 3)
        
        y_offset = self.panel_y + 20
        
        # Title
        title_text = f"{component.name}"
        title_surface = self.font_title.render(title_text, True, (255, 255, 100))
        title_rect = title_surface.get_rect(centerx=panel_rect.centerx, y=y_offset)
        screen.blit(title_surface, title_rect)
        y_offset += 50
        
        # Stats
        stats = component.calculate_stats()
        stat_lines = [
            f"Armor: +{stats['armor']}", f"HP: +{stats['hp']}",
            f"Speed: +{stats['speed']:.1f}", f"Damage Mult: {stats['damage_multiplier']:.2f}x",
            f"Weapon Damage: {stats['weapon_damage']:.0f}"
        ]
        
        for i, line in enumerate(stat_lines):
            stat_surface = self.font_normal.render(line, True, (200, 255, 200))
            screen.blit(stat_surface, (self.panel_x + 30, y_offset + i * 30))
            
    def draw_no_components(self, screen: pygame.Surface):
        text = "No components equipped"
        text_surface = self.font_title.render(text, True, (200, 200, 200))
        text_rect = text_surface.get_rect(center=(self.screen_width / 2, self.screen_height / 2))
        screen.blit(text_surface, text_rect)

