# pixbots_enhanced/equipment/component.py
# UPDATED to fix the TypeError on WeaponMountTile creation.

from dataclasses import dataclass, field
from typing import Dict, Optional
from hex_system.hex_coord import HexCoord
# FIX: Import TileCategory to be used when creating tiles
from hex_system.hex_tile import HexTile, AmplifierTile, ResonatorTile, SplitterTile, WeaponMountTile, TileCategory
from hex_system.energy_packet import SynergyType, EnergyCore
from systems.synergy_manager import SynergyManager

from systems.graphics_engine import ProceduralGenerator

@dataclass
class ComponentEquipment:
    """A body part component that can be equipped and contains a tile grid."""
    name: str
    slot: str
    quality: str = "Common"
    level: int = 1
    grid_width: int = 3
    grid_height: int = 3
    tile_slots: Dict[HexCoord, HexTile] = field(default_factory=dict)
    base_armor: int = 0
    base_hp: int = 0
    base_speed: float = 0.0
    core: Optional[EnergyCore] = None
    max_tile_capacity: int = 9
    merge_count: int = 0
    background_image: Optional[object] = None # pygame.Surface, but avoid type hint issue if pygame not imported here

    def __post_init__(self):
        quality_sizes = {
            "Common": (3, 3, 9), "Uncommon": (3, 4, 12), "Rare": (4, 4, 16),
            "Epic": (4, 5, 20), "Legendary": (5, 5, 25)
        }
        if self.quality in quality_sizes:
            self.grid_width, self.grid_height, self.max_tile_capacity = quality_sizes[self.quality]
            
        # Procedural Visuals
        # Determine type from slot or stats (simple heuristic)
        item_type = "utility"
        if "damage" in self.name.lower() or "gun" in self.name.lower() or "sword" in self.name.lower(): 
            item_type = "weapon"
        elif "shield" in self.name.lower() or "armor" in self.name.lower(): 
            item_type = "shield"
        
        # We need to handle the case where pygame display isn't init, but Surface creation usually works.
        # If it fails, we catch it or let it be None.
        try:
            self.background_image = ProceduralGenerator.generate_hex_background(item_type, self.quality)
        except Exception:
            self.background_image = None



    def place_tile(self, coord: HexCoord, tile: HexTile) -> bool:
        self.tile_slots[coord] = tile
        return True

    def get_entry_exit_hexes(self):
        """Returns ONE specific entry hex and ONE specific exit hex."""
        mid_q = self.grid_width // 2
        mid_r = self.grid_height // 2
        
        entry_hex = None
        exit_hex = None
        
        if self.slot == "torso":
            # Torso special case: reactor is source, multiple exits
            entry_hex = None  # Reactor core is the entry
            exit_hex = None   # Multiple exit directions
        elif self.slot == "left_arm":
            # Entry from torso (right side), exit to weapon (left side)
            entry_hex = HexCoord(self.grid_width - 1, mid_r)
            exit_hex = HexCoord(0, mid_r)
        elif self.slot == "right_arm":
            # Entry from torso (left side), exit to weapon (right side)
            entry_hex = HexCoord(0, mid_r)
            exit_hex = HexCoord(self.grid_width - 1, mid_r)
        elif self.slot in ["left_leg", "right_leg"]:
            # Entry from top (torso), exit to bottom (jump jet)
            entry_hex = HexCoord(mid_q, 0)
            exit_hex = HexCoord(mid_q, self.grid_height - 1)
        elif self.slot == "head":
            # Entry from bottom (torso), exit to top (focus beam/sensor)
            entry_hex = HexCoord(mid_q, self.grid_height - 1)
            exit_hex = HexCoord(mid_q, 0)
        elif self.slot == "back":
            # Entry from left (torso), exit to right (shield projection)
            entry_hex = HexCoord(0, mid_r)
            exit_hex = HexCoord(self.grid_width - 1, mid_r)
        
        return entry_hex, exit_hex

    def _is_in_bounds(self, coord: HexCoord) -> bool:
        return (0 <= coord.q < self.grid_width and 
                0 <= coord.r < self.grid_height)

    def _get_neighbor_in_direction(self, coord: HexCoord, direction: int) -> HexCoord:
        offsets = [
            (1, 0),    # 0: E
            (1, -1),   # 1: NE
            (0, -1),   # 2: NW
            (-1, 0),   # 3: W
            (-1, 1),   # 4: SW
            (0, 1),    # 5: SE
        ]
        dq, dr = offsets[direction % 6]
        return HexCoord(coord.q + dq, coord.r + dr)

    def simulate_flow(self):
        """
        Simulates energy flow through the component.
        Returns:
            flows: List of (start, end, color) tuples for visualization.
            stats: Dictionary of calculated stats based on the flow.
        """
        from hex_system.energy_packet import SynergyType, ProjectileContext
        
        flows = []
        stats = {
            "damage_multiplier": 1.0,
            "synergies": set(),
            "active_synergy_result": None,
            "weapon_damage": 0.0,
            "active_tiles": 0
        }
        
        synergy_manager = SynergyManager()
        
        entry_hex, exit_hex = self.get_entry_exit_hexes()
        
        # Initial context setup
        start_contexts = []
        
        if self.slot == "torso":
            if self.core and self.core.position:
                reactor_pos = self.core.position
                # Use generate_context instead of generate_packet
                context = self.core.generate_context()
                dominant_synergy = context.get_dominant_synergy()
                
                # Determine color based on synergy
                # Simple mapping for now, could be moved to a helper
                synergy_colors = {
                    SynergyType.FIRE: (255, 100, 50),
                    SynergyType.ICE: (100, 200, 255),
                    SynergyType.RAW: (200, 200, 200)
                }
                color = synergy_colors.get(dominant_synergy, (200, 200, 200))
                
                for direction in range(6):
                    next_coord = self._get_neighbor_in_direction(reactor_pos, direction)
                    if self._is_in_bounds(next_coord):
                        flows.append((reactor_pos, next_coord, color))
                        entry_direction = (direction + 3) % 6
                        start_contexts.append((next_coord, entry_direction, context))
        else:
            if entry_hex and self._is_in_bounds(entry_hex):
                # Default context for non-torso parts
                context = ProjectileContext()
                color = (200, 200, 200) # Raw energy color
                
                for direction in range(6):
                    next_coord = self._get_neighbor_in_direction(entry_hex, direction)
                    if self._is_in_bounds(next_coord) and next_coord in self.tile_slots:
                        flows.append((entry_hex, next_coord, color))
                        entry_direction = (direction + 3) % 6
                        start_contexts.append((next_coord, entry_direction, context))

        # Trace paths
        # We need to handle branching, so we use a queue instead of recursion to avoid depth issues
        # and better handle the state explosion if we have many splitters.
        queue = []
        for start_coord, start_entry, start_context in start_contexts:
            queue.append((start_coord, start_entry, start_context, 0)) # 0 is depth
            
        visited_states = set() # (coord, entry_dir) to prevent infinite loops
        
        while queue:
            coord, entry_dir, context, depth = queue.pop(0)
            
            if depth > 20: continue
            if (coord, entry_dir) in visited_states: continue
            
            if not self._is_in_bounds(coord): continue
            
            tile = self.tile_slots.get(coord)
            if not tile: continue
            
            visited_states.add((coord, entry_dir))
            stats["active_tiles"] += 1
            
            # Process tile effects
            # This returns a LIST of contexts (1 or more)
            next_contexts = tile.process_energy(context, entry_dir)
            
            # Determine flow color for this step
            dom_syn = context.get_dominant_synergy()
            synergy_colors = {
                SynergyType.FIRE: (255, 100, 50),
                SynergyType.ICE: (100, 200, 255),
                SynergyType.RAW: (200, 200, 200)
            }
            color = synergy_colors.get(dom_syn, (200, 200, 200))
            
            # Handle stats accumulation from the context
            # We take the MAX stats from any path to represent the "best" shot?
            # Or do we sum them?
            # For "weapon_damage", if we have multiple projectiles (splitters), we should probably sum the total damage output.
            
            # If we hit a weapon mount, we finalize this path
            if isinstance(tile, WeaponMountTile):
                # Calculate final synergy
                # Note: synergy_manager expects EnergyPacket, but we have ProjectileContext.
                # We might need to update SynergyManager or adapt the context.
                # For now, let's assume we can extract what we need.
                # Creating a dummy packet for compatibility if needed, or update SynergyManager later.
                # Let's just use the context's stats directly for now.
                
                final_mult = context.damage_multiplier
                stats["damage_multiplier"] = max(stats["damage_multiplier"], final_mult) # Track max multiplier seen
                
                # Add to total weapon damage (sum of all projectiles)
                # Base damage 10 * multiplier
                stats["weapon_damage"] += 10.0 * final_mult * context.projectile_count
                
                continue # End of this path
            
            # Continue flow for each resulting context
            # We need to match contexts to exit directions.
            # If Splitter, we have 2 contexts and 2 exit directions.
            # If normal tile, 1 context and 1 exit direction.
            
            if isinstance(tile, SplitterTile):
                exit_dirs = tile.get_exit_directions(entry_dir)
                # Assuming next_contexts has same length as exit_dirs
                for i, next_ctx in enumerate(next_contexts):
                    if i < len(exit_dirs):
                        exit_dir = exit_dirs[i]
                        next_coord = self._get_neighbor_in_direction(coord, exit_dir)
                        
                        # Visualize flow
                        flows.append((coord, next_coord, color))
                        
                        next_entry = (exit_dir + 3) % 6
                        queue.append((next_coord, next_entry, next_ctx, depth + 1))
            else:
                # Single exit
                exit_dir = tile.get_exit_direction(entry_dir)
                next_coord = self._get_neighbor_in_direction(coord, exit_dir)
                
                # Visualize flow
                flows.append((coord, next_coord, color))
                
                next_entry = (exit_dir + 3) % 6
                # Pass the first (and likely only) context
                if next_contexts:
                    queue.append((next_coord, next_entry, next_contexts[0], depth + 1))

        stats["synergies"] = list(stats["synergies"])
        return flows, stats

    def calculate_stats(self) -> dict:
        # Use the simulation to get accurate stats
        _, sim_stats = self.simulate_flow()
        
        stats = {
            "armor": self.base_armor, 
            "hp": self.base_hp, 
            "speed": self.base_speed,
            "damage_multiplier": sim_stats["damage_multiplier"], 
            "synergies": sim_stats["synergies"], 
            "active_synergy": sim_stats["active_synergy_result"].name if sim_stats["active_synergy_result"] else "None",
            "weapon_damage": sim_stats["weapon_damage"]
        }
        
        # Base weapon damage if no mount is connected but it's an arm (fallback)
        if self.slot in ["left_arm", "right_arm"] and stats["weapon_damage"] == 0:
             # Check if there is a weapon mount at all
             has_mount = any(isinstance(t, WeaponMountTile) for t in self.tile_slots.values())
             if has_mount:
                 # It's there but not connected? Give base damage.
                 stats["weapon_damage"] = 10.0
        
        # If we have a connected weapon, ensure it has at least base damage
        if self.slot in ["left_arm", "right_arm"] and stats["weapon_damage"] > 0:
             stats["weapon_damage"] = max(stats["weapon_damage"], 10.0)

        return stats
    
    def recalculate_stats(self):
        """A placeholder to indicate stats should be recalculated. The logic is in calculate_stats."""
        pass

    def get_total_power(self) -> float:
        stats = self.calculate_stats()
        return (
            stats["armor"] * 2 + stats["hp"] * 0.5 + stats["speed"] * 10 +
            stats["damage_multiplier"] * 50 + len(stats["synergies"]) * 20 +
            stats["weapon_damage"] * 0.5
        )

