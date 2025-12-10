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
    # Modifiers applied during traversal
    modifiers: List[ProjectileModifier] = field(default_factory=list)

    # Custom Effects (metadata for secondary systems)
    custom_effects: Dict[str, Any] = field(default_factory=dict)

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

    def add_synergy(self, synergy_type: SynergyType, magnitude: float):
        """Adds a synergy to the context."""
        if synergy_type in self.synergies:
            self.synergies[synergy_type] += magnitude
        else:
            self.synergies[synergy_type] = magnitude 

    def clone(self) -> 'ProjectileContext':
        """Creates a deep copy of the context (for splitters)."""
        return copy.deepcopy(self)

    def copy(self) -> 'ProjectileContext':
        """Alias for clone(), providing standard naming."""
        return self.clone()

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
    # Map of direction (0-5) to synergy mix. If empty, assumes omnidirectional.
    # Format: {direction_index: {SynergyType: magnitude}}
    directional_outputs: Dict[int, Dict[SynergyType, float]] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.synergy_outputs:
            self.synergy_outputs = {
                SynergyType.RAW: self.generation_rate * 0.5
            }
            if self.core_type in self.synergy_outputs:
                self.synergy_outputs[self.core_type] = self.generation_rate
            else:
                self.synergy_outputs[self.core_type] = self.generation_rate
        
        # Default to omnidirectional if not specified
        if not self.directional_outputs:
            self.configure_omnidirectional()

    def configure_omnidirectional(self):
        """Sets all 6 directions to output the base synergy mix."""
        # Divide total generation rate by 6? Or is generation_rate per side?
        # Usually generation_rate is total. So per side is rate/6.
        # But for simplicity, let's say the synergy_outputs dict represents the TOTAL output.
        # So we divide the values by 6 for each side.
        per_side_mix = {k: v / 6.0 for k, v in self.synergy_outputs.items()}
        for i in range(6):
            self.directional_outputs[i] = per_side_mix.copy()

    def configure_focused(self, direction: int):
        """Sets output only to the specified direction (0-5)."""
        self.directional_outputs.clear()
        self.directional_outputs[direction] = self.synergy_outputs.copy()
        
    def configure_custom(self, direction: int, mix: Dict[SynergyType, float]):
        """Sets a custom mix for a specific direction."""
        self.directional_outputs[direction] = mix

    def generate_context(self, direction: int = None) -> Optional[ProjectileContext]:
        """Creates a new ProjectileContext from this reactor for a specific direction."""
        if direction is not None:
            # If direction is specified, strictly use directional_outputs
            if direction in self.directional_outputs:
                mix = self.directional_outputs[direction]
            else:
                # Direction not configured -> No output
                return None
        else:
            # No direction specified -> Return total output (Legacy/Fallback)
            mix = self.synergy_outputs.copy()
            
        ctx = ProjectileContext(
            synergies=mix.copy(),
            current_position=self.position
        )
        return ctx
    
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

    def add_synergy(self, synergy_type: SynergyType, magnitude: float):
        """Adds a synergy to the context."""
        if synergy_type in self.synergies:
            self.synergies[synergy_type] += magnitude
        else:
            self.synergies[synergy_type] = magnitude 

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
    # Map of direction (0-5) to synergy mix. If empty, assumes omnidirectional.
    # Format: {direction_index: {SynergyType: magnitude}}
    directional_outputs: Dict[int, Dict[SynergyType, float]] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.synergy_outputs:
            self.synergy_outputs = {
                SynergyType.RAW: self.generation_rate * 0.5
            }
            if self.core_type in self.synergy_outputs:
                self.synergy_outputs[self.core_type] = self.generation_rate
            else:
                self.synergy_outputs[self.core_type] = self.generation_rate
        
        # Default to omnidirectional if not specified
        if not self.directional_outputs:
            self.configure_omnidirectional()

    def configure_omnidirectional(self):
        """Sets all 6 directions to output the base synergy mix."""
        # Divide total generation rate by 6? Or is generation_rate per side?
        # Usually generation_rate is total. So per side is rate/6.
        # But for simplicity, let's say the synergy_outputs dict represents the TOTAL output.
        # So we divide the values by 6 for each side.
        per_side_mix = {k: v / 6.0 for k, v in self.synergy_outputs.items()}
        for i in range(6):
            self.directional_outputs[i] = per_side_mix.copy()

    def configure_focused(self, direction: int):
        """Sets output only to the specified direction (0-5)."""
        self.directional_outputs.clear()
        self.directional_outputs[direction] = self.synergy_outputs.copy()
        
    def configure_custom(self, direction: int, mix: Dict[SynergyType, float]):
        """Sets a custom mix for a specific direction."""
        self.directional_outputs[direction] = mix

    def generate_context(self, direction: int = None) -> Optional[ProjectileContext]:
        """Creates a new ProjectileContext from this reactor for a specific direction."""
        if direction is not None:
            # If direction is specified, strictly use directional_outputs
            if direction in self.directional_outputs:
                mix = self.directional_outputs[direction]
            else:
                # Direction not configured -> No output
                return None
        else:
            # No direction specified -> Return total output (Legacy/Fallback)
            mix = self.synergy_outputs.copy()
            
        ctx = ProjectileContext(
            synergies=mix.copy(),
            current_position=self.position
        )
        return ctx
    
    def set_synergy_output(self, synergy_type: SynergyType, magnitude: float):
        """Adjusts the output magnitude for a specific synergy type."""
        self.synergy_outputs[synergy_type] = magnitude
        # Re-configure omnidirectional to propagate changes
        self.configure_omnidirectional()
    
    def get_dominant_synergy(self) -> SynergyType:
        """Returns the synergy type with the highest magnitude."""
        if not self.synergy_outputs:
            return self.core_type
        return max(self.synergy_outputs.items(), key=lambda x: x[1])[0]

    def to_dict(self) -> dict:
        return {
            "core_type": self.core_type.value,
            "generation_rate": self.generation_rate,
            "position": self.position.to_dict() if self.position else None,
            "synergy_outputs": {k.value: v for k, v in self.synergy_outputs.items()},
            "directional_outputs": {
                str(d): {k.value: v for k, v in mix.items()} 
                for d, mix in self.directional_outputs.items()
            }
        }

    @staticmethod
    def from_dict(data: dict) -> 'EnergyCore':
        core_type = SynergyType(data["core_type"])
        core = EnergyCore(
            core_type=core_type,
            generation_rate=data.get("generation_rate", 10.0),
            position=HexCoord.from_dict(data["position"]) if data.get("position") else None
        )
        
        if "synergy_outputs" in data:
            core.synergy_outputs = {SynergyType(k): v for k, v in data["synergy_outputs"].items()}
            
        if "directional_outputs" in data:
            core.directional_outputs = {}
            for d_str, mix_data in data["directional_outputs"].items():
                mix = {SynergyType(k): v for k, v in mix_data.items()}
                core.directional_outputs[int(d_str)] = mix
                
        return core

# Compatibility Alias
EnergyPacket = ProjectileContext