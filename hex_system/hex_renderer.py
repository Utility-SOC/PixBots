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
            
            # Draw Direction Indicators
            center_x, center_y = self.world_to_screen(coord)
            
            if hasattr(tile, "exit_direction"):
                # Draw arrow for single exit
                self._draw_direction_arrow((center_x, center_y), tile.exit_direction)
                
            if hasattr(tile, "exit_direction_1") and hasattr(tile, "exit_direction_2"):
                # Draw arrows for splitter
                self._draw_direction_arrow((center_x, center_y), tile.exit_direction_1, color=(100, 255, 100))
                self._draw_direction_arrow((center_x, center_y), tile.exit_direction_2, color=(100, 255, 100))
                
            if hasattr(tile, "rotation_steps"):
                 # Draw reflector orientation (simple line for now)
                 angle = math.radians(tile.rotation_steps * 60)
                 end_x = center_x + math.cos(angle) * (self.hex_size * 0.8)
                 end_y = center_y + math.sin(angle) * (self.hex_size * 0.8)
                 pygame.draw.line(self.screen, (255, 255, 255), (center_x, center_y), (end_x, end_y), 3)

            # Add tile name to the hex
            # Use full name, simplified for secondary systems
            display_name = tile.name.split(" ")[0] if " " in tile.name and len(tile.name) > 8 else tile.name
            self.draw_hex_text(coord, display_name, (0, 0, 0))

    def _draw_direction_arrow(self, center: Tuple[float, float], direction: int, color: tuple = (255, 255, 255)):
        cx, cy = center
        
        # Map logical direction (0=E, 1=NE, 2=NW, 3=W, 4=SW, 5=SE) 
        # to visual angle (Pygame Y-down: 0=E, 90=S, 270=N)
        # Logical 1 (NE) should be -60 deg (300)
        # Logical 5 (SE) should be +60 deg
        
        visual_angle_map = {
            0: 0,
            1: 300,
            2: 240,
            3: 180,
            4: 120,
            5: 60
        }
        
        angle_deg = visual_angle_map.get(direction % 6, 0)
        angle = math.radians(angle_deg)
        
        # Arrow end point
        end_x = cx + math.cos(angle) * (self.hex_size * 0.7)
        end_y = cy + math.sin(angle) * (self.hex_size * 0.7)
        
        pygame.draw.line(self.screen, color, (cx, cy), (end_x, end_y), 3)
        pygame.draw.circle(self.screen, color, (int(end_x), int(end_y)), 4)

    def draw_flow_overlay(self, flows: List[Tuple[HexCoord, HexCoord, Dict]], valid_coords: set[HexCoord] = None):
        """
        Draws energy flow lines on top of the grid with high-fidelity effects (H6).
        flows: List of (start_coord, end_coord, synergy_mix_dict)
        valid_coords: Set of valid hex coordinates.
        """
        from hex_system.energy_packet import SynergyType
        from systems.energy_system import EnergySystem
        
        current_time = pygame.time.get_ticks() / 1000.0
        
        synergy_colors = {
            SynergyType.FIRE: (255, 100, 50),
            SynergyType.ICE: (100, 200, 255),
            SynergyType.RAW: (200, 200, 200),
            SynergyType.VORTEX: (150, 50, 200),
            SynergyType.EXPLOSION: (255, 100, 50),
            SynergyType.LIGHTNING: (255, 255, 0),
            SynergyType.POISON: (100, 255, 100),
            SynergyType.KINETIC: (150, 150, 150),
            SynergyType.PIERCE: (200, 50, 50),
            SynergyType.VAMPIRIC: (100, 0, 0)
        }
        
        for start, end, mix in flows:
            start_x, start_y = self.world_to_screen(start)
            end_x, end_y = self.world_to_screen(end)
            
            is_exit = valid_coords is not None and end not in valid_coords
            
            # H5/H6: Use Normalized Magnitude
            raw_mag = sum(v for k,v in mix.items())
            norm_mag = EnergySystem.calculate_flow(raw_mag) # 0-1000
            
            # Filter significant synergies and sort
            active_synergies = [(k, v) for k, v in mix.items() if v > 1.0]
            if not active_synergies: continue
            active_synergies.sort(key=lambda x: x[1], reverse=True)
            active_synergies = active_synergies[:3]

            count = len(active_synergies)
            # Center-Dominant Layout strategy
            # We want the Dominant synergy (Index 0) to be in the Center and drawn LAST (Top).
            # Others on sides.
            
            # Prepare render items: (Synergy, Mag, OffsetMultiplier, Z-Index)
            render_items = []
            
            # --- Vector Calculations (Restored) ---
            dx = end_x - start_x
            dy = end_y - start_y
            length = math.sqrt(dx*dx + dy*dy)
            if length == 0: continue
            
            ux, uy = dx/length, dy/length
            px, py = -uy, ux # Perpendicular vector
            
            if is_exit:
                clip_dist = self.hex_size * 0.9
                end_x = start_x + ux * clip_dist
                end_y = start_y + uy * clip_dist
            # --------------------------------------

            # Restore Pulse and Intensity
            pulse_freq = 5.0
            intensity = norm_mag / 1000.0

            if count == 1:
                render_items.append((active_synergies[0][0], active_synergies[0][1], 0.0))
            elif count == 2:
                # Big (0) at +0.5, Small (1) at -0.5
                # Draw Small first, then Big
                render_items.append((active_synergies[1][0], active_synergies[1][1], -0.5))
                render_items.append((active_synergies[0][0], active_synergies[0][1], 0.5))
            elif count >= 3:
                # Big (0) at 0.
                # Med (1) at -1.
                # Small (2) at +1.
                # Draw Med/Small first, then Big.
                render_items.append((active_synergies[1][0], active_synergies[1][1], -1.0))
                render_items.append((active_synergies[2][0], active_synergies[2][1], 1.0))
                render_items.append((active_synergies[0][0], active_synergies[0][1], 0.0))
            
            # Cap spacing to prevent wide separation
            base_spacing = min(8, max(4, int(norm_mag / 150))) 
            
            for i, (syn_type, magnitude, offset_mult) in enumerate(render_items):
                offset = offset_mult * base_spacing
                
                sx, sy = start_x + px * offset, start_y + py * offset
                ex, ey = end_x + px * offset, end_y + py * offset
                
                base_color = synergy_colors.get(syn_type, (200, 200, 200))
                
                # Apply Pulse
                # Temporal offset: i is render order. 
                # To sync "Red First, Then Blue", we want consistent phase based on synergy type?
                # Or just render order.
                # Let's use render order phase shift.
                local_pulse = (math.sin(current_time * pulse_freq - i * 1.5) + 1) * 0.5
                
                pulse_val = local_pulse * intensity * 0.8
                color = (
                    min(255, base_color[0] + int(pulse_val * 100)),
                    min(255, base_color[1] + int(pulse_val * 100)),
                    min(255, base_color[2] + int(pulse_val * 100))
                )
    
                # H6: Size/Thickness properties
                # Inner (Dominant) should be thickest?
                is_dominant = (offset_mult == 0.0 and count != 2) or (count == 2 and offset_mult == 0.5)
                
                # CLAMP INTENSITY AND THICKNESS
                # norm_mag is 0-1000 officially, but can go higher with huge damage.
                # Cap effective intensity for drawing purposes.
                clamped_intensity = min(intensity, 5.0) 
                
                base_thickness = max(2, int(2 + clamped_intensity * 2))
                base_thickness = min(base_thickness, 12) # Hard cap at 12px
                
                if is_dominant: base_thickness += 2
                
                # Draw main line
                pygame.draw.line(self.screen, color, (sx, sy), (ex, ey), base_thickness)
                
                # Particles
                num_particles = max(1, int(intensity * 5))
                particle_phase = (current_time * 1.5 - i * 0.2) % 1.0 
                
                for p in range(num_particles):
                    phase = (particle_phase + p/num_particles) % 1.0
                    p_x = sx + (ex - sx) * phase
                    p_y = sy + (ey - sy) * phase
                    
                    p_size = base_thickness + 2
                    pygame.draw.circle(self.screen, (255, 255, 255), (int(p_x), int(p_y)), p_size)

                # Entry Edge Highlight (unchanged logic, just color update)
                angle_to_start = math.atan2(start_y - end_y, start_x - end_x)
                end_corners = hex_corners(end_x, end_y, self.hex_size)
                end_corners.sort(key=lambda p: (p[0]-start_x)**2 + (p[1]-start_y)**2)
                c1, c2 = end_corners[0], end_corners[1]
                
                # Glowy edge
                pygame.draw.line(self.screen, color, c1, c2, base_thickness + 2)
                
                if is_exit:
                    pygame.draw.circle(self.screen, color, (int(ex), int(ey)), base_thickness + 2)
                    p_len = 6
                    pygame.draw.line(self.screen, (255, 255, 255), 
                                     (ex - px * p_len, ey - py * p_len), 
                                     (ex + px * p_len, ey + py * p_len), 2)
                    
                    edge_mid_x = (start_x + end_x) / 2
                    edge_mid_y = (start_y + end_y) / 2
                    indicator_offset = self.hex_size * 0.4
                    ind_x = edge_mid_x + ux * indicator_offset
                    ind_y = edge_mid_y + uy * indicator_offset
                    
                    chev_size = 5
                    p1 = (ind_x - ux * chev_size + px * chev_size, ind_y - uy * chev_size + py * chev_size)
                    p2 = (ind_x, ind_y)
                    p3 = (ind_x - ux * chev_size - px * chev_size, ind_y - uy * chev_size - py * chev_size)
                    pygame.draw.lines(self.screen, (255, 255, 255), False, [p1, p2, p3], 2)
                else:
                    arrow_pos_x = sx + (ex - sx) * 0.66
                    arrow_pos_y = sy + (ey - sy) * 0.66
                    pygame.draw.circle(self.screen, color, (int(arrow_pos_x), int(arrow_pos_y)), base_thickness)

    def draw_marker_shape(self, center: Tuple[float, float], shape_type: str, color: tuple, size: int = 20):
        """Draws a specific shape marker at the given center coordinates."""
        cx, cy = center
        
        if shape_type == "triangle_right":
            points = [
                (cx - size, cy - size),
                (cx - size, cy + size),
                (cx + size, cy)
            ]
            pygame.draw.polygon(self.screen, color, points)
            pygame.draw.polygon(self.screen, (255, 255, 255), points, 2)
            
        elif shape_type == "triangle_left":
            points = [
                (cx + size, cy - size),
                (cx + size, cy + size),
                (cx - size, cy)
            ]
            pygame.draw.polygon(self.screen, color, points)
            pygame.draw.polygon(self.screen, (255, 255, 255), points, 2)
            
        elif shape_type == "diamond":
            points = [
                (cx, cy - size),
                (cx + size, cy),
                (cx, cy + size),
                (cx - size, cy)
            ]
            pygame.draw.polygon(self.screen, color, points)
            pygame.draw.polygon(self.screen, (255, 255, 255), points, 2)
            
        elif shape_type == "square":
            rect = pygame.Rect(cx - size, cy - size, size * 2, size * 2)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)
            
        elif shape_type == "pentagon":
            points = []
            for i in range(5):
                angle = math.radians(i * 72 - 90) # Start at top
                px = cx + size * math.cos(angle)
                py = cy + size * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(self.screen, color, points)
            pygame.draw.polygon(self.screen, (255, 255, 255), points, 2)
            
        elif shape_type == "star_15":
            points = []
            inner_radius = size * 0.5
            for i in range(30): # 15 points = 30 vertices
                angle = math.radians(i * 12 - 90)
                r = size if i % 2 == 0 else inner_radius
                px = cx + r * math.cos(angle)
                py = cy + r * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(self.screen, color, points)
            pygame.draw.polygon(self.screen, (255, 255, 255), points, 2)
        
        else:
            # Fallback circle
            pygame.draw.circle(self.screen, color, (int(cx), int(cy)), size)
            pygame.draw.circle(self.screen, (255, 255, 255), (int(cx), int(cy)), size, 2)