# --- Factory Functions ---

def create_starter_torso() -> ComponentEquipment:
    torso = ComponentEquipment(name="Basic Torso Mk I", slot="torso", quality="Common", base_armor=5, base_hp=50)
    torso.core = EnergyCore(core_type=SynergyType.FIRE, generation_rate=100.0, position=HexCoord(1, 1))
    
    # Place visual tile for the reactor
    from hex_system.hex_tile import ReactorTile
    torso.place_tile(HexCoord(1, 1), ReactorTile())
    
    return torso

def create_starter_arm(slot: str) -> ComponentEquipment:
    if slot not in ["left_arm", "right_arm"]:
        raise ValueError("Arm slot must be 'left_arm' or 'right_arm'")
    side = "Right" if "right" in slot else "Left"
    arm = ComponentEquipment(name=f"Basic {side} Arm", slot=slot, quality="Common", base_armor=2)
    
    # FIX: Correctly instantiate WeaponMountTile with the right arguments.
    weapon_mount = WeaponMountTile(tile_type="Weapon Mount", category=TileCategory.OUTPUT, weapon_type="beam")
    
    arm.place_tile(HexCoord(1, 1), weapon_mount)
    return arm

def create_starter_leg(slot: str) -> ComponentEquipment:
    if slot not in ["left_leg", "right_leg"]:
        raise ValueError("Leg slot must be 'left_leg' or 'right_leg'")
    side = "Right" if "right" in slot else "Left"
    leg = ComponentEquipment(name=f"Basic {side} Leg", slot=slot, quality="Common", base_speed=1.5)
    return leg

