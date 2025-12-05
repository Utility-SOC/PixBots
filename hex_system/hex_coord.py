# pixbots_enhanced/hex_system/hex_coord.py
# Source: Your provided hex_coord.py file
# Description: Full hexagonal coordinate system with math, pathfinding, and conversion utilities.

import math
from typing import List, Tuple, Optional
from dataclasses import dataclass

@dataclass(frozen=True)
class HexCoord:
    """Immutable hexagonal coordinate using axial system (q, r)."""
    q: int
    r: int

    def __add__(self, other):
        return HexCoord(self.q + other.q, self.r + other.r)

    def __sub__(self, other):
        return HexCoord(self.q - other.q, self.r - other.r)

    def to_cube(self) -> Tuple[int, int, int]:
        s = -self.q - self.r
        return (self.q, self.r, s)

    def distance(self, other: 'HexCoord') -> int:
        vec = self - other
        q, r, s = vec.to_cube()
        return (abs(q) + abs(r) + abs(s)) // 2

    def neighbors(self) -> List['HexCoord']:
        return [self + direction for direction in HEX_DIRECTIONS]

    def neighbor(self, direction: int) -> 'HexCoord':
        return self + HEX_DIRECTIONS[direction % 6]

    def to_dict(self) -> dict:
        return {"q": self.q, "r": self.r}

    @staticmethod
    def from_dict(data: dict) -> 'HexCoord':
        return HexCoord(data["q"], data["r"])

HEX_DIRECTIONS: List[HexCoord] = [
    HexCoord(1, 0), HexCoord(0, -1), HexCoord(-1, -1),
    HexCoord(-1, 0), HexCoord(0, 1), HexCoord(1, 1)
]

def hex_round(q_float: float, r_float: float) -> HexCoord:
    s_float = -q_float - r_float
    q, r, s = round(q_float), round(r_float), round(s_float)
    q_diff, r_diff, s_diff = abs(q - q_float), abs(r - r_float), abs(s - s_float)

    if q_diff > r_diff and q_diff > s_diff:
        q = -r - s
    elif r_diff > s_diff:
        r = -q - s
    
    return HexCoord(q, r)

def hex_to_pixel(hex_coord: HexCoord, size: float, flat_top: bool = False) -> Tuple[float, float]:
    q, r = hex_coord.q, hex_coord.r
    if flat_top:
        x = size * (3/2 * q)
        y = size * (math.sqrt(3)/2 * q + math.sqrt(3) * r)
    else:  # pointy-top
        x = size * (math.sqrt(3) * q + math.sqrt(3)/2 * r)
        y = size * (3/2 * r)
    return (x, y)

def pixel_to_hex(x: float, y: float, size: float, flat_top: bool = False) -> HexCoord:
    if flat_top:
        q = (2/3 * x) / size
        r = (-1/3 * x + math.sqrt(3)/3 * y) / size
    else:  # pointy-top
        q = (math.sqrt(3)/3 * x - 1/3 * y) / size
        r = (2/3 * y) / size
    return hex_round(q, r)

def hex_corners(center_x: float, center_y: float, size: float) -> List[Tuple[float, float]]:
    corners = []
    for i in range(6):
        angle_deg = 60 * i + 30 # 30 degree offset for pointy-top
        angle_rad = math.pi / 180 * angle_deg
        x = center_x + size * math.cos(angle_rad)
        y = center_y + size * math.sin(angle_rad)
        corners.append((x, y))
    return corners