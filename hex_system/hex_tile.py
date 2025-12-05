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

    def to_dict(self) -> dict:
        return {
            "class_name": self.__class__.__name__,
            "tile_type": self.tile_type,
            "category": self.category.value,
            "level": self.level,
            "name": self.name,
            "description": self.description,
            "base_color": self.base_color,
            "glow_color": self.glow_color,
            "merge_count": self.merge_count,
            "merge_bonus": self.merge_bonus
        }

    @staticmethod
    def from_dict(data: dict) -> 'HexTile':
        class_name = data.get("class_name", "HexTile")
        
        # Dispatch based on class name
        cls = HexTile
        if class_name == "BasicConduitTile": cls = BasicConduitTile
        elif class_name == "AmplifierTile": cls = AmplifierTile
        elif class_name == "ResonatorTile": cls = ResonatorTile
        elif class_name == "SplitterTile": cls = SplitterTile
        elif class_name == "WeaponMountTile": cls = WeaponMountTile
        elif class_name == "ReflectorTile": cls = ReflectorTile
        elif class_name == "FilterTile": cls = FilterTile
        elif class_name == "ReactorTile": cls = ReactorTile
        
        # Create instance
        instance = cls()
        
        # Restore base fields
        instance.tile_type = data.get("tile_type", instance.tile_type)
        try:
            instance.category = TileCategory(data.get("category", "special"))
        except ValueError:
            pass
            
        instance.level = data.get("level", 1)
        instance.name = data.get("name", "")
        instance.description = data.get("description", "")
        instance.base_color = tuple(data.get("base_color", (100, 100, 100)))
        if data.get("glow_color"):
            instance.glow_color = tuple(data["glow_color"])
        instance.merge_count = data.get("merge_count", 0)
        instance.merge_bonus = data.get("merge_bonus", 0.0)
        
        # Restore subclass specific fields
        instance.restore_from_dict(data)
        
        return instance

    def restore_from_dict(self, data: dict):
        """Override in subclasses to restore specific fields."""
        pass

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

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["exit_direction"] = self.exit_direction
        return d

    def restore_from_dict(self, data: dict):
        self.exit_direction = data.get("exit_direction", 0)

@dataclass
class AmplifierTile(BasicConduitTile):
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
        # Call BasicConduitTile post_init to set up defaults if needed (though we overwrote most)
        # Actually BasicConduitTile.__post_init__ sets tile_type to "Conduit", we want "Amplifier"
        # So we should call HexTile.__post_init__? 
        # No, we should just let it be.
        # But BasicConduitTile doesn't have much in post_init except setting type/color.
        # We overwrote those.
        # So we can just call super().__post_init__() which goes to BasicConduitTile -> HexTile.
        super().__post_init__()
        # Restore our type and color in case super overwrote it
        self.tile_type = "Amplifier"
        self.base_color = (255, 200, 100)

    def process_energy(self, context: 'ProjectileContext', from_direction: int) -> List['ProjectileContext']:
        # Call super to handle merge bonus!
        contexts = super().process_energy(context, from_direction)
        context = contexts[0]
        
        from .energy_packet import ProjectileModifier
        
        total_amp = self.amplification + self.merge_bonus
        
        context.add_modifier(ProjectileModifier(
            stat="damage",
            value=total_amp,
            operation="multiply"
        ))
        
        # Apply Synergies
        for synergy in self.synergies:
            # Add synergy magnitude. 
            # Amount? Maybe proportional to amplification? or fixed?
            # Let's add a fixed amount for now, e.g. 20.0
            context.add_synergy(synergy, 20.0)
            
        return [context]

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["amplification"] = self.amplification
        d["synergies"] = [s.value for s in self.synergies]
        return d

    def restore_from_dict(self, data: dict):
        super().restore_from_dict(data)
        self.amplification = data.get("amplification", 1.2)
        from .energy_packet import SynergyType
        self.synergies = [SynergyType(s) for s in data.get("synergies", [])]

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
        
    def process_energy(self, context: 'ProjectileContext', from_direction: int) -> List['ProjectileContext']:
        # Resonators add their synergy to the context
        for synergy in self.synergies:
            context.add_synergy(synergy, 20.0)
            
        # Interaction Buff: If context has multiple synergies, amplify damage
        # This simulates "interacting streams" getting a bonus
        if len(context.synergies) > 1:
             from .energy_packet import ProjectileModifier
             context.add_modifier(ProjectileModifier(stat="damage", value=1.1, operation="multiply"))
             
        return [context]

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["synergies"] = [s.value for s in self.synergies]
        return d

    def restore_from_dict(self, data: dict):
        from .energy_packet import SynergyType
        self.synergies = [SynergyType(s) for s in data.get("synergies", [])]

