# pixbots_enhanced/hex_system/hex_tile.py
# Defines all tile types for the hex grid system.

from dataclasses import dataclass, field
from typing import Optional, List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .energy_packet import ProjectileContext, SynergyType, ProjectileModifier

class TileCategory(Enum):
    CONDUIT = "conduit"
    PROCESSOR = "processor"
    STORAGE = "storage"
    ROUTER = "router"
    CONVERTER = "converter"
    OUTPUT = "output"
    SPECIAL = "special"

@dataclass
class HexTile:
    tile_type: str = "Generic"
    category: TileCategory = TileCategory.SPECIAL
    level: int = 1
    name: str = ""
    description: str = ""
    base_color: tuple = (100, 100, 100)
    glow_color: Optional[tuple] = None
    
    # Merging Logic
    merge_count: int = 0
    merge_bonus: float = 0.0 # Cumulative bonus from merging (e.g. 0.01 = 1%)

    def __post_init__(self):
        if not self.name: self.name = self.tile_type

    def process_energy(self, context: 'ProjectileContext', from_direction: int) -> List['ProjectileContext']:
        """
        Processes the projectile context.
        Returns a list of contexts (usually just the modified original, but splitters return multiple).
        """
        # Base implementation just passes it through
        return [context]

    def get_exit_direction(self, entry_direction: int) -> int:
        return (entry_direction + 3) % 6

@dataclass
class AmplifierTile(HexTile):
    amplification: float = 1.2
    synergies: List['SynergyType'] = field(default_factory=list)

    def __post_init__(self):
        self.tile_type = "Amplifier"
        self.category = TileCategory.PROCESSOR
        self.base_color = (255, 200, 100)
        self.glow_color = (255, 255, 100)
        self.description = f"Amplifies energy by {int((self.amplification-1)*100)}%"
        if not self.synergies:
            from .energy_packet import SynergyType
            self.synergies = [SynergyType.FIRE]
        super().__post_init__()

    def process_energy(self, context: 'ProjectileContext', from_direction: int) -> List['ProjectileContext']:
        from .energy_packet import ProjectileModifier
        
        # Calculate total amplification including merge bonus
        # Each merge adds 1% efficiency to the amplification
        # e.g. base 1.2, merge_bonus 0.05 -> 1.2 + 0.05 = 1.25? 
        # Or 1.2 * (1 + 0.05)? Let's do additive to the multiplier for now as requested "1% increase in efficiency"
        
        total_amp = self.amplification + self.merge_bonus
        
        context.add_modifier(ProjectileModifier(
            stat="damage",
            value=total_amp,
            operation="multiply"
        ))
        return [context]

@dataclass
class ResonatorTile(HexTile):
    synergies: List['SynergyType'] = field(default_factory=list)
    def __post_init__(self):
        self.tile_type = "Resonator"
        self.category = TileCategory.PROCESSOR
        self.base_color = (180, 100, 200)
        if not self.synergies:
            from .energy_packet import SynergyType
            self.synergies = [SynergyType.ICE]
        super().__post_init__()

@dataclass
class SplitterTile(HexTile):
    split_count: int = 2
    exit_direction_1: int = 1  # First exit direction (configurable)
    exit_direction_2: int = 5  # Second exit direction (configurable)
    
    def __post_init__(self):
        self.tile_type = "Splitter"
        self.category = TileCategory.ROUTER
        self.base_color = (150, 200, 150)
        super().__post_init__()
    
    def process_energy(self, context: 'ProjectileContext', from_direction: int) -> List['ProjectileContext']:
        # Splitter creates a clone for the second path
        context1 = context
        context2 = context.clone()
        
        # Apply split penalty? Miner Gun Builder usually doesn't penalize damage on split, 
        # but sometimes does. Let's assume no penalty for now, just branching.
        # Or maybe we want to divide damage? "Splits the projectile" implies division.
        # The user said "passing through a splitter creates two bullets".
        # Usually that means 2 full bullets or 2 half-strength bullets.
        # Let's go with 2 full bullets for "fun" factor unless balanced otherwise.
        # Actually, let's add a modifier to halve damage to keep it sane, 
        # but allow merge bonus to mitigate this.
        
        split_penalty = 0.5 + (self.merge_bonus * 0.5) # Merging improves split efficiency
        split_penalty = min(1.0, split_penalty)
        
        from .energy_packet import ProjectileModifier
        mod = ProjectileModifier(stat="damage", value=split_penalty, operation="multiply")
        
        context1.add_modifier(mod)
        context2.add_modifier(mod)
        
        return [context1, context2]
    
    def get_exit_directions(self, entry_direction: int) -> List[int]:
        """Returns TWO exit directions for splitter."""
        return [self.exit_direction_1, self.exit_direction_2]
    
    def set_exit_direction(self, index: int, direction: int):
        """Set one of the two exit directions (index 0 or 1)."""
        if index == 0:
            self.exit_direction_1 = direction % 6
        elif index == 1:
            self.exit_direction_2 = direction % 6

@dataclass
class WeaponMountTile(HexTile):
    weapon_type: str = "generic"
    def __post_init__(self):
        self.tile_type = "Weapon Mount"
        self.category = TileCategory.OUTPUT
        self.base_color = (255, 100, 100)
        super().__post_init__()
    def process_energy(self, context: 'ProjectileContext', from_direction: int) -> List['ProjectileContext']:
        return [] # Consumes context (fires projectile)

@dataclass
class ReflectorTile(HexTile):
    rotation_steps: int = 1
    def __post_init__( self):
        self.tile_type = "Reflector"
        self.category = TileCategory.ROUTER
        super().__post_init__()
    def get_exit_direction(self, entry_direction: int) -> int:
        return (entry_direction + self.rotation_steps) % 6

@dataclass
class FilterTile(HexTile):
    def __post_init__(self):
        self.tile_type = "Filter"
        self.category = TileCategory.CONVERTER
        super().__post_init__()

@dataclass
class ReactorTile(HexTile):
    tile_type: str = "Reactor Core"
    category: TileCategory = TileCategory.SPECIAL
    
    def __post_init__(self):
        self.base_color = (255, 50, 50)
        self.glow_color = (255, 100, 100)
        self.description = "Generates energy. Source of power."
        super().__post_init__()
    
    def process_energy(self, context: 'ProjectileContext', from_direction: int) -> List['ProjectileContext']:
        return [context]

@dataclass
class BasicConduitTile(HexTile):
    exit_direction: int = 0 # Configurable exit direction
    
    def __post_init__(self):
        self.tile_type = "Conduit"
        self.category = TileCategory.CONDUIT
        self.base_color = (100, 100, 100)
        super().__post_init__()
        
    def get_exit_direction(self, entry_direction: int) -> int:
        return self.exit_direction
        
    def set_exit_direction(self, direction: int):
        self.exit_direction = direction % 6
    
    def process_energy(self, context: 'ProjectileContext', from_direction: int) -> List['ProjectileContext']:
        # Conduits can have a merge bonus too!
        if self.merge_bonus > 0:
             from .energy_packet import ProjectileModifier
             # "1% total bonus for all energy packets passing through"
             context.add_modifier(ProjectileModifier(
                 stat="damage", 
                 value=1.0 + self.merge_bonus, 
                 operation="multiply"
             ))
        return [context]
