# pixbots_enhanced/hex_system/energy_packet.py
# REFACTORED VERSION - ProjectileContext for Advanced Hex Mechanics

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import copy

from .hex_coord import HexCoord

class SynergyType(Enum):
    """Enumeration of all possible energy synergy types."""
    RAW = "raw"
    FIRE = "fire"
    ICE = "ice"
    LIGHTNING = "lightning"
    VORTEX = "vortex"
    POISON = "poison"
    EXPLOSION = "explosion"
    KINETIC = "kinetic"
    PIERCE = "pierce"
    VAMPIRIC = "vampiric"

@dataclass
class ProjectileModifier:
    """A modifier applied to the projectile context."""
    stat: str  # e.g., "damage", "speed", "split_count"
    value: float
    operation: str = "multiply"  # "multiply" or "add"

@dataclass
class ProjectileContext:
    """
    Represents the state of a projectile as it travels through the hex grid.
    Replaces the old EnergyPacket.
    """
    # Core Stats
    damage_multiplier: float = 1.0
    speed_multiplier: float = 1.0
    projectile_count: int = 1
    
    # Synergies
    synergies: Dict[SynergyType, float] = field(default_factory=dict)
    
    # Path History for Visuals
    path: List[HexCoord] = field(default_factory=list)
    path_colors: List[tuple] = field(default_factory=list) # Colors for each segment
    
    # State
    current_position: Optional[HexCoord] = None
    current_direction: int = 0
    is_active: bool = True
    
    # Modifiers applied during traversal
    modifiers: List[ProjectileModifier] = field(default_factory=list)

    def __post_init__(self):
        if not self.synergies:
            self.synergies = {SynergyType.RAW: 100.0}

    def add_modifier(self, modifier: ProjectileModifier):
        """Applies a modifier to the context."""
        self.modifiers.append(modifier)
        
        if modifier.operation == "multiply":
            if modifier.stat == "damage":
                self.damage_multiplier *= modifier.value
            elif modifier.stat == "speed":
                self.speed_multiplier *= modifier.value
        elif modifier.operation == "add":
            if modifier.stat == "projectile_count":
                self.projectile_count += int(modifier.value)
            elif modifier.stat == "damage":
                pass 

    def clone(self) -> 'ProjectileContext':
        """Creates a deep copy of the context (for splitters)."""
        return copy.deepcopy(self)

    def get_dominant_synergy(self) -> SynergyType:
        """Returns the synergy type with the highest magnitude."""
        if not self.synergies:
            return SynergyType.RAW
        return max(self.synergies.items(), key=lambda x: x[1])[0]

    def record_step(self, coord: HexCoord, color: tuple):
        """Records a step in the path."""
        self.path.append(coord)
        self.path_colors.append(color)
    
    # Compatibility methods for EnergyPacket interface
    def get_total_magnitude(self) -> float:
        return sum(self.synergies.values())
        
    @property
    def magnitude(self) -> float:
        return self.get_total_magnitude()

@dataclass
class EnergyCore:
    """The source of energy (Projectiles) within a torso component."""
    core_type: SynergyType
    generation_rate: float = 10.0
    position: Optional[HexCoord] = None
    synergy_outputs: Dict[SynergyType, float] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.synergy_outputs:
            self.synergy_outputs = {
                SynergyType.RAW: self.generation_rate * 0.5,
                SynergyType.FIRE: self.generation_rate * 0.3,
                SynergyType.ICE: self.generation_rate * 0.3,
                SynergyType.LIGHTNING: self.generation_rate * 0.3,
                SynergyType.VORTEX: self.generation_rate * 0.2,
                SynergyType.POISON: self.generation_rate * 0.2,
                SynergyType.EXPLOSION: self.generation_rate * 0.2,
                SynergyType.KINETIC: self.generation_rate * 0.4,
                SynergyType.PIERCE: self.generation_rate * 0.2,
                SynergyType.VAMPIRIC: self.generation_rate * 0.1,
            }
            if self.core_type in self.synergy_outputs:
                self.synergy_outputs[self.core_type] = self.generation_rate

    def generate_context(self) -> ProjectileContext:
        """Creates a new ProjectileContext from this reactor."""
        ctx = ProjectileContext(
            synergies=self.synergy_outputs.copy(),
            current_position=self.position
        )
        return ctx
    
    # Legacy support alias
    def generate_packet(self) -> ProjectileContext:
        return self.generate_context()
    
    def set_synergy_output(self, synergy_type: SynergyType, magnitude: float):
        """Adjusts the output magnitude for a specific synergy type."""
        self.synergy_outputs[synergy_type] = magnitude
    
    def get_dominant_synergy(self) -> SynergyType:
        """Returns the synergy type with the highest magnitude."""
        if not self.synergy_outputs:
            return self.core_type
        return max(self.synergy_outputs.items(), key=lambda x: x[1])[0]

# Compatibility Alias
EnergyPacket = ProjectileContext