def create_starter_head() -> ComponentEquipment:
    head = ComponentEquipment(name="Basic Head", slot="head", quality="Common", base_armor=1)
    return head

def create_starter_back() -> ComponentEquipment:
    back = ComponentEquipment(name="Basic Back Unit", slot="back", quality="Common")
    return back

def create_random_component(rarity: str = "Common", slot: str = None) -> ComponentEquipment:
    import random
    slots = ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "back"]
    if slot is None:
        slot = random.choice(slots)
    
    base_armor = random.randint(1, 5)
    base_hp = random.randint(10, 50)
    base_speed = 0.0
    
    if rarity == "Uncommon":
        base_armor += 2
        base_hp += 20
    elif rarity == "Rare":
        base_armor += 5
        base_hp += 50
    elif rarity == "Epic":
        base_armor += 10
        base_hp += 100
    elif rarity == "Legendary":
        base_armor += 20
        base_hp += 200
        
    comp = ComponentEquipment(name=f"{rarity} {slot}", slot=slot, quality=rarity, base_armor=base_armor, base_hp=base_hp, base_speed=base_speed)
    
    # Ensure arms have a weapon mount
    if slot in ["left_arm", "right_arm"]:
        # 50% chance for weapon mount on random arms
        if random.random() < 0.5:
            from hex_system.hex_tile import WeaponMountTile, TileCategory
            mount = WeaponMountTile(tile_type="Weapon Mount", category=TileCategory.OUTPUT, weapon_type="beam")
            comp.place_tile(HexCoord(1, 1), mount)
            
    return comp