@dataclass
class SplitterTile(HexTile):
    split_count: int = 2
    exit_directions: List[int] = field(default_factory=lambda: [1, 5]) # Default NE and SE
    
    def __post_init__(self):
        self.tile_type = "Splitter"
        self.category = TileCategory.ROUTER
        self.base_color = (150, 200, 150)
        super().__post_init__()
    
    def process_energy(self, context: 'ProjectileContext', from_direction: int) -> List['ProjectileContext']:
        # Splitter creates clones for all paths
        # We need to return as many contexts as we have exit directions
        
        num_exits = len(self.exit_directions)
        if num_exits == 0:
            return []
            
        # Calculate split penalty/division
        # If we have N exits, do we divide damage by N?
        # User wants "5 particles for 5 streams".
        # If we divide by 5, each is weak.
        # But merge bonus helps.
        # Let's keep the logic: 0.5 base penalty, improved by merge.
        # But if N > 2, maybe we should scale it?
        # Let's stick to the previous formula for now, but maybe cap it?
        # split_penalty = 0.5 + (self.merge_bonus * 0.5)
        
        # Actually, if we split 6 ways, 0.5 damage each is 3.0x total damage. That's OP.
        # We should probably divide by (N/2) or something?
        # Or just let it be OP for now. It's a "Legendary" mechanic.
        
        split_penalty = 0.5 + (self.merge_bonus * 0.5)
        split_penalty = min(1.0, split_penalty)
        
        # If more than 2 exits, maybe reduce further?
        # e.g. if 6 exits, 0.5 * 6 = 3.0.
        # If we want to conserve energy, it should be 1/N.
        # But "Splitter" usually implies some multiplication/efficiency gain in these games.
        # Let's leave it as is.
        
        from .energy_packet import ProjectileModifier
        mod = ProjectileModifier(stat="damage", value=split_penalty, operation="multiply")
        
        results = []
        for _ in range(num_exits):
            new_ctx = context.clone()
            new_ctx.add_modifier(mod)
            results.append(new_ctx)
        
        return results
    
    def get_exit_directions(self, entry_direction: int) -> List[int]:
        """Returns configured exit directions."""
        return self.exit_directions
    
    def set_exit_direction(self, index: int, direction: int):
        """Legacy support / Set specific index."""
        # Ensure list is long enough
        while len(self.exit_directions) <= index:
            self.exit_directions.append(0)
        self.exit_directions[index] = direction % 6

    def toggle_exit_direction(self, direction: int):
        """Toggles a specific exit direction on/off."""
        direction = direction % 6
        if direction in self.exit_directions:
            self.exit_directions.remove(direction)
        else:
            self.exit_directions.append(direction)
            self.exit_directions.sort() # Keep sorted for consistency

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["split_count"] = len(self.exit_directions)
        d["exit_directions"] = self.exit_directions
        return d

    def restore_from_dict(self, data: dict):
        self.split_count = data.get("split_count", 2)
        # Handle legacy format if needed
        if "exit_directions" in data:
            self.exit_directions = data["exit_directions"]
        else:
            # Legacy fallback
            d1 = data.get("exit_direction_1", 1)
            d2 = data.get("exit_direction_2", 5)
            self.exit_directions = [d1, d2]

@dataclass
class WeaponMountTile(HexTile):
    weapon_type: str = "generic"
    def __post_init__(self):
        self.tile_type = "Weapon Mount"
        self.category = TileCategory.OUTPUT
        self.base_color = (255, 100, 100)
        super().__post_init__()
    def process_energy(self, context: 'ProjectileContext', from_direction: int) -> List['ProjectileContext']:
        # Pass through so simulate_flow can detect it exiting the component
        return [context]

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["weapon_type"] = self.weapon_type
        return d

    def restore_from_dict(self, data: dict):
        self.weapon_type = data.get("weapon_type", "generic")

@dataclass
class ReflectorTile(HexTile):
    target_synergy: str = "fire" # Configurable target to pass through
    reflection_offset: int = 1   # Direction offset for reflected energy (relative to straight exit)
    
    def __post_init__(self):
        self.tile_type = "Reflector"
        self.category = TileCategory.ROUTER
        self.base_color = (200, 200, 255) # Mirror-ish
        super().__post_init__()
        
    def process_energy(self, context: 'ProjectileContext', from_direction: int) -> List['ProjectileContext']:
        # Split context based on target synergy
        pass_context = context.clone()
        reflect_context = context.clone()
        
        # Filter pass_context to ONLY have target_synergy
        # Handle Enum string conversion (e.g. "SynergyType.FIRE" -> "fire")
        pass_context.synergies = {
            k: v for k, v in context.synergies.items() 
            if str(k).lower().split('.')[-1] == self.target_synergy.lower()
        }
        
        # Filter reflect_context to have everything ELSE
        reflect_context.synergies = {
            k: v for k, v in context.synergies.items() 
            if str(k).lower().split('.')[-1] != self.target_synergy.lower()
        }
        
        # We must return two contexts to match the two exit directions
        return [pass_context, reflect_context]

    def get_exit_directions(self, entry_direction: int) -> List[int]:
        straight = (entry_direction + 3) % 6
        reflected = (straight + self.reflection_offset) % 6
        return [straight, reflected]

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["target_synergy"] = self.target_synergy
        d["reflection_offset"] = self.reflection_offset
        return d

    def restore_from_dict(self, data: dict):
        self.target_synergy = data.get("target_synergy", "fire")
        self.reflection_offset = data.get("reflection_offset", 1)

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


