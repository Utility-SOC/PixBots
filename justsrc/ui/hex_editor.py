# pixbots_enhanced/ui/hex_editor.py
# REWRITTEN: Specific entry/exit HEX visualization (not edge markers)

import pygame
from typing import Dict, Optional, List, Tuple
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
        self.tiles = [
            ("1", "Conduit", lambda: BasicConduitTile("", TileCategory.CONDUIT)),
            ("2", "Amplifier", lambda: AmplifierTile("", TileCategory.PROCESSOR)),
            ("3", "Resonator", lambda: ResonatorTile("", TileCategory.PROCESSOR)),
            ("4", "Splitter", lambda: SplitterTile("", TileCategory.ROUTER)),
            ("5", "Reflector", lambda: ReflectorTile("", TileCategory.ROUTER)),
            ("6", "Weapon", lambda: WeaponMountTile("", TileCategory.OUTPUT)),
        ]
        self.selected_index = 0

    def get_selected(self) -> HexTile:
        return self.tiles[self.selected_index][2]()

    def select_by_key(self, key: int):
        if 1 <= key <= len(self.tiles):
            self.selected_index = key - 1

class ComponentHexEditor:
    """Hex editor with SPECIFIC entry/exit hex markers."""
    def __init__(self, component: ComponentEquipment, screen: pygame.Surface):
        self.screen = screen
        self.component = component
        self.renderer = HexRenderer(screen.get_width(), screen.get_height(), hex_size=30)
        self.palette = TilePalette()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 48)
        self.mouse_hex: Optional[HexCoord] = None
        self.tile_grid = self.component.tile_slots.copy()
        
        # Splitter configuration state
        self.configuring_splitter: Optional[HexCoord] = None
        self.splitter_config_step: int = 0  # 0=not configuring, 1=set first exit, 2=set second exit

    def get_mouse_hex(self) -> Optional[HexCoord]:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_x = mouse_x - self.renderer.camera_x
        world_y = mouse_y - self.renderer.camera_y
        hex_coord = pixel_to_hex(world_x, world_y, self.renderer.hex_size)
        if 0 <= hex_coord.q < self.component.grid_width and 0 <= hex_coord.r < self.component.grid_height:
            return hex_coord
        return None

    def save_changes(self):
        """Saves the working copy back to component."""
        self.component.tile_slots = self.tile_grid

    def update(self):
        self.mouse_hex = self.get_mouse_hex()

    def handle_input(self, event: pygame.event.Event) -> Optional[str]:
        """Handles input for the hex editor. Returns 'close' if finished."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "close"
            
            # Palette selection
            key_map = {
                pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3,
                pygame.K_4: 4, pygame.K_5: 5, pygame.K_6: 6
            }
            if event.key in key_map:
                self.palette.select_by_key(key_map[event.key])
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if not self.mouse_hex:
                return None
                
            if event.button == 1: # Left Click: Place
                if self._is_in_bounds(self.mouse_hex):
                    new_tile = self.palette.get_selected()
                    self.tile_grid[self.mouse_hex] = new_tile
                    
            elif event.button == 3: # Right Click: Rotate or Delete
                if self.mouse_hex in self.tile_grid:
                    mods = pygame.key.get_mods()
                    if mods & pygame.KMOD_SHIFT:
                        # Shift+Right Click = Delete
                        del self.tile_grid[self.mouse_hex]
                    else:
                        # Right Click = Rotate
                        tile = self.tile_grid[self.mouse_hex]
                        if isinstance(tile, BasicConduitTile):
                            tile.set_exit_direction(tile.exit_direction + 1)
                        elif isinstance(tile, SplitterTile):
                            # Rotate both exits
                            tile.set_exit_direction(0, tile.exit_direction_1 + 1)
                            tile.set_exit_direction(1, tile.exit_direction_2 + 1)
                        elif isinstance(tile, ReflectorTile):
                            tile.rotation_steps = (tile.rotation_steps + 1) % 6
                        else:
                            # If not rotatable, delete it (fallback)
                            del self.tile_grid[self.mouse_hex]
                        
        return None

    def get_entry_exit_hexes(self) -> Tuple[Optional[HexCoord], Optional[HexCoord]]:
        """Returns ONE specific entry hex and ONE specific exit hex."""
        slot = self.component.slot
        mid_q = self.component.grid_width // 2
        mid_r = self.component.grid_height // 2
        
        entry_hex = None
        exit_hex = None
        
        if slot == "torso":
            # Torso special case: reactor is source, multiple exits
            entry_hex = None  # Reactor core is the entry
            exit_hex = None   # Multiple exit directions
        elif slot == "left_arm":
            # Entry from torso (right side), exit to weapon (left side)
            entry_hex = HexCoord(self.component.grid_width - 1, mid_r)
            exit_hex = HexCoord(0, mid_r)
        elif slot == "right_arm":
            # Entry from torso (left side), exit to weapon (right side)
            entry_hex = HexCoord(0, mid_r)
            exit_hex = HexCoord(self.component.grid_width - 1, mid_r)
        elif slot in ["left_leg", "right_leg"]:
            # Entry from top (torso), exit to bottom (jump jet)
            entry_hex = HexCoord(mid_q, 0)
            exit_hex = HexCoord(mid_q, self.component.grid_height - 1)
        elif slot == "head":
            # Entry from bottom (torso), exit to top (focus beam/sensor)
            entry_hex = HexCoord(mid_q, self.component.grid_height - 1)
            exit_hex = HexCoord(mid_q, 0)
        elif slot == "back":
            # Entry from left (torso), exit to right (shield projection)
            entry_hex = HexCoord(0, mid_r)
            exit_hex = HexCoord(self.component.grid_width - 1, mid_r)
        
        return entry_hex, exit_hex

    def draw_entry_exit_markers(self):
        """Draw LARGE, LABELED entry/exit hex markers."""
        entry_hex, exit_hex = self.get_entry_exit_hexes()
        
        # Draw ENTRY hex marker (YELLOW/ORANGE)
        if entry_hex and self._is_in_bounds(entry_hex):
            center_x, center_y = self.renderer.world_to_screen(entry_hex)
            # Large orange circle
            pygame.draw.circle(self.screen, (255, 180, 50), (int(center_x), int(center_y)), 18, 4)
            # "ENTRY" label below
            label = self.font.render("ENTRY", True, (255, 200, 50))
            label_rect = label.get_rect(center=(int(center_x), int(center_y) + 30))
            self.screen.blit(label, label_rect)
        
        # Draw EXIT hex marker (RED)
        if exit_hex and self._is_in_bounds(exit_hex):
            center_x, center_y = self.renderer.world_to_screen(exit_hex)
            # Large red circle
            pygame.draw.circle(self.screen, (255, 50, 50), (int(center_x), int(center_y)), 18, 4)
            # "EXIT" label below
            label = self.font.render("EXIT", True, (255, 80, 80))
            label_rect = label.get_rect(center=(int(center_x), int(center_y) + 30))
            self.screen.blit(label, label_rect)

    def simulate_energy_flow(self) -> List[Tuple[HexCoord, HexCoord, any]]:
        """Simulate energy flow from ENTRY hex to EXIT hex."""
        from hex_system.energy_packet import SynergyType
        
        flows = []
        slot = self.component.slot
        entry_hex, exit_hex = self.get_entry_exit_hexes()
        
        if slot == "torso":
            # Torso: reactor → tiles in all 6 directions
            if not (self.component.core and self.component.core.position):
                return flows
            
            reactor_pos = self.component.core.position
            packet = self.component.core.generate_packet()
            dominant_synergy = packet.get_dominant_synergy()
            
            for direction in range(6):
                next_coord = self._get_neighbor_in_direction(reactor_pos, direction)
                if self._is_in_bounds(next_coord):
                    flows.append((reactor_pos, next_coord, dominant_synergy))
                    entry_direction = (direction + 3) % 6
                    self._trace_energy_path(next_coord, entry_direction, dominant_synergy, flows, set(), 1)
        else:
            # Other components: ENTRY hex → tiles → EXIT hex
            if not entry_hex or not self._is_in_bounds(entry_hex):
                return flows
            
            dominant_synergy = SynergyType.KINETIC
            
            # Start tracing from entry hex in all directions
            for direction in range(6):
                next_coord = self._get_neighbor_in_direction(entry_hex, direction)
                if self._is_in_bounds(next_coord) and next_coord in self.tile_grid:
                    flows.append((entry_hex, next_coord, dominant_synergy))
                    entry_direction = (direction + 3) % 6
                    self._trace_energy_path(next_coord, entry_direction, dominant_synergy, flows, set(), 1)
        
        return flows
    
    def _trace_energy_path(self, coord: HexCoord, entry_dir: int, synergy: any, 
                          flows: List[Tuple[HexCoord, HexCoord, any]], visited: set, depth: int):
        """Recursively trace energy path for visualization."""
        if depth > 20 or coord in visited:
            return
        
        if not self._is_in_bounds(coord):
            return
            
        tile = self.tile_grid.get(coord)
        if not tile:
            return
            
        visited.add(coord)
        
        # Determine exit direction(s)
        if isinstance(tile, SplitterTile):
            exit_directions = tile.get_exit_directions(entry_dir)
            for exit_dir in exit_directions:
                next_coord = self._get_neighbor_in_direction(coord, exit_dir)
                flows.append((coord, next_coord, synergy))
                next_entry = (exit_dir + 3) % 6
                self._trace_energy_path(next_coord, next_entry, synergy, flows, visited.copy(), depth + 1)
        else:
            exit_dir = tile.get_exit_direction(entry_dir)
            next_coord = self._get_neighbor_in_direction(coord, exit_dir)
            flows.append((coord, next_coord, synergy))
            next_entry = (exit_dir + 3) % 6
            self._trace_energy_path(next_coord, next_entry, synergy, flows, visited, depth + 1)

    def _get_neighbor_in_direction(self, coord: HexCoord, direction: int) -> HexCoord:
        offsets = [
            (1, 0),    # 0: E
            (1, -1),   # 1: NE
            (0, -1),   # 2: NW
            (-1, 0),   # 3: W
            (-1, 1),   # 4: SW
            (0, 1),    # 5: SE
        ]
        dq, dr = offsets[direction % 6]
        return HexCoord(coord.q + dq, coord.r + dr)

    def draw_energy_flows(self):
        """Draws animated energy flow lines."""
        flows = self.simulate_energy_flow()
        
        # Get synergy colors
        from hex_system.energy_packet import SynergyType
        colors = {
            SynergyType.KINETIC: (200, 200, 200),
            SynergyType.FIRE: (255, 100, 50),
            SynergyType.LIGHTNING: (100, 100, 255),
            SynergyType.VORTEX: (150, 50, 200),
            SynergyType.POISON: (50, 200, 50),
            SynergyType.ICE: (100, 200, 255),
            SynergyType.RAW: (255, 255, 255)
        }
        
        for start, end, synergy in flows:
            if not self._is_in_bounds(start): continue
            
            start_pos = self.renderer.world_to_screen(start)
            
            if self._is_in_bounds(end):
                end_pos = self.renderer.world_to_screen(end)
            else:
                # Draw a short stub if going out of bounds
                # Calculate direction vector
                # This is a bit complex without vector math, let's just skip drawing out-of-bounds lines for now
                # or approximate it.
                continue
                
            color = colors.get(synergy, (200, 200, 200))
            
            # Draw line
            pygame.draw.line(self.screen, color, start_pos, end_pos, 3)
            
            # Draw moving particle (simple animation)
            import time
            t = time.time() * 2.0
            offset = t % 1.0
            
            dx = end_pos[0] - start_pos[0]
            dy = end_pos[1] - start_pos[1]
            
            px = start_pos[0] + dx * offset
            py = start_pos[1] + dy * offset
            
            pygame.draw.circle(self.screen, (255, 255, 255), (int(px), int(py)), 3)

    def _is_in_bounds(self, coord: HexCoord) -> bool:
        return (0 <= coord.q < self.component.grid_width and 
                0 <= coord.r < self.component.grid_height)
    


    def draw(self):
        self.screen.fill((20, 20, 30))
        
        title_surf = self.title_font.render(f"Editing: {self.component.name}", True, (255, 255, 100))
        title_rect = title_surf.get_rect(center=(self.screen.get_width() / 2, 50))
        self.screen.blit(title_surf, title_rect)
        
        # Draw grid outlines
        for q in range(self.component.grid_width):
            for r in range(self.component.grid_height):
                self.renderer.draw_hex_outline(HexCoord(q,r), (80,80,120))

        # Draw energy flows FIRST (behind tiles)
        self.draw_energy_flows()

        # Draw tiles
        self.renderer.draw_grid(self.tile_grid, [self.mouse_hex] if self.mouse_hex else [])
        
        # Draw LARGE entry/exit markers ON TOP
        self.draw_entry_exit_markers()

        # UI
        palette_text = self.font.render(f"Selected: {self.palette.tiles[self.palette.selected_index][1]} (1-6)", 
                                       True, (255, 255, 255))
        self.screen.blit(palette_text, (10, self.screen.get_height() - 60))
        
        instructions = [
            "Left Click: Place | Right Click: Delete/Rotate | ESC: Save & Close",
            "ORANGE Circle=ENTRY | RED Circle=EXIT | Energy flows Entry→Tiles→Exit"
        ]
        
        # Show splitter configuration message
        if self.configuring_splitter and self.splitter_config_step > 0:
            if self.splitter_config_step == 1:
                msg = "SPLITTER CONFIG: Right-click a neighbor hex for FIRST exit direction"
            else:
                msg = "SPLITTER CONFIG: Right-click a neighbor hex for SECOND exit direction"
            config_surf = self.font.render(msg, True, (255, 255, 100))
            self.screen.blit(config_surf, (10, self.screen.get_height() - 90))
        
        for i, text in enumerate(instructions):
            inst_surf = self.font.render(text, True, (200, 200, 200))
            self.screen.blit(inst_surf, (10, self.screen.get_height() - 30 + i * 20))
