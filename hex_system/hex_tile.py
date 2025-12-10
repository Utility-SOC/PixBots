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

class TargetSystem(Enum):
    SHIELD = "SHIELD"
    CLOAK = "CLOAK"
    ORBITAL = "ORBITAL"
    SUCM = "SUCM"
    ROCKET_LEGS = "ROCKET_LEGS"

class TriggerMode(Enum):
    TOGGLE = "TOGGLE"
    MOMENTARY = "MOMENTARY"

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

    def process_energy(self, context: 'ProjectileContext', from_direction: int, valid_exits: list = None) -> List['ProjectileContext']:
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
        elif class_name == "OrbitalModulatorTile": cls = OrbitalModulatorTile
        elif class_name == "DetonationTriggerTile": cls = DetonationTriggerTile
        elif class_name == "SecondaryOutputTile": cls = SecondaryOutputTile
        elif class_name == "ShieldGenTile": cls = ShieldGenTile
        elif class_name == "CloakTile": cls = CloakTile
        elif class_name == "AcceleratorTile": cls = AcceleratorTile
        elif class_name == "HipsTile": cls = HipsTile
        elif class_name == "KneesTile": cls = KneesTile
        elif class_name == "AnklesTile": cls = AnklesTile
        
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
    
    def process_energy(self, context: 'ProjectileContext', from_direction: int, valid_exits: list = None) -> List['ProjectileContext']:
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

    def process_energy(self, context: 'ProjectileContext', from_direction: int, valid_exits: list = None) -> List['ProjectileContext']:
        # Call super to handle merge bonus!
        contexts = super().process_energy(context, from_direction, valid_exits)
        context = contexts[0]
        
        from .energy_packet import ProjectileModifier
        
        total_amp = self.amplification + self.merge_bonus
        
        context.add_modifier(ProjectileModifier(
            stat="damage",
            value=total_amp,
            operation="multiply"
        ))
        
        # Apply Synergies PROPORTIONALLY
        current_mag = context.get_total_magnitude()
        for synergy in self.synergies:
            # Add 25% of current magnitude as the new synergy type
            # This ensures it scales with weapon power
            context.add_synergy(synergy, current_mag * 0.25)
            
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
        
    def process_energy(self, context: 'ProjectileContext', from_direction: int, valid_exits: list = None) -> List['ProjectileContext']:
        # Resonators add their synergy to the context PROPORTIONALLY
        current_mag = context.get_total_magnitude()
        for synergy in self.synergies:
             # Add 30% of current magnitude
            context.add_synergy(synergy, current_mag * 0.3)
            
        # Interaction Buff: If context has multiple synergies, amplify damage
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
    
    def process_energy(self, context: 'ProjectileContext', from_direction: int, valid_exits: list = None) -> List['ProjectileContext']:
        # R1: Smart Splitter Logic
        active_exits = self.exit_directions
        if valid_exits is not None:
             # Filter exits that are in our configured list AND are valid
             active_exits = [d for d in self.exit_directions if d in valid_exits]
        
        count = len(active_exits)
        if count == 0:
            return [] 
            
        results = []
        import copy
        
        # Smart Redistribution: 100% efficiency distributed among valid exits
        ratio = 1.0 / count
        
        for _ in range(count):
            new_ctx = copy.deepcopy(context)
            if new_ctx.damage_multiplier > 0:
                new_ctx.damage_multiplier *= ratio
            
            for k in new_ctx.synergies:
                new_ctx.synergies[k] *= ratio
            
            results.append(new_ctx)
        
        return results

    def get_active_exits(self, valid_exits: list = None) -> List[int]:
        if valid_exits is None: return self.exit_directions
        return [d for d in self.exit_directions if d in valid_exits]
    
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
    def process_energy(self, context: 'ProjectileContext', from_direction: int, valid_exits: list = None) -> List['ProjectileContext']:
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
        
    def process_energy(self, context: 'ProjectileContext', from_direction: int, valid_exits: list = None) -> List['ProjectileContext']:
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
    
    def process_energy(self, context: 'ProjectileContext', from_direction: int, valid_exits: list = None) -> List['ProjectileContext']:
        return [context]

@dataclass
class OrbitalModulatorTile(HexTile):
    orbit_radius: float = 0.5
    particle_ttl: float = 3.0
    orbit_speed: float = 1.0

    def __post_init__(self):
        self.tile_type = "Orbital Modulator"
        self.category = TileCategory.PROCESSOR
        self.base_color = (100, 255, 255) # Cyan-ish
        super().__post_init__()

    def process_energy(self, context: 'ProjectileContext', from_direction: int, valid_exits: list = None) -> List['ProjectileContext']:
        # S5: Add orbital configuration
        context.custom_effects["orbital_config"] = {
            "radius": self.orbit_radius * 100.0, # Convert internal unit to pixels if needed, or assume scaling
            "speed": self.orbit_speed,
            "ttl": self.particle_ttl,
            "period": 0.0 # calculated elsewhere
        }
        return [context]

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["orbit_radius"] = self.orbit_radius
        d["particle_ttl"] = self.particle_ttl
        d["orbit_speed"] = self.orbit_speed
        return d

    def restore_from_dict(self, data: dict):
        self.orbit_radius = data.get("orbit_radius", 0.5)
        self.particle_ttl = data.get("particle_ttl", 3.0)
        self.orbit_speed = data.get("orbit_speed", 1.0)

