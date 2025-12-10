# pixbots_enhanced/ui/hex_editor.py
# REWRITTEN: Specific entry/exit HEX visualization (not edge markers)

import pygame
import math
from typing import Dict, Optional, List, Tuple
from hex_system.hex_coord import HexCoord, pixel_to_hex, hex_to_pixel
from hex_system.hex_tile import (
    HexTile, BasicConduitTile, AmplifierTile, ResonatorTile,
    SplitterTile, WeaponMountTile, ReflectorTile, FilterTile,
    ShieldGenTile, CloakTile, AcceleratorTile,
    HipsTile, KneesTile, AnklesTile, OrbitalModulatorTile,
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
            ("7", "Super Conduit", lambda: self._create_super_conduit()),
            ("8", "Shield Gen", lambda: ShieldGenTile("", TileCategory.OUTPUT)),
            ("9", "Cloak", lambda: CloakTile("", TileCategory.OUTPUT)),
            ("0", "Accelerator", lambda: AcceleratorTile("", TileCategory.OUTPUT)),
            ("-", "Hips", lambda: HipsTile("", TileCategory.OUTPUT)),
            ("=", "Knees", lambda: KneesTile("", TileCategory.OUTPUT)),
            ("[", "Ankles", lambda: AnklesTile("", TileCategory.OUTPUT)),
            ("]", "Orbital", lambda: OrbitalModulatorTile("", TileCategory.PROCESSOR)),
        ]
        self.selected_index = 0

    def _create_super_conduit(self) -> BasicConduitTile:
        tile = BasicConduitTile("", TileCategory.CONDUIT)
        tile.merge_bonus = 0.2
        tile.base_color = (255, 200, 100)
        tile.name = "Super Conduit"
        return tile

    def get_selected(self) -> HexTile:
        return self.tiles[self.selected_index][2]()

    def select_by_key(self, key: int):
        if 1 <= key <= len(self.tiles):
            self.selected_index = key - 1

