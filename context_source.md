Module File: G:\work\pixelbots\hex_system\energy_packet.py
```python
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

```