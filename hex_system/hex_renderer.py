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
            self.draw_hex_text(coord, tile.name.split(" ")[0], (0, 0, 0))

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
        Draws energy flow lines on top of the grid.
        flows: List of (start_coord, end_coord, synergy_mix_dict)
        valid_coords: Set of valid hex coordinates. If provided, lines to invalid coords will be clipped.
        """
        from hex_system.energy_packet import SynergyType
        
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
            
            # Filter significant synergies (> 1.0 magnitude) and sort by magnitude
            active_synergies = [(k, v) for k, v in mix.items() if v > 1.0]
            active_synergies.sort(key=lambda x: x[1], reverse=True)
            
            # Limit to top 3 to avoid clutter
            active_synergies = active_synergies[:3]
            
            if not active_synergies: continue
            
            count = len(active_synergies)
            spacing = 4 # pixels between lines
            total_width = (count - 1) * spacing
            
            # Calculate perpendicular vector for offset
            dx = end_x - start_x
            dy = end_y - start_y
            length = math.sqrt(dx*dx + dy*dy)
            if length == 0: continue
            
            ux = dx / length
            uy = dy / length
            px = -uy
            py = ux
            
            # If exiting, shorten the line to the edge of the start hex
            if is_exit:
                # Hex radius is self.hex_size. Distance to edge is approx hex_size * 0.866 (sqrt(3)/2)
                # Let's go to 0.9 * hex_size
                clip_dist = self.hex_size * 0.9
                end_x = start_x + ux * clip_dist
                end_y = start_y + uy * clip_dist
            
            for i, (syn_type, magnitude) in enumerate(active_synergies):
                offset = (i * spacing) - (total_width / 2)
                
                # Offset start and end points
                sx = start_x + px * offset
                sy = start_y + py * offset
                ex = end_x + px * offset
                ey = end_y + py * offset
                
                color = synergy_colors.get(syn_type, (200, 200, 200))
                
                # Draw line (thickness based on magnitude, clamped)
                thickness = max(2, min(5, int(magnitude / 10)))
                pygame.draw.line(self.screen, color, (sx, sy), (ex, ey), thickness)
                
                # --- NEW: Highlight the shared edge (Entry Side) ---
                # Find the shared edge between start and end hexes
                # The direction from start to end determines which side of 'end' is entered.
                # We can calculate the vertices of the 'end' hex that face the 'start' hex.
                
                # Calculate angle from end to start (to find the entry side)
                angle_to_start = math.atan2(start_y - end_y, start_x - end_x)
                # Snap to nearest 60 degrees (hex sides)
                # Hex sides are at 30, 90, 150, 210, 270, 330 degrees (if flat top?) 
                # or 0, 60, 120... (if pointy top).
                # Our hex_corners function starts at angle_deg=30 for i=0. So pointy top?
                # Let's check hex_corners in hex_coord.py if needed, but assuming standard layout:
                # We want the vertices closest to the start point.
                
                # Simple approach: Find the two vertices of 'end' hex that are closest to 'start' center.
                end_corners = hex_corners(end_x, end_y, self.hex_size)
                # Sort corners by distance to start_x, start_y
                end_corners.sort(key=lambda p: (p[0]-start_x)**2 + (p[1]-start_y)**2)
                
                # The two closest corners form the entry edge
                c1 = end_corners[0]
                c2 = end_corners[1]
                
                # Draw a glowing line on this edge
                pygame.draw.line(self.screen, color, c1, c2, 4)
                # ---------------------------------------------------
                
                # Draw arrowhead or exit marker
                if is_exit:
                    # Draw a small "burst" or circle at the end to show exit
                    pygame.draw.circle(self.screen, color, (int(ex), int(ey)), thickness + 2)
                    # Maybe a small perpendicular line?
                    p_len = 6
                    pygame.draw.line(self.screen, (255, 255, 255), 
                                     (ex - px * p_len, ey - py * p_len), 
                                     (ex + px * p_len, ey + py * p_len), 2)
                    
                    # NEW: Draw Input Indicator on the receiving hex edge
                    # We know 'end' is the exit hex (Weapon Mount).
                    # We know 'start' is where it came from.
                    # We want to draw a small chevron on the edge between start and end.
                    
                    # Calculate edge midpoint
                    edge_mid_x = (start_x + end_x) / 2
                    edge_mid_y = (start_y + end_y) / 2
                    
                    # Move slightly towards end hex to be "inside" the target
                    indicator_offset = self.hex_size * 0.4
                    ind_x = edge_mid_x + ux * indicator_offset
                    ind_y = edge_mid_y + uy * indicator_offset
                    
                    # Draw chevron pointing IN to the end hex
                    # Vector is (ux, uy). Perpendicular is (px, py).
                    chev_size = 5
                    p1 = (ind_x - ux * chev_size + px * chev_size, ind_y - uy * chev_size + py * chev_size)
                    p2 = (ind_x, ind_y)
                    p3 = (ind_x - ux * chev_size - px * chev_size, ind_y - uy * chev_size - py * chev_size)
                    
                    pygame.draw.lines(self.screen, (255, 255, 255), False, [p1, p2, p3], 2)

                else:
                    # Draw small arrowhead at 2/3 distance
                    arrow_pos_x = sx + (ex - sx) * 0.66
                    arrow_pos_y = sy + (ey - sy) * 0.66
                    pygame.draw.circle(self.screen, color, (int(arrow_pos_x), int(arrow_pos_y)), thickness)

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