class ComponentHexEditor:
    """Hex editor with SPECIFIC entry/exit hex markers."""
    def __init__(self, component: ComponentEquipment, screen: pygame.Surface, input_context=None):
        self.screen = screen
        self.component = component
        self.input_context = input_context # Store the real input context
        self.renderer = HexRenderer(screen.get_width(), screen.get_height(), hex_size=30)
        self.palette = TilePalette()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 48)
        self.mouse_hex: Optional[HexCoord] = None
        self.tile_grid = self.component.tile_slots.copy()
        
        # Splitter configuration state
        self.configuring_splitter: Optional[HexCoord] = None
        self.splitter_config_step: int = 0  # 0=not configuring, 1=set first exit, 2=set second exit
        
        # Center camera on the component grid
        mid_q = self.component.grid_width // 2
        mid_r = self.component.grid_height // 2
        center_hex = HexCoord(mid_q, mid_r)
        
        # Calculate pixel position of center hex relative to (0,0)
        # We want this to be at screen center (width/2, height/2)
        # world_x = screen_x + camera_x  => camera_x = world_x - screen_x
        # But renderer uses: screen_x = world_x - camera_x + offset?
        # Let's check renderer.
        
        # Renderer default: center of screen is (0,0) world coords?
        # No, renderer usually has camera_x, camera_y.
        # Let's just set camera to center the grid.
        # HexRenderer.hex_to_pixel returns (x, y) relative to (0,0) world.
        
        cx, cy = hex_to_pixel(center_hex, self.renderer.hex_size)
        self.renderer.camera_x = screen.get_width() / 2 - cx
        self.renderer.camera_y = screen.get_height() / 2 - cy

    # ... (existing methods) ...

    def draw(self):
        self.screen.fill((20, 20, 30))
        
        # Draw Background Grid (Valid Coords)
        for coord in self.component.valid_coords:
            self.renderer.draw_hex_filled(coord, (30, 40, 50))
            self.renderer.draw_hex_outline(coord, (60, 100, 150))
        
        # Inject test energy for non-Torso components so user can see flow
        input_context = self.input_context # Use the passed context by default
        input_dir = 0
        
        if self.component.slot != "torso":
            from hex_system.energy_packet import ProjectileContext, SynergyType
            
            # If no real context was passed, create a dummy one
            if input_context is None:
                input_context = ProjectileContext(synergies={SynergyType.RAW: 50.0})
            
            # Find entry hex to inject into
            entry_hex, _ = self.component.get_entry_exit_hexes()
            if entry_hex:
                 # Determine input direction based on slot
                 # If Right Arm, entry is usually on the Left side (min_q).
                 # So energy comes FROM the Left (West).
                 # Moving East (0). Enters side 3 (West).
                 
                 if self.component.slot == "right_arm":
                     input_dir = 3 # Enters West side
                 elif self.component.slot == "left_arm":
                     input_dir = 0 # Enters East side (entry is on Right/max_q)
                 elif self.component.slot == "head":
                     input_dir = 4 
                 elif self.component.slot == "legs":
                     input_dir = 1 # Enters Top (NE/NW). Let's say 1 (NE).
                 elif self.component.slot == "back":
                     input_dir = 0 # Enters East side (attached to Left)
                 
        # Backup original tiles from component
        original_tiles = self.component.tile_slots
        # Set component tiles to current editor state for simulation
        self.component.tile_slots = self.tile_grid
        
        # Draw the grid first
        self.renderer.draw_grid(self.tile_grid, highlight_coords=[self.mouse_hex] if self.mouse_hex else [])
        
        # Draw specific markers
        if self.component.slot == "torso":
            self.draw_torso_labels()
        else:
            self.draw_entry_exit_markers()
            
        # Draw Splitter Exits Overlay
        for coord, tile in self.tile_grid.items():
            if isinstance(tile, SplitterTile) and hasattr(tile, "exit_directions"):
                cx, cy = self.renderer.world_to_screen(coord)
                
                # If this specific splitter is being configured, show ALL potential exits
                is_configuring = (self.configuring_splitter == coord)
                directions_to_draw = range(6) if is_configuring else tile.exit_directions
                
                for exit_dir in directions_to_draw:
                    # Draw small arrow or dot indicating exit
                    # Calculate position on edge
                    import math
                    angle_deg = 0
                    if exit_dir == 0: angle_deg = 0
                    elif exit_dir == 1: angle_deg = -60
                    elif exit_dir == 2: angle_deg = -120
                    elif exit_dir == 3: angle_deg = 180
                    elif exit_dir == 4: angle_deg = 120
                    elif exit_dir == 5: angle_deg = 60
                    
                    rad = math.radians(angle_deg)
                    dist = self.renderer.hex_size * 0.7
                    ex = cx + math.cos(rad) * dist
                    ey = cy + math.sin(rad) * dist
                    
                    color = (255, 255, 255)
                    radius = 4
                    
                    if is_configuring:
                        if exit_dir in tile.exit_directions:
                            color = (50, 255, 50) # Active: Green
                            radius = 6
                        else:
                            color = (100, 100, 100) # Inactive: Grey
                            radius = 4
                            
                    pygame.draw.circle(self.screen, color, (int(ex), int(ey)), radius)
                    if is_configuring:
                         pygame.draw.circle(self.screen, (255, 255, 255), (int(ex), int(ey)), radius, 1)
        
        flows, stats, _ = self.component.simulate_flow(input_context=input_context, input_direction=input_dir)
        self.renderer.draw_flow_overlay(flows, valid_coords=self.component.valid_coords)
        
        # Restore original tiles
        self.component.tile_slots = original_tiles
        
        # Draw Palette
        self._draw_palette()
        
        # Draw Legend
        self._draw_legend()
        
        # Draw Stats
        self._draw_stats(stats)
        
        # Draw Tooltips
        if self.mouse_hex:
            self._draw_tooltip(self.mouse_hex)

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
                pygame.K_4: 4, pygame.K_5: 5, pygame.K_6: 6,
                pygame.K_7: 7, pygame.K_8: 8, pygame.K_9: 9, 
                pygame.K_0: 10, pygame.K_MINUS: 11, pygame.K_EQUALS: 12,
                pygame.K_LEFTBRACKET: 13, pygame.K_RIGHTBRACKET: 14
            }
            if event.key in key_map:
                self.palette.select_by_key(key_map[event.key])
            
            elif event.key == pygame.K_s: # Cycle Synergy for Reflector/Filter
                if self.mouse_hex and self.mouse_hex in self.tile_grid:
                    tile = self.tile_grid[self.mouse_hex]
                    if isinstance(tile, ReflectorTile):
                        # Cycle through synergies
                        synergies = ["fire", "ice", "lightning", "vortex", "poison", "explosion", "kinetic", "pierce", "vampiric"]
                        try:
                            current_idx = synergies.index(tile.target_synergy)
                            next_idx = (current_idx + 1) % len(synergies)
                            tile.target_synergy = synergies[next_idx]
                        except ValueError:
                            tile.target_synergy = "fire"

            elif event.key == pygame.K_e: # Edit Exits (Splitter)
                if self.configuring_splitter:
                    # Exit config mode
                    self.configuring_splitter = None
                elif self.mouse_hex and self.mouse_hex in self.tile_grid:
                    tile = self.tile_grid[self.mouse_hex]
                    if isinstance(tile, SplitterTile):
                        self.configuring_splitter = self.mouse_hex
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Handle clicks for Splitter Config
            if event.button == 1 and self.configuring_splitter:
                 tile = self.tile_grid.get(self.configuring_splitter)
                 if tile and isinstance(tile, SplitterTile):
                     # Check if click is on an exit indicator
                     cx, cy = self.renderer.world_to_screen(self.configuring_splitter)
                     mx, my = pygame.mouse.get_pos()
                     
                     import math
                     for i in range(6):
                         angle_deg = 0
                         if i == 0: angle_deg = 0
                         elif i == 1: angle_deg = -60
                         elif i == 2: angle_deg = -120
                         elif i == 3: angle_deg = 180
                         elif i == 4: angle_deg = 120
                         elif i == 5: angle_deg = 60
                         
                         rad = math.radians(angle_deg)
                         dist = self.renderer.hex_size * 0.7
                         ex = cx + math.cos(rad) * dist
                         ey = cy + math.sin(rad) * dist
                         
                         # Check distance to click (increased radius)
                         if math.hypot(mx - ex, my - ey) < 15:
                             tile.toggle_exit_direction(i)
                             return None # Handled
                             
                 # If clicked outside, exit config mode?
                 if self.mouse_hex != self.configuring_splitter:
                     self.configuring_splitter = None
            
            if not self.mouse_hex:
                return None
                
            if event.button == 1: # Left Click: Place
                if not self.configuring_splitter: # Only place if not configuring
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
                            # Rotate all exits by 1
                            new_exits = [(d + 1) % 6 for d in tile.exit_directions]
                            new_exits.sort()
                            tile.exit_directions = new_exits
                        elif isinstance(tile, ReflectorTile):
                            # Cycle reflection offset 1-5
                            tile.reflection_offset = (tile.reflection_offset % 5) + 1
                        else:
                            # If not rotatable, delete it (fallback)
                            del self.tile_grid[self.mouse_hex]
        
        return None

    def get_entry_exit_hexes(self) -> Tuple[Optional[HexCoord], Optional[HexCoord]]:
        """Returns ONE specific entry hex and ONE specific exit hex."""
        # Use the component's logic to ensure consistency
        return self.component.get_entry_exit_hexes()

    def draw_entry_exit_markers(self):
        entry_hex, exit_hex = self.component.get_entry_exit_hexes()
        
        # Draw ENTRY hex marker
        if entry_hex and self._is_in_bounds(entry_hex):
            center_x, center_y = self.renderer.world_to_screen(entry_hex)
            
            # Determine shape based on slot
            shape = "circle"
            color = (255, 165, 0)
            
            slot = self.component.slot
            if slot == "right_arm":
                shape = "triangle_right"
                color = (100, 100, 255) # Blue
            elif slot == "left_arm":
                shape = "triangle_left"
                color = (100, 255, 100) # Green
            elif slot == "head":
                shape = "diamond"
                color = (255, 255, 100) # Yellow
            elif slot == "legs":
                shape = "pentagon"
                color = (100, 255, 255) # Cyan
            elif slot == "back":
                shape = "square"
                color = (200, 100, 255) # Purple
                
            self.renderer.draw_marker_shape((center_x, center_y), shape, color, size=22)
            
            # "IN" label (small)
            label = self.font.render("IN", True, (255, 255, 255))
            label_rect = label.get_rect(center=(int(center_x), int(center_y)))
            self.screen.blit(label, label_rect)
            
        # Draw EXIT hex marker
        if exit_hex and self._is_in_bounds(exit_hex):
            center_x, center_y = self.renderer.world_to_screen(exit_hex)
            
            # Determine shape based on slot
            shape = "circle"
            color = (255, 50, 50)
            
            if self.component.slot in ["right_arm", "left_arm"]:
                shape = "star_15"
                color = (255, 165, 0) # Orange
            
            self.renderer.draw_marker_shape((center_x, center_y), shape, color, size=22)
            
            # "OUT" label
            label = self.font.render("OUT", True, (255, 255, 255))
            label_rect = label.get_rect(center=(int(center_x), int(center_y)))
            self.screen.blit(label, label_rect)




    
    def draw_torso_labels(self):
        """Draws shape markers indicating which body part each direction leads to, with lines to specific hexes."""
        valid = self.component.valid_coords
        if not valid: return
        
        # Calculate bounds
        min_q = min(c.q for c in valid)
        max_q = max(c.q for c in valid)
        min_r = min(c.r for c in valid)
        max_r = max(c.r for c in valid)
        mid_q = (min_q + max_q) // 2
        mid_r = (min_r + max_r) // 2
        
        # Dynamic Target Finding
        # 0: Right Arm (East) -> Max Q, Mid R
        hex_0 = min(valid, key=lambda c: abs(c.q - max_q) + abs(c.r - mid_r))
        
        # 3: Left Arm (West) -> Min Q, Mid R
        hex_3 = min(valid, key=lambda c: abs(c.q - min_q) + abs(c.r - mid_r))
        
        # 1: Head (Top) -> Min R, Mid Q (Using NE direction slot 1)
        hex_1 = min(valid, key=lambda c: abs(c.r - min_r) + abs(c.q - mid_q))
        
        # 2: Back (Top Left) -> Min R, Min Q (Using NW direction slot 2)
        hex_2 = min(valid, key=lambda c: abs(c.r - min_r) + abs(c.q - min_q))
        
        # 5: Right Leg (Bottom Right) -> Max R, Max Q (Using SE direction slot 5)
        hex_5 = min(valid, key=lambda c: abs(c.r - max_r) + abs(c.q - max_q))
        
        # 4: Left Leg (Bottom Left) -> Max R, Min Q (Using SW direction slot 4)
        hex_4 = min(valid, key=lambda c: abs(c.r - max_r) + abs(c.q - min_q))

        # Mapping
        # (direction, shape, color, target_hex)
        markers = [
            (0, "triangle_right", (100, 100, 255), hex_0),   # R. ARM
            (3, "triangle_left", (100, 255, 100), hex_3),    # L. ARM
            (1, "diamond", (255, 255, 100), hex_1),          # HEAD
            (2, "square", (200, 100, 255), hex_2),           # BACK
            (5, "pentagon", (100, 255, 255), hex_5),         # R. LEG
            (4, "pentagon", (100, 255, 255), hex_4)          # L. LEG
        ]
        
        # Filter duplicates to avoid stacking markers if grid is small
        # (Optional, but good for clarity. For now, let them stack or just draw over)
        
        for direction, shape, color, target_hex in markers:
            if not self._is_in_bounds(target_hex): 
                continue
            
            # Calculate Screen Pos of Target Hex
            tx, ty = self.renderer.world_to_screen(target_hex)
            
            # Calculate Label Pos (Further out from center relative to grid center)
            # Find grid center (visual center of bounding box)
            center_q = (min_q + max_q) / 2
            center_r = (min_r + max_r) / 2
            # Approximate pixel center
            cx, cy = self.renderer.world_to_screen(HexCoord(int(center_q), int(center_r)))
            
            # Vector from center to target hex
            vx = tx - cx
            vy = ty - cy
            dist = math.hypot(vx, vy)
            if dist == 0: 
                # Fallback direction if target is at center
                angle = math.radians(direction * 60)
                vx = math.cos(angle)
                vy = math.sin(angle)
                dist = 1.0
            
            # Push out by extra spacing
            label_dist = dist + 80 # Push 80px past the hex
            lx = cx + (vx/dist) * label_dist
            ly = cy + (vy/dist) * label_dist
            
            # Draw Line
            pygame.draw.line(self.screen, (200, 200, 200), (tx, ty), (lx, ly), 2)
            
            # Draw Marker at Label Pos
            self.renderer.draw_marker_shape((lx, ly), shape, color, size=25)
            
            # Draw Exit Indicator on the Hex itself (small highlight)
            pygame.draw.circle(self.screen, color, (int(tx), int(ty)), 5)

    def _draw_palette(self):
        # Draw palette background
        palette_rect = pygame.Rect(10, self.screen.get_height() - 100, 300, 90)
        pygame.draw.rect(self.screen, (30, 30, 40), palette_rect)
        pygame.draw.rect(self.screen, (100, 100, 120), palette_rect, 2)
        
        # Draw selected tile info
        selected_tile = self.palette.get_selected()
        name_surf = self.font.render(f"Selected: {selected_tile.name} (Keys 1-{len(self.palette.tiles)})", True, (255, 255, 255))
        self.screen.blit(name_surf, (20, self.screen.get_height() - 90))
        
        desc_surf = self.font.render(selected_tile.description, True, (200, 200, 200))
        self.screen.blit(desc_surf, (20, self.screen.get_height() - 60))

    def _draw_legend(self):
        """Draws a list of all available tiles and their keys."""
        panel_rect = pygame.Rect(10, 50, 200, 420)
        pygame.draw.rect(self.screen, (30, 30, 40), panel_rect)
        pygame.draw.rect(self.screen, (100, 100, 120), panel_rect, 2)
        
        y = 60
        title = self.title_font.render("Legend", True, (255, 255, 100))
        self.screen.blit(title, (30, y))
        y += 40
        
        # Helper to draw key + name
        def draw_item(key, name, color):
            nonlocal y
            key_surf = self.font.render(f"[{key}]", True, (255, 200, 100))
            name_surf = self.font.render(name, True, (255, 255, 255))
            
            self.screen.blit(key_surf, (20, y))
            self.screen.blit(name_surf, (60, y))
            
            # Small color indicator
            pygame.draw.circle(self.screen, color, (190, y + 10), 6)
            y += 25

        # Updated list matches Palette
        draw_item("1", "Conduit", (100, 100, 100))
        draw_item("2", "Amplifier", (50, 200, 100)) # Greenish active
        draw_item("3", "Resonator", (100, 100, 255)) # Blue active
        draw_item("4", "Splitter", (200, 200, 50))
        draw_item("5", "Reflector", (200, 50, 200))
        draw_item("6", "Weapon", (255, 50, 50))
        draw_item("7", "Super Cond", (255, 200, 100))
        y += 5
        draw_item("8", "Shield", (50, 50, 255))
        draw_item("9", "Cloak", (50, 50, 50))
        draw_item("0", "Accel.", (255, 50, 50))
        y += 5
        draw_item("-", "Hips", (200, 200, 50))
        draw_item("=", "Knees", (150, 100, 255))
        draw_item("[", "Ankles", (50, 200, 200))

    def _draw_stats(self, stats: dict):
        # Draw stats panel on right
        panel_rect = pygame.Rect(self.screen.get_width() - 250, 50, 240, 400)
        pygame.draw.rect(self.screen, (30, 30, 40), panel_rect)
        pygame.draw.rect(self.screen, (100, 100, 120), panel_rect, 2)
        
        y = 60
        title = self.title_font.render("Stats", True, (255, 255, 100))
        self.screen.blit(title, (self.screen.get_width() - 230, y))
        y += 50
        
        lines = [
            f"Flow Efficiency: {stats['damage_multiplier']:.2f}x",
            f"Weapon Dmg: {stats['weapon_damage']:.1f}",
            f"Active Tiles: {stats['active_tiles']}",
        ]
        
        # Add Synergy Breakdown
        magnitudes = stats.get("synergy_magnitudes", {})
        if magnitudes:
            lines.append("--- Synergies ---")
            # Sort by mag
            for syn, mag in sorted(magnitudes.items(), key=lambda x: x[1], reverse=True):
                syn_name = str(syn).split('.')[-1].upper()
                lines.append(f"{syn_name}: {mag:.1f}")
        
        # Add Active Synergy Name
        if stats.get("active_synergy"):
             lines.append(f"DOMINANT: {stats['active_synergy']}")

        for line in lines:
            surf = self.font.render(line, True, (220, 220, 220))
            self.screen.blit(surf, (self.screen.get_width() - 230, y))
            y += 24 # Reduced spacing to fit more info

    def _draw_tooltip(self, hex_coord: HexCoord):
        if hex_coord not in self.tile_grid: return
        
        tile = self.tile_grid[hex_coord]
        mouse_pos = pygame.mouse.get_pos()
        
        lines = [tile.name, tile.description]
        if hasattr(tile, "exit_direction"):
            lines.append(f"Exit Dir: {tile.exit_direction}")
        if hasattr(tile, "merge_bonus") and tile.merge_bonus > 0:
            lines.append(f"Merge Bonus: +{int(tile.merge_bonus*100)}%")
            
        width = 200
        height = len(lines) * 25 + 10
        rect = pygame.Rect(mouse_pos[0] + 15, mouse_pos[1] + 15, width, height)
        
        pygame.draw.rect(self.screen, (20, 20, 30), rect)
        pygame.draw.rect(self.screen, (100, 100, 100), rect, 1)
        
        for i, line in enumerate(lines):
            surf = self.font.render(line, True, (255, 255, 255))
            self.screen.blit(surf, (rect.x + 5, rect.y + 5 + i * 25))

    def _is_in_bounds(self, coord: HexCoord) -> bool:
        return self.component._is_in_bounds(coord)

    def _get_neighbor_in_direction(self, coord: HexCoord, direction: int) -> HexCoord:
        return self.component._get_neighbor_in_direction(coord, direction)
