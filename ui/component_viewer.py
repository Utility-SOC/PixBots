# pixbots_enhanced/ui/component_viewer.py
# UPDATED to use DiegeticUI

import pygame
from typing import List, Optional

from equipment.component import ComponentEquipment
from core.asset_manager import ProceduralAssetManager
from ui.diegetic_ui import DiegeticUI

class ComponentViewer:
    """UI for viewing equipped components."""
    
    def __init__(self, screen: pygame.Surface, asset_manager: ProceduralAssetManager, player=None):
        self.screen = screen
        self.asset_manager = asset_manager
        self.player = player
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
        # Draw Scanlines
        DiegeticUI.draw_scanlines(screen)
        
        component = self.get_current_component()
        if not component:
            self.draw_no_components(screen)
            return
        
        # Draw background panel
        panel_height = 500
        panel_rect = pygame.Rect(self.panel_x, self.panel_y, self.panel_width, panel_height)
        
        DiegeticUI.draw_holographic_panel(screen, panel_rect, DiegeticUI.HOLO_BLUE)
        
        y_offset = self.panel_y + 20
        
        # Title
        title_text = f"{component.name}"
        title_surface = self.font_title.render(title_text, True, DiegeticUI.HOLO_BLUE)
        title_rect = title_surface.get_rect(centerx=panel_rect.centerx, y=y_offset)
        screen.blit(title_surface, title_rect)
        y_offset += 50
        
        # Stats
        # If we have a player, try to get context from Torso for accurate simulation
        input_context = None
        input_dir = 0
        
        if self.player and component.slot != "torso":
            # Find the torso
            torso = self.player.components.get("torso")
            if torso and torso.core:
                # Determine direction based on slot
                # Right Arm (enters from West/Left side) -> Needs Torso's East output (0)
                # Left Arm (enters from East/Right side) -> Needs Torso's West output (3)
                # Head (enters from Bottom) -> Needs Torso's Top output (??) - Let's check get_entry_exit_hexes logic
                
                # Simplified: Just ask the Torso for the output in the direction of this component
                # We need to map Slot -> Direction from Torso
                # 0: Right (East) -> Right Arm
                # 3: Left (West) -> Left Arm
                # 1/2: Bottom Right/Left -> Legs?
                # 4/5: Top Left/Right -> Head/Back?
                
                # Let's assume standard layout:
                # 0 (East) -> Right Arm
                # 3 (West) -> Left Arm
                # 1 (SE) -> Right Leg
                # 4 (SW) -> Left Leg
                # 5 (NW) -> Head
                # 2 (NE) -> Back
                
                torso_dir = -1
                if component.slot == "right_arm": torso_dir = 0
                elif component.slot == "left_arm": torso_dir = 3
                elif component.slot == "right_leg": torso_dir = 1
                elif component.slot == "left_leg": torso_dir = 4
                elif component.slot == "head": torso_dir = 5
                elif component.slot == "back": torso_dir = 2
                
                if torso_dir != -1:
                    # Generate context from Torso
                    input_context = torso.core.generate_context(torso_dir)
                    # Determine input direction
                    # The energy travels FROM the Torso INTO the component.
                    # So the input_dir (flow direction) is the SAME as the Torso output direction.
                    input_dir = torso_dir
        
        # If no context found (or not equipped), calculate_stats will use default test context
        if input_context:
            # We need to manually call simulate_flow to get the stats with this context
            # because component.calculate_stats() creates its own test context if none provided,
            # but we want to use THIS context.
            # Actually, let's update calculate_stats to accept an optional context?
            # Or just call simulate_flow here.
            _, stats, _ = component.simulate_flow(input_context, input_dir)
            
            # Re-apply level bonus manually since we bypassed calculate_stats
            level_mult = 1.0 + (component.level * 0.1)
            stats["armor"] = int(component.base_armor * level_mult)
            stats["hp"] = int(component.base_hp * level_mult)
            stats["speed"] = component.base_speed * level_mult
            stats["damage_multiplier"] = stats["damage_multiplier"] * level_mult
            stats["weapon_damage"] = stats.get("weapon_damage", 0.0) * level_mult
            
        else:
            stats = component.calculate_stats()
            
        total_tiles = len(component.tile_slots)
        active_tiles = stats.get("active_tiles", 0)
        
        stat_lines = [
            f"Armor: +{stats['armor']}", f"HP: +{stats['hp']}",
            f"Speed: +{stats['speed']:.1f}", f"Damage Mult: {stats['damage_multiplier']:.2f}x",
            f"Weapon Damage: {stats['weapon_damage']:.0f}",
            f"Powered Tiles: {active_tiles}/{total_tiles}"
        ]
        
        # Draw Grid Preview
        # We need a HexRenderer here.
        from hex_system.hex_renderer import HexRenderer
        # Initialize renderer if not exists (lazy init to avoid init issues)
        if not hasattr(self, 'renderer'):
            self.renderer = HexRenderer(self.screen_width, self.screen_height, hex_size=20)
            # Center camera on the panel
            self.renderer.camera_x = self.panel_x + self.panel_width // 2
            self.renderer.camera_y = self.panel_y + 350 # Below stats
            
        # Draw Schematic Background for valid coords
        for coord in component.valid_coords:
            self.renderer.draw_hex_filled(coord, (30, 40, 50))
            self.renderer.draw_hex_outline(coord, (60, 100, 150))
            
        # Draw actual tiles
        # We need to map component.tile_slots to the renderer
        # But HexRenderer.draw_grid expects a dict.
        # We can just iterate and draw manually to avoid full grid overhead or just use it.
        for coord, tile in component.tile_slots.items():
            if coord in component.valid_coords:
                self.renderer.draw_hex_filled(coord, tile.base_color)
                self.renderer.draw_hex_outline(coord, (200, 200, 200), 1)

        for i, line in enumerate(stat_lines):
            stat_surface = self.font_normal.render(line, True, DiegeticUI.HOLO_BLUE) # Use bright color
            # Draw a small background for text
            bg_rect = stat_surface.get_rect(topleft=(self.panel_x + 30, y_offset + i * 30))
            bg_rect.inflate_ip(10, 4)
            pygame.draw.rect(screen, (0, 0, 0, 200), bg_rect) # Dark semi-transparent box
            screen.blit(stat_surface, (self.panel_x + 30, y_offset + i * 30))
            
        # Instructions
        instr_text = "Arrows: Cycle | E: Edit Grid | ESC: Close"
        instr_surf = self.font_normal.render(instr_text, True, (150, 255, 150)) # Bright green hint
        instr_rect = instr_surf.get_rect(centerx=panel_rect.centerx, bottom=panel_rect.bottom - 20)
        screen.blit(instr_surf, instr_rect)
            
    def draw_no_components(self, screen: pygame.Surface):
        text = "No components equipped"
        text_surface = self.font_title.render(text, True, (200, 200, 200))
        text_rect = text_surface.get_rect(center=(self.screen_width / 2, self.screen_height / 2))
        screen.blit(text_surface, text_rect)