@dataclass
class DetonationTriggerTile(HexTile):
    trigger_time: float = 1.0

    def __post_init__(self):
        self.tile_type = "Detonation Trigger"
        self.category = TileCategory.PROCESSOR
        self.base_color = (255, 150, 50) # Orange
        super().__post_init__()

    def process_energy(self, context: 'ProjectileContext', from_direction: int, valid_exits: list = None) -> List['ProjectileContext']:
        # S4: Add detonation timer
        context.custom_effects["detonation_time"] = self.trigger_time
        return [context]

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["trigger_time"] = self.trigger_time
        return d

    def restore_from_dict(self, data: dict):
        self.trigger_time = data.get("trigger_time", 1.0)

@dataclass
class SecondaryOutputTile(HexTile):
    target_system: TargetSystem = TargetSystem.SHIELD
    trigger_mode: TriggerMode = TriggerMode.MOMENTARY

    def __post_init__(self):
        self.tile_type = "Secondary Output"
        self.category = TileCategory.OUTPUT
        self.base_color = (50, 50, 200) # Dark Blue
        super().__post_init__()

    def process_energy(self, context: 'ProjectileContext', from_direction: int, valid_exits: list = None) -> List['ProjectileContext']:
        # Secondary Systems consume ~80% of energy passing through them for activation.
        # The remaining 20% continues flow.
        
        consumption_rate = 0.8
        
        # Create output context (the flow continuing downstream)
        # Use clone() as copy() might not be detected in some load states
        out_context = context.clone()
        
        # Scale down output synergies
        for s in out_context.synergies:
            out_context.synergies[s] *= (1.0 - consumption_rate)
            
        # Record consumed energy in the output context's custom effects
        # This allows component.py to read "consumed_energy" and apply it to the system.
        consumed_mag = context.get_total_magnitude() * consumption_rate
        
        if not hasattr(out_context, "custom_effects"):
            out_context.custom_effects = {}
            
        out_context.custom_effects[f"system_{self.target_system.value}_charge"] = consumed_mag
        
        return [out_context]

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["target_system"] = self.target_system.value
        d["trigger_mode"] = self.trigger_mode.value
        return d

    def restore_from_dict(self, data: dict):
        try:
            self.target_system = TargetSystem(data.get("target_system", "SHIELD"))
        except ValueError:
            self.target_system = TargetSystem.SHIELD
            
        try:
            self.trigger_mode = TriggerMode(data.get("trigger_mode", "MOMENTARY"))
        except ValueError:
            self.trigger_mode = TriggerMode.MOMENTARY



@dataclass
class ShieldGenTile(SecondaryOutputTile):
    """Activates Shield when powered."""
    def __post_init__(self):
        super().__post_init__()
        self.tile_type = "Shield Generator"
        self.name = "Shield" 
        self.description = "Generates a protective forcefield."
        self.target_system = TargetSystem.SHIELD
        self.base_color = (50, 50, 255) # Blue

@dataclass
class CloakTile(SecondaryOutputTile):
    """Activates Cloak when powered."""
    def __post_init__(self):
        super().__post_init__()
        self.tile_type = "Cloak Module"
        self.name = "Cloak"
        self.description = "Renders the bot invisible."
        self.target_system = TargetSystem.CLOAK
        self.base_color = (50, 50, 50) # Dark Grey

@dataclass
class AcceleratorTile(SecondaryOutputTile):
    """Activates Speed Boost when powered."""
    def __post_init__(self):
        super().__post_init__()
        self.tile_type = "Accelerator"
        self.name = "Boost"
        self.description = "Boosts movement speed temporarily."
        self.target_system = TargetSystem.ROCKET_LEGS # Maps to Rocket Legs logic
        self.base_color = (255, 50, 50) # Red

@dataclass
class HipsTile(HexTile):
    """Converts energy into Movement Speed."""
    efficiency: float = 1.0

    def __post_init__(self):
        self.tile_type = "Hips Joint"
        self.name = "Hips"
        self.description = "Converts energy into Movement Speed."
        self.category = TileCategory.OUTPUT
        self.base_color = (200, 200, 50) # Yellow-ish
        super().__post_init__()

    def process_energy(self, context: 'ProjectileContext', from_direction: int, valid_exits: list = None) -> List['ProjectileContext']:
        # Absorbs energy
        return []

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["efficiency"] = self.efficiency
        return d

    def restore_from_dict(self, data: dict):
        self.efficiency = data.get("efficiency", 1.0)

@dataclass
class KneesTile(HexTile):
    """Converts energy into Acceleration/Turn Speed."""
    efficiency: float = 1.0

    def __post_init__(self):
        self.tile_type = "Knee Servo"
        self.name = "Knees"
        self.description = "Converts energy into Turn Speed."
        self.category = TileCategory.OUTPUT
        self.base_color = (150, 100, 255) # Purple-ish
        super().__post_init__()

    def process_energy(self, context: 'ProjectileContext', from_direction: int, valid_exits: list = None) -> List['ProjectileContext']:
        return []

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["efficiency"] = self.efficiency
        return d

    def restore_from_dict(self, data: dict):
        self.efficiency = data.get("efficiency", 1.0)

@dataclass
class AnklesTile(HexTile):
    """Converts energy into Stability/Braking."""
    efficiency: float = 1.0

    def __post_init__(self):
        self.tile_type = "Ankle Pivot"
        self.name = "Ankles"
        self.description = "Converts energy into Stability/Braking."
        self.category = TileCategory.OUTPUT
        self.base_color = (50, 200, 200) # Cyan/Teal
        super().__post_init__()

    def process_energy(self, context: 'ProjectileContext', from_direction: int, valid_exits: list = None) -> List['ProjectileContext']:
        return []

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["efficiency"] = self.efficiency
        return d

    def restore_from_dict(self, data: dict):
        self.efficiency = data.get("efficiency", 1.0)
