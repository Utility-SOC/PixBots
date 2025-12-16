# pixbots_enhanced/equipment/component.py
# UPDATED to fix the TypeError on WeaponMountTile creation.

from dataclasses import dataclass, field
from typing import Dict, Optional
from hex_system.hex_coord import HexCoord
# FIX: Import TileCategory to be used when creating tiles
from hex_system.hex_tile import HexTile, AmplifierTile, ResonatorTile, SplitterTile, WeaponMountTile, TileCategory, SecondaryOutputTile, HipsTile, KneesTile, AnklesTile
from hex_system.energy_packet import SynergyType, EnergyCore
from systems.synergy_manager import SynergyManager

from systems.graphics_engine import ProceduralGenerator

@dataclass
class ComponentEquipment:
    """A body part component that can be equipped and contains a tile grid."""
    name: str
    slot: str
    quality: str = "Common"
    level: int = 0
    grid_width: int = 3
    grid_height: int = 3
    tile_slots: Dict[HexCoord, HexTile] = field(default_factory=dict)
    valid_coords: set[HexCoord] = field(default_factory=set) # Set of valid hex coordinates for this shape
    base_armor: int = 0
    base_hp: int = 0
    base_speed: float = 0.0
    core: Optional[EnergyCore] = None
    max_tile_capacity: int = 9
    max_tile_capacity: int = 9
    merge_count: int = 0
    background_image: Optional[object] = None 
    
    # R4: Accumulation
    stored_energy: float = 0.0
    accumulation_rate: float = 0.0 # Calculated per frame/update from flow 

    def __post_init__(self):
        # If valid_coords is empty, default to rectangular grid based on quality
        if not self.valid_coords:
            quality_sizes = {
                "Common": (3, 3), "Uncommon": (3, 4), "Rare": (4, 4),
                "Epic": (4, 5), "Legendary": (5, 5)
            }
            w, h = quality_sizes.get(self.quality, (3, 3))
            self.grid_width = w
            self.grid_height = h
            
            for q in range(w):
                for r in range(h):
                    self.valid_coords.add(HexCoord(q, r))
            
        self.max_tile_capacity = len(self.valid_coords)
            
        # Procedural Visuals
        item_type = "utility"
        if "damage" in self.name.lower() or "gun" in self.name.lower() or "sword" in self.name.lower(): 
            item_type = "weapon"
        elif "shield" in self.name.lower() or "armor" in self.name.lower(): 
            item_type = "shield"
        
        try:
            self.background_image = ProceduralGenerator.generate_hex_background(item_type, self.quality)
        except Exception:
            self.background_image = None

    def update(self, dt: float):
        """Update component state, primarily energy accumulation."""
        if self.accumulation_rate > 0:
            # Accumulate energy
            self.stored_energy += self.accumulation_rate * dt
            
            # Cap at some reasonable max (e.g. 10x generation rate or fixed 1000 * level)
            max_cap = 1000.0 * (1 + self.level)
            if self.stored_energy > max_cap:
                self.stored_energy = max_cap
    
    def consume_stored_energy(self, amount: Optional[float] = None) -> float:
        """
        Consumes stored energy. 
        If amount is None, consumes ALL and returns it (Discharge).
        If amount is specified, consumes up to amount and returns actual consumed.
        """
        if amount is None:
            # Discharge all
            v = self.stored_energy
            self.stored_energy = 0.0
            return v
        else:
            consumed = min(self.stored_energy, amount)
            self.stored_energy -= consumed
            return consumed

    def get_recycle_value(self) -> int:
        """Returns the number of shards obtained from recycling this item."""
        rarity_values = {
            "Common": 1, "Uncommon": 2, "Rare": 3, 
            "Epic": 4, "Legendary": 5
        }
        return rarity_values.get(self.quality, 1)

    def get_upgrade_cost(self) -> int:
        """Returns the shard cost to upgrade to the next level."""
        rarity_values = {
            "Common": 1, "Uncommon": 2, "Rare": 3, 
            "Epic": 4, "Legendary": 5
        }
        base_cost = rarity_values.get(self.quality, 1)
        return (self.level + 1) * base_cost

    def upgrade(self):
        """Increases the item level."""
        self.level += 1

    def place_tile(self, coord: HexCoord, tile: HexTile) -> bool:
        if coord in self.valid_coords:
            self.tile_slots[coord] = tile
            return True
        return False

    def get_entry_exit_hexes(self):
        """Returns ONE specific entry hex and ONE specific exit hex."""
        if not self.valid_coords: return None, None
        
        min_q = min(c.q for c in self.valid_coords)
        max_q = max(c.q for c in self.valid_coords)
        min_r = min(c.r for c in self.valid_coords)
        max_r = max(c.r for c in self.valid_coords)
        
        mid_r = (min_r + max_r) // 2
        mid_q = (min_q + max_q) // 2
        
        entry_hex = None
        exit_hex = None
        
        if self.slot == "torso":
            entry_hex = None
            exit_hex = None
        elif self.slot == "left_arm":
            # Entry from Torso (Right side of arm, max_q)
            # Exit at weapon mount (Left side of arm, min_q)
            entry_hex = min(self.valid_coords, key=lambda c: (abs(c.q - max_q) + abs(c.r - mid_r)))
            exit_hex = min(self.valid_coords, key=lambda c: (abs(c.q - min_q) + abs(c.r - mid_r)))
        elif self.slot == "right_arm":
            # Entry from Torso (Left side of arm, min_q)
            # Exit at weapon mount (Right side of arm, max_q)
            entry_hex = min(self.valid_coords, key=lambda c: (abs(c.q - min_q) + abs(c.r - mid_r)))
            exit_hex = min(self.valid_coords, key=lambda c: (abs(c.q - max_q) + abs(c.r - mid_r)))
        elif self.slot in ["left_leg", "right_leg", "legs"]:
            # Entry top (min_r), Exit bottom (max_r)
            entry_hex = min(self.valid_coords, key=lambda c: (abs(c.r - min_r) + abs(c.q - mid_q)))
            exit_hex = min(self.valid_coords, key=lambda c: (abs(c.r - max_r) + abs(c.q - mid_q)))
        elif self.slot == "head":
            # Entry bottom (max_r), Exit top (min_r)
            entry_hex = min(self.valid_coords, key=lambda c: (abs(c.r - max_r) + abs(c.q - mid_q)))
            exit_hex = min(self.valid_coords, key=lambda c: (abs(c.r - min_r) + abs(c.q - mid_q)))
        elif self.slot == "back":
            # Entry from Torso (Left side of back unit, max_q)
            # Exit at weapon mount (Right side of back unit, min_q)
            entry_hex = min(self.valid_coords, key=lambda c: (abs(c.q - max_q) + abs(c.r - mid_r)))
            exit_hex = min(self.valid_coords, key=lambda c: (abs(c.q - min_q) + abs(c.r - mid_r)))
        
        return entry_hex, exit_hex

    def _is_in_bounds(self, coord: HexCoord) -> bool:
        return coord in self.valid_coords

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

    def simulate_flow(self, input_context: Optional['ProjectileContext'] = None, input_direction: int = None):
        """
        Simulates energy flow through the component.
        Args:
            input_context: Optional context entering the component.
            input_direction: Direction FROM WHICH energy enters (0-5). 
                             e.g. if entering from Left, direction is 0 (East)? 
                             No, usually we use "entry_direction" as "side of tile entered".
                             If moving East (0), we enter the West side (3).
                             So input_direction should be the side of the entry hex we enter.
        """
        from hex_system.energy_packet import SynergyType, ProjectileContext
        import logging
        logger = logging.getLogger(__name__)
        
        flows = []
        stats = {
            "damage_multiplier": 1.0,
            "synergies": set(),
            "active_synergy_result": None,
            "active_synergy_effects": {},
            "weapon_damage": 0.0,
            "transfer_rate": 0.0, # New stat for transfer output
            "active_tiles": 0
        }
        exit_contexts = {} # For Transfer (Conduits, etc)
        weapon_exit_contexts = {} # For Actual Weapon Output 
        
        synergy_manager = SynergyManager()
        
        entry_hex, exit_hex = self.get_entry_exit_hexes()
        
        # Initial context setup
        start_contexts = [] # (coord, entry_dir, context)
        entry_direction = 0 # Default initialization
        
        if self.slot == "torso":
            # Fallback: If core position is missing, find the ReactorTile
            if self.core and not self.core.position:
                from hex_system.hex_tile import ReactorTile
                for coord, tile in self.tile_slots.items():
                    if isinstance(tile, ReactorTile):
                        self.core.position = coord
                        break
            
            if self.core and self.core.position:
                reactor_pos = self.core.position
                for direction in range(6):
                    context = self.core.generate_context(direction)
                    if context is None or context.get_total_magnitude() <= 0: continue
                    
                    next_coord = self._get_neighbor_in_direction(reactor_pos, direction)
                    if self._is_in_bounds(next_coord):
                        # Store the full synergy mix for visualization
                        flows.append((reactor_pos, next_coord, context.synergies.copy()))
                        entry_direction = (direction + 3) % 6
                        start_contexts.append((next_coord, entry_direction, context))
                    else:
                        exit_contexts[direction] = context
        
        elif input_context:
            # ROBUST ENTRY SCAN for Components
            # Instead of guessing one "center" hex, find ALL conduits on the interface edge.
            entry_coords = []
            
            if self.valid_coords:
                min_q = min(c.q for c in self.valid_coords)
                max_q = max(c.q for c in self.valid_coords)
                min_r = min(c.r for c in self.valid_coords)
                max_r = max(c.r for c in self.valid_coords)
                
                candidates = []
                
                # Identify Edge Candidates based on Slot
                if self.slot == "right_arm": # Input from West (Left side, min_q)
                    candidates = [c for c in self.valid_coords if c.q == min_q]
                elif self.slot == "left_arm": # Input from East (Right side, max_q)
                    candidates = [c for c in self.valid_coords if c.q == max_q]
                elif "leg" in self.slot: # Input from Top (min_r)
                    candidates = [c for c in self.valid_coords if c.r == min_r]
                elif self.slot == "head": # Input from Bottom (max_r)
                    candidates = [c for c in self.valid_coords if c.r == max_r]
                elif self.slot == "back": # Input from Right? (Checking get_entry_exit_hexes logic: max_q)
                    candidates = [c for c in self.valid_coords if c.q == max_q]
                
                # Filter candidates to find valid inputs
                from hex_system.hex_tile import TileCategory
                for c in candidates:
                    tile = self.tile_slots.get(c)
                    if tile and (getattr(tile, "category", None) in [TileCategory.CONDUIT, TileCategory.ROUTER] 
                                 or "conduit" in tile.tile_type.lower()
                                 or "conductor" in tile.tile_type.lower()):
                        entry_coords.append(c)
            
            # Fallback to legacy
            if not entry_coords and entry_hex:
                 entry_coords.append(entry_hex)

            # Initialize Queue with ALL found entries
            for e_hex in entry_coords:
                 if self._is_in_bounds(e_hex):
                    # Visual flow entering
                    prev_coord = self._get_neighbor_in_direction(e_hex, (input_direction + 3) % 6)
                    flows.append((prev_coord, e_hex, input_context.synergies.copy()))
                    
                    
                    start_contexts.append((e_hex, input_direction, input_context))

        # Process the flow queue
        queue = start_contexts # Rename for clarity
        processed_coords = set() 
        
        # VISITED STATE: Track (coord, entry_dir) to prevent infinite loops
        visited_states = set()
        
        steps = 0
        max_steps = 1000 # Safety Break
        
        max_damage_mult = 1.0
        
        while queue and steps < max_steps:
            steps += 1
            coord, entry_dir, context = queue.pop(0)
            
            # CYCLE DETECTION: If we've entered this tile from this direction before, stop.
            state_key = (coord, entry_dir)
            if state_key in visited_states:
                continue
            visited_states.add(state_key)
            
            if coord not in self.tile_slots:
                continue
                
            tile = self.tile_slots[coord]
            
            # Track active tiles (using a set to avoid double counting)
            if coord not in processed_coords:
                processed_coords.add(coord)
                stats["active_tiles"] += 1
            
            # Track max damage multiplier seen in the flow
            if context.damage_multiplier > max_damage_mult:
                max_damage_mult = context.damage_multiplier
            
            # R1: Smart Splitter Logic (DISABLED - Reverted to Dumb for predictability)
            valid_exits = None
            if tile.tile_type == "Splitter" and hasattr(tile, "exit_directions"):
                # Revert to simple behavior: Always use all configured exits.
                # This allows users to "eject" energy into empty tiles if they want.
                valid_exits = tile.exit_directions
                
                # Original Smart Logic (Commented out)
                # valid_exits = []
                # for d in tile.exit_directions:
                #     neighbor = self._get_neighbor_in_direction(coord, d)
                #     if not self._is_in_bounds(neighbor):
                #         valid_exits.append(d) # Transfer
                #     elif neighbor in self.tile_slots:
                #         valid_exits.append(d) # Valid internal connection
                
                # if not valid_exits:
                #      valid_exits = tile.exit_directions
                
                logger.info(f"DEBUG: Splitter at {coord} Exits: {tile.exit_directions} Valid: {valid_exits}")

            
            # --- PRE-EMPTIVE WEAPON CAPTURE ---
            # Detect weapon immediately to bypass potential flow processing glitches
            is_weapon = False
            if hasattr(tile, "weapon_type"): is_weapon = True
            elif tile.tile_type == "Weapon Mount": is_weapon = True
            elif "weapon" in tile.tile_type.lower() or "weapon" in tile.name.lower(): is_weapon = True
            else:
                try:
                    from hex_system.hex_tile import WeaponMountTile as WMT
                    if isinstance(tile, WMT): is_weapon = True
                except ImportError: pass
                
            if is_weapon:
                # Calculate exit direction (standard pass-through: entry + 3)
                exit_dir = (entry_dir + 3) % 6
                # print(f"DEBUG: Pre-emptive Capture at {coord}. ExitDir={exit_dir}")
                
                target_dict = weapon_exit_contexts
                if exit_dir in target_dict:
                     existing = target_dict[exit_dir]
                     for s, m in context.synergies.items():
                         existing.synergies[s] = existing.synergies.get(s, 0.0) + m
                     existing.damage_multiplier = max(existing.damage_multiplier, context.damage_multiplier)
                     if hasattr(context, "custom_effects"):
                         existing.custom_effects.update(context.custom_effects)
                else:
                    target_dict[exit_dir] = context
                    
                # Stop propagation for this beam
                continue 
            # ----------------------------------

            # Process energy through tile
            out_contexts = tile.process_energy(context, entry_dir, valid_exits=valid_exits)
            
            # Special handling for WeaponMountTile: It consumes energy to fire
            if isinstance(tile, WeaponMountTile):
                # Calculate damage for ALL processed contexts (usually just one)
                for out_ctx in out_contexts:
                    dmg_add = out_ctx.get_total_magnitude() * out_ctx.damage_multiplier
                    stats["weapon_damage"] += dmg_add
                    
                    # Track unique input directions
                    if "weapon_inputs" not in stats:
                        stats["weapon_inputs"] = set()
                    stats["weapon_inputs"].add(entry_dir)
                    
                    # Track synergy magnitudes for R3 (Kinetic Spread)
                    if "synergy_magnitudes" not in stats:
                         stats["synergy_magnitudes"] = {}
                    
                    for syn_type, mag in out_ctx.synergies.items():
                         key = syn_type.value
                         stats["synergy_magnitudes"][key] = stats["synergy_magnitudes"].get(key, 0.0) + mag
                    
                    # R4: Accumulation Rate (Energy reaching weapon = Charge Rate)
                    if "accumulation_rate" not in stats: stats["accumulation_rate"] = 0.0
                    stats["accumulation_rate"] += dmg_add # Start with dmg_add logic (base flow)
                    
                    # Calculate active synergy
                    stats["active_synergy_result"] = synergy_manager.calculate_synergy(out_ctx)
                    stats["active_synergy_effects"] = stats["active_synergy_result"].effects
                
                # Weapon Mounts consume energy, so we stop propagation here for logic
                continue

            # S7: Leg Sink Tiles
            if isinstance(tile, (HipsTile, KneesTile, AnklesTile)):
                 # Use INPUT context because Sinks absorb energy (no output)
                 magnitude = context.get_total_magnitude()
                 
                 if isinstance(tile, HipsTile):
                     stats["movement_speed_bonus"] = stats.get("movement_speed_bonus", 0.0) + magnitude * tile.efficiency
                 elif isinstance(tile, KneesTile):
                     stats["turn_speed_bonus"] = stats.get("turn_speed_bonus", 0.0) + magnitude * tile.efficiency
                 elif isinstance(tile, AnklesTile):
                     stats["stability_bonus"] = stats.get("stability_bonus", 0.0) + magnitude * tile.efficiency
                 
                 continue # Stop propagation

            else:
                if hasattr(tile, "get_active_exits"):
                    exit_dirs = tile.get_active_exits(valid_exits)
                elif hasattr(tile, "get_exit_directions"):
                    exit_dirs = tile.get_exit_directions(entry_dir)
                else:
                    exit_dirs = [tile.get_exit_direction(entry_dir)]
            

            
            for i, out_ctx in enumerate(out_contexts):
                if i >= len(exit_dirs): break
                exit_dir = exit_dirs[i]
                
                # Check max multiplier on output too
                if out_ctx.damage_multiplier > max_damage_mult:
                    max_damage_mult = out_ctx.damage_multiplier
                
                next_coord = self._get_neighbor_in_direction(coord, exit_dir)
                
                # Record flow for visualization
                flows.append((coord, next_coord, out_ctx.synergies.copy()))
                
                if self._is_in_bounds(next_coord):
                    next_entry_dir = (exit_dir + 3) % 6
                    queue.append((next_coord, next_entry_dir, out_ctx))
                else:
                    # Leaving component. Energy Transfer.
                    target_dict = exit_contexts
                    # Weapon Mounts handled above
                    
                    # Fix: Accumulate contexts instead of overwriting!
                    if exit_dir in target_dict:
                         # Merge logic: Add synergies, Max multiplier
                         existing = target_dict[exit_dir]
                         
                         # Sum synergies
                         for s, m in out_ctx.synergies.items():
                             existing.synergies[s] = existing.synergies.get(s, 0.0) + m
                             
                         # Maximize multipliers
                         existing.damage_multiplier = max(existing.damage_multiplier, out_ctx.damage_multiplier)
                         
                         # Merge custom effects
                         if hasattr(out_ctx, "custom_effects"):
                             if hasattr(existing, "custom_effects"):
                                 existing.custom_effects.update(out_ctx.custom_effects)
                             else:
                                 # Upgrade legacy object on the fly
                                 existing.custom_effects = out_ctx.custom_effects.copy()
                    else:
                        target_dict[exit_dir] = out_ctx

            # Accumulate synergies seen in this step
            for syn in context.synergies:
                if context.synergies[syn] > 0:
                    stats["synergies"].add(syn)
            for out_ctx in out_contexts:
                # Merge custom effects safely
                if hasattr(out_ctx, "custom_effects"):
                    stats["active_synergy_effects"].update(out_ctx.custom_effects)
                elif hasattr(out_ctx, "synergies"): # Fallback for malformed contexts
                     pass
                    
                for syn in out_ctx.synergies:
                    if out_ctx.synergies[syn] > 0:
                        stats["synergies"].add(syn)
            
            # --- AGGREGATE SECONDARY CHARGES ---
            # Extract "system_X_charge" from contexts and sum into stats
            if hasattr(context, "custom_effects"):
                for key, val in context.custom_effects.items():
                    if key.startswith("system_") and key.endswith("_charge"):
                         # Add to stats (e.g. stats["system_SHIELD_charge"] += 50.0)
                         stats[key] = stats.get(key, 0.0) + val
            
            for out_ctx in out_contexts:
                if hasattr(out_ctx, "custom_effects"):
                    for key, val in out_ctx.custom_effects.items():
                         if key.startswith("system_") and key.endswith("_charge"):
                              stats[key] = stats.get(key, 0.0) + val

        stats["synergies"] = list(stats["synergies"])
        
        # Populate weapon_inputs with ACTIVE WEAPON EXITS to trigger multishot in Player.shoot
        # (Player.shoot uses len(weapon_inputs) to determine spread count)
        if weapon_exit_contexts:
             stats["weapon_inputs"] = list(weapon_exit_contexts.keys())
        else:
             stats["weapon_inputs"] = []

        # Convert set to count for easier use
        stats["spread_count"] = len(stats.get("weapon_inputs", []))
        stats["damage_multiplier"] = max_damage_mult # Update stats with max seen
        
        # Calculate resulting active synergy from WEAPON contexts
        if weapon_exit_contexts:
            # Aggregate all weapon output synergies
            aggregated_synergies = {}
            for ctx in weapon_exit_contexts.values():
                for s, m in ctx.synergies.items():
                    aggregated_synergies[s] = aggregated_synergies.get(s, 0.0) + m
            
            # Store magnitudes for spread logic etc (Using weapon output for this)
            stats["synergy_magnitudes"] = {
                (k.value if hasattr(k, "value") else str(k)).lower(): v 
                for k, v in aggregated_synergies.items()
            }
            
            # Use SynergyManager to determine dominant effect
            from hex_system.energy_packet import ProjectileContext
            dummy_context = ProjectileContext(synergies=aggregated_synergies)
            syn_result = synergy_manager.calculate_synergy(dummy_context)
            
            stats["active_synergy_result"] = syn_result
            # Merge synergy-specific effects (e.g. burn chance, slow)
            stats["active_synergy_effects"].update(syn_result.effects)
            
            # CRITICAL FIX: Calculate weapon damage from total output magnitude
            # This ensures damage is actually reported and used by Player.shoot
            stats["weapon_damage"] = sum(aggregated_synergies.values())
            
        else:
             # If no weapon output, check Transfer Output for magnitudes 
             # (Allows Torso visualization to still work for transfer)
             if exit_contexts:
                aggregated_transfer = {}
                for ctx in exit_contexts.values():
                   for s, m in ctx.synergies.items():
                       aggregated_transfer[s] = aggregated_transfer.get(s, 0.0) + m
                
                stats["synergy_magnitudes"] = {
                    (k.value if hasattr(k, "value") else str(k)).lower(): v 
                    for k, v in aggregated_transfer.items()
                }
                
                # We calculate transfer rate
                stats["transfer_rate"] = sum(aggregated_transfer.values())
             else:
                stats["synergy_magnitudes"] = {}
             
             stats["weapon_damage"] = 0.0

        # --- Calculate Synergy Magnitudes from Weapon Inputs ---
        # REMOVED: This block was overwriting valid synergy magnitudes with empty data
        # because weapon_inputs contains directions (ints), not contexts.
        # stats["synergy_magnitudes"] is already correctly populated from weapon output above.


        # Populate active_synergy string for Player.shoot
        if stats["active_synergy_result"]:
            stats["active_synergy"] = stats["active_synergy_result"].name
        elif stats.get("synergy_magnitudes"): # Fallback for transfer visualization
             # Determine dominant transfer synergy
             best_syn = max(stats["synergy_magnitudes"].items(), key=lambda x: x[1])[0]
             stats["active_synergy"] = str(best_syn).split('.')[-1].lower()
        else:
            stats["active_synergy"] = None
        
        if input_context:
             import logging
             logger = logging.getLogger(__name__)
             logger.debug(f"Simulating {self.slot} with input context. Mag: {input_context.get_total_magnitude()}. Result Weapon Dmg: {stats['weapon_damage']}")
        
        # Persist stats for external access (e.g. by Player for secondary abilities)
        self.stats = stats
             
        return flows, stats, exit_contexts

    def calculate_stats(self) -> dict:
        # Use the simulation to get accurate stats
        # If this is a dependent component (Arm/Leg/Head) and we are just calculating stats
        # (likely for UI display), we need to simulate with a "Test" input to show potential.
        input_context = None
        input_dir = 0
        
        if self.slot != "torso":
            from hex_system.energy_packet import ProjectileContext, SynergyType
            # Default test input: 100 RAW energy
            input_context = ProjectileContext(synergies={SynergyType.RAW: 100.0})
            
            # Determine default input direction based on slot
            if self.slot == "right_arm":
                input_dir = 3 # Enters West side
            elif self.slot == "left_arm":
                input_dir = 0 # Enters East side
            elif self.slot == "head":
                input_dir = 4 # Enters Bottom-Left
            elif "leg" in self.slot:
                input_dir = 1 # Enters Top-Right
            elif self.slot == "back":
                input_dir = 0 # Enters East side
        
        _, sim_stats, _ = self.simulate_flow(input_context=input_context, input_direction=input_dir)
        
        # R4: Update Accumulation Rate from current potential
        self.accumulation_rate = sim_stats.get("accumulation_rate", 0.0)
        
        # Apply Level Bonus (+10% per level)
        level_mult = 1.0 + (self.level * 0.1)
        
        stats = {
            "armor": int(self.base_armor * level_mult), 
            "hp": int(self.base_hp * level_mult), 
            "speed": self.base_speed * level_mult,
            "damage_multiplier": sim_stats["damage_multiplier"] * level_mult,
            
            # S7: Pass through sink stats
            "movement_speed_bonus": sim_stats.get("movement_speed_bonus", 0.0),
            "turn_speed_bonus": sim_stats.get("turn_speed_bonus", 0.0),
            "stability_bonus": sim_stats.get("stability_bonus", 0.0), 
            "weapon_damage": sim_stats.get("weapon_damage", 0.0) * level_mult,
            "weapon_inputs": list(sim_stats.get("weapon_inputs", set())), # Convert set to list for JSON serialization if needed
            "active_tiles": sim_stats.get("active_tiles", 0),
            "synergies": sim_stats["synergies"], 
            "active_synergy": sim_stats["active_synergy_result"].name if sim_stats["active_synergy_result"] else "None",
            "quality": self.quality,
            "level": self.level,
            "grid_width": self.grid_width,
            "grid_height": self.grid_height,
            "valid_coords": [c.to_dict() for c in self.valid_coords],
            "tile_slots": {f"{c.q},{c.r}": t.to_dict() for c, t in self.tile_slots.items()},
            "base_armor": self.base_armor,
            "base_hp": self.base_hp,
            "base_speed": self.base_speed,
            "core": self.core.to_dict() if self.core else None,
            "merge_count": self.merge_count
        }
        return stats

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "slot": self.slot,
            "quality": self.quality,
            "level": self.level,
            "grid_width": self.grid_width,
            "grid_height": self.grid_height,
            "base_armor": self.base_armor,
            "base_hp": self.base_hp,
            "base_speed": self.base_speed,
            "merge_count": self.merge_count,
            "valid_coords": [c.to_dict() for c in self.valid_coords],
            "tile_slots": {f"{c.q},{c.r}": t.to_dict() for c, t in self.tile_slots.items()},
            "core": self.core.to_dict() if self.core else None
        }

    @staticmethod
    def from_dict(data: dict) -> 'ComponentEquipment':
        comp = ComponentEquipment(
            name=data["name"],
            slot=data["slot"],
            quality=data.get("quality", "Common"),
            level=data.get("level", 0),
            grid_width=data.get("grid_width", 3),
            grid_height=data.get("grid_height", 3),
            base_armor=data.get("base_armor", 0),
            base_hp=data.get("base_hp", 0),
            base_speed=data.get("base_speed", 0.0),
            merge_count=data.get("merge_count", 0)
        )
        
        # Restore valid coords
        if "valid_coords" in data:
            comp.valid_coords = {HexCoord.from_dict(c) for c in data["valid_coords"]}
            
        # Restore tiles
        if "tile_slots" in data:
            from hex_system.hex_tile import HexTile
            for coord_str, tile_data in data["tile_slots"].items():
                q, r = map(int, coord_str.split(','))
                coord = HexCoord(q, r)
                tile = HexTile.from_dict(tile_data)
                comp.tile_slots[coord] = tile
                
        # Restore Core
        if "core" in data and data["core"]:
            from hex_system.energy_packet import EnergyCore
            comp.core = EnergyCore.from_dict(data["core"])
            
        return comp

# --- Factory Functions ---

def create_starter_torso() -> ComponentEquipment:
    torso = ComponentEquipment(name="Basic Torso Mk I", slot="torso", quality="Common", base_armor=5, base_hp=50)
    # Shape: 3x3 block
    torso.valid_coords = {
        HexCoord(0,0), HexCoord(1,0), HexCoord(2,0),
        HexCoord(0,1), HexCoord(1,1), HexCoord(2,1),
        HexCoord(0,2), HexCoord(1,2), HexCoord(2,2)
    }
    torso.core = EnergyCore(core_type=SynergyType.FIRE, generation_rate=100.0, position=HexCoord(1, 1))
    
    # Place visual tile for the reactor
    from hex_system.hex_tile import ReactorTile, HexTile
    torso.place_tile(HexCoord(1, 1), ReactorTile())
    
    # Fill the rest with generic tiles to allow flow
    for q in range(3):
        for r in range(3):
            coord = HexCoord(q, r)
            if coord != HexCoord(1, 1):
                torso.place_tile(coord, HexTile(tile_type="Conductor", description="Conducts energy."))
    
    return torso

def create_starter_arm(slot: str) -> ComponentEquipment:
    if slot not in ["left_arm", "right_arm"]:
        raise ValueError("Arm slot must be 'left_arm' or 'right_arm'")
    side = "Right" if "right" in slot else "Left"
    arm = ComponentEquipment(name=f"Basic {side} Arm", slot=slot, quality="Common", base_armor=2)
    
    # Shape: Simple: 4x1 strip
    arm.valid_coords = {
        HexCoord(0,1), HexCoord(1,1), HexCoord(2,1), HexCoord(3,1)
    }
    
    # FIX: Correctly instantiate WeaponMountTile with the right arguments.
    from hex_system.hex_tile import WeaponMountTile, TileCategory, HexTile
    weapon_mount = WeaponMountTile(tile_type="Weapon Mount", category=TileCategory.OUTPUT, weapon_type="beam")
    
    # Place at end
    if slot == "left_arm":
        arm.place_tile(HexCoord(0, 1), weapon_mount) # Exit at left
    else:
        arm.place_tile(HexCoord(3, 1), weapon_mount) # Exit at right
        
    # Fill rest with conductors
    for coord in arm.valid_coords:
        if coord not in arm.tile_slots:
            arm.place_tile(coord, HexTile(tile_type="Conductor", description="Conducts energy."))
        
    return arm

def create_starter_leg(slot: str) -> ComponentEquipment:
    if slot not in ["left_leg", "right_leg"]:
        raise ValueError("Leg slot must be 'left_leg' or 'right_leg'")
    side = "Right" if "right" in slot else "Left"
    leg = ComponentEquipment(name=f"Basic {side} Leg", slot=slot, quality="Common", base_speed=1.5)
    
    # Shape: Vertical strip 2x4
    leg.valid_coords = {
        HexCoord(1,0), 
        HexCoord(1,1), 
        HexCoord(1,2), 
        HexCoord(1,3),
        HexCoord(0,3) # Foot
    }
    
    # Fill with conductors
    from hex_system.hex_tile import HexTile
    for coord in leg.valid_coords:
        if coord not in leg.tile_slots:
            leg.place_tile(coord, HexTile(tile_type="Conductor", description="Conducts energy."))
            
    return leg

def create_starter_head() -> ComponentEquipment:
    head = ComponentEquipment(name="Basic Head", slot="head", quality="Common", base_armor=1)
    # Shape: Hexagon-ish (Center + ring)
    head.valid_coords = {
        HexCoord(1,0), HexCoord(2,0),
        HexCoord(0,1), HexCoord(1,1), HexCoord(2,1), HexCoord(3,1),
        HexCoord(1,2), HexCoord(2,2)
    }
    
    # Fill with conductors
    from hex_system.hex_tile import HexTile
    for coord in head.valid_coords:
        if coord not in head.tile_slots:
            head.place_tile(coord, HexTile(tile_type="Conductor", description="Conducts energy."))
            
    return head

def create_starter_back() -> ComponentEquipment:
    back = ComponentEquipment(name="Basic Back Unit", slot="back", quality="Common")
    # Shape: T-shape or Wings
    back.valid_coords = {
        HexCoord(0,0), HexCoord(1,0), HexCoord(2,0), HexCoord(3,0),
        HexCoord(1,1), HexCoord(2,1)
    }
    
    # Fill with conductors
    from hex_system.hex_tile import HexTile
    for coord in back.valid_coords:
        if coord not in back.tile_slots:
            back.place_tile(coord, HexTile(tile_type="Conductor", description="Conducts energy."))
            
    return back

def create_random_component(rarity: str = "Common", slot: str = None) -> ComponentEquipment:
    import random
    from hex_system.hex_tile import HexTile, AmplifierTile, ResonatorTile, WeaponMountTile, TileCategory, SplitterTile
    
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
    
    entry = None
    target_hex = None
    
    # --- Custom Grid Shape Generation ---
    valid_coords = set()
    
    # Helper to add rect
    def add_rect(w, h, offset_q=0, offset_r=0):
        for q in range(w):
            for r in range(h):
                valid_coords.add(HexCoord(q + offset_q, r + offset_r))

    if slot == "torso":
        # Torso: Large, symmetric block or blob
        if rarity in ["Common", "Uncommon"]:
            add_rect(3, 3)
        elif rarity == "Rare":
            add_rect(4, 4)
        else:
            # Cross shape or 5x5 with corners cut
            add_rect(5, 5)
            # Remove corners
            valid_coords.remove(HexCoord(0, 0))
            valid_coords.remove(HexCoord(4, 0))
            valid_coords.remove(HexCoord(0, 4))
            valid_coords.remove(HexCoord(4, 4))
            
    elif slot == "head":
        # Head: Smaller, symmetric
        if rarity == "Common":
            add_rect(3, 2) # Wide
        elif rarity == "Uncommon":
            add_rect(2, 3) # Tall
        else:
            # Diamond-ish
            valid_coords.add(HexCoord(1, 0))
            valid_coords.add(HexCoord(0, 1))
            valid_coords.add(HexCoord(1, 1))
            valid_coords.add(HexCoord(2, 1))
            valid_coords.add(HexCoord(1, 2))
            if rarity == "Legendary":
                valid_coords.add(HexCoord(0, 2))
                valid_coords.add(HexCoord(2, 0))

    elif slot in ["left_arm", "right_arm"]:
        # Arms: Elongated horizontally
        width = 4 if rarity in ["Common", "Uncommon"] else 5
        height = 2
        if rarity == "Legendary": height = 3
        
        add_rect(width, height)
        
        # Make it look like an arm (tapered?)
        if rarity != "Common":
            if HexCoord(0, 0) in valid_coords: valid_coords.remove(HexCoord(0, 0))
            if HexCoord(width-1, height-1) in valid_coords: valid_coords.remove(HexCoord(width-1, height-1))

    elif slot in ["left_leg", "right_leg"]:
        # Legs: Elongated vertically
        width = 2
        height = 4 if rarity in ["Common", "Uncommon"] else 5
        if rarity == "Legendary": width = 3
        
        add_rect(width, height)
        
    elif slot == "back":
        # Back: Symmetric, medium
        add_rect(3, 3)
        if rarity != "Common":
            valid_coords.add(HexCoord(1, -1)) # Top center extension
            valid_coords.add(HexCoord(1, 3))  # Bottom center extension
            
    # Apply generated coords
    if valid_coords:
        comp.valid_coords = valid_coords
        # Recalculate dimensions
        qs = [c.q for c in valid_coords]
        rs = [c.r for c in valid_coords]
        comp.grid_width = max(qs) - min(qs) + 1
        comp.grid_height = max(rs) - min(rs) + 1
        comp.max_tile_capacity = len(valid_coords)
    
    # Ensure arms have a weapon mount
    if slot in ["left_arm", "right_arm"]:
        # 50% chance for weapon mount on random arms, or 100% if it's a "Weapon"
        # The user expects weapons to work, so let's be generous.
        from hex_system.hex_tile import WeaponMountTile, TileCategory, HexTile, AmplifierTile, ResonatorTile, SplitterTile
        
        # Determine weapon mount position (usually far side)
        entry, exit_hex = comp.get_entry_exit_hexes()
        mount_pos = exit_hex if exit_hex else HexCoord(1, 1)
        
        # Ensure mount_pos is valid
        if mount_pos not in comp.valid_coords:
             # Fallback to any valid coord
             mount_pos = list(comp.valid_coords)[-1]
        
        mount = WeaponMountTile(tile_type="Weapon Mount", category=TileCategory.OUTPUT, weapon_type="beam")
        comp.place_tile(mount_pos, mount)
        
    # If Torso, generate a Core and ReactorTile
    if slot == "torso":
        from hex_system.energy_packet import EnergyCore, SynergyType
        # Random synergy
        syn_type = random.choice(list(SynergyType))
        # Higher rarity = higher rate
        rate = 10.0
        if rarity == "Uncommon": rate = 20.0
        elif rarity == "Rare": rate = 40.0
        elif rarity == "Epic": rate = 70.0
        elif rarity == "Legendary": rate = 100.0
        
        comp.core = EnergyCore(generation_rate=rate, core_type=syn_type)
        
        # Place ReactorTile at center
        center_q = (min(c.q for c in comp.valid_coords) + max(c.q for c in comp.valid_coords)) // 2
        center_r = (min(c.r for c in comp.valid_coords) + max(c.r for c in comp.valid_coords)) // 2
        center = HexCoord(center_q, center_r)
        
        if center not in comp.valid_coords:
             # Find closest valid
             center = min(comp.valid_coords, key=lambda c: (c.q - center_q)**2 + (c.r - center_r)**2)

        comp.core.position = center
        from hex_system.hex_tile import ReactorTile
        comp.place_tile(center, ReactorTile())
            
        # Update entry for pathfinding to be the reactor
        entry = center

    # Ensure a valid path exists from entry to exit (or mount)
    # If Torso, entry is the Reactor (center). Target is... random edge?
    if slot == "torso":
        # Pick a random edge hex as target to ensure at least one output
        edges = [h for h in comp.valid_coords if len([n for n in range(6) if comp._get_neighbor_in_direction(h, n) not in comp.valid_coords]) > 0]
        if edges:
            target_hex = random.choice(edges)
        else:
            target_hex = list(comp.valid_coords)[0]
    else:
        entry, exit_hex = comp.get_entry_exit_hexes()
        target_hex = exit_hex
    
    # If it's an arm, target the weapon mount
    if slot in ["left_arm", "right_arm"]:
        # Find the weapon mount
        for coord, tile in comp.tile_slots.items():
            if isinstance(tile, WeaponMountTile):
                target_hex = coord
                break
    
    if entry and target_hex and entry != target_hex:
        # Simple pathfinding to ensure connection
        current = entry
        path = [current]
        
        # Greedy path to target
        while current != target_hex:
            # Find neighbor closest to target
            best_dist = float('inf')
            best_next = None
            best_dir = 0
            
            for direction in range(6):
                next_coord = comp._get_neighbor_in_direction(current, direction)
                if next_coord in comp.valid_coords:
                    dist = ((next_coord.q - target_hex.q)**2 + (next_coord.r - target_hex.r)**2)**0.5
                    if dist < best_dist:
                        best_dist = dist
                        best_next = next_coord
                        best_dir = direction
            
            if best_next:
                # If we are placing a tile at 'current', it should point to 'best_dir'
                # But we place tiles AFTER finding the path. We need to store directions.
                # Actually, let's just store the path and deduce directions later.
                current = best_next
                path.append(current)
                if len(path) > 20: break # Safety break
            else:
                break
        
        # Fill path with high-quality tiles AND orient them
        from hex_system.hex_tile import BasicConduitTile
        
        for i in range(len(path) - 1):
            coord = path[i]
            next_coord = path[i+1]
            
            # Determine direction from coord to next_coord
            # We can cheat and check neighbors or just use the logic we just used?
            # Let's find direction index
            exit_dir = 0
            for d in range(6):
                if comp._get_neighbor_in_direction(coord, d) == next_coord:
                    exit_dir = d
                    break
            
            if coord not in comp.tile_slots:
                # High chance for amplifier on the main path for high rarity
                roll = random.random()
                tile = None
                
                if rarity == "Legendary" and roll < 0.7:
                    # NOW we can use AmplifierTile because it inherits BasicConduitTile!
                    tile = AmplifierTile()
                    tile.set_exit_direction(exit_dir)
                    
                    # Add a small merge bonus to make it even better
                    tile.merge_bonus = 0.05
                
                elif rarity == "Epic" and roll < 0.5:
                    tile = AmplifierTile()
                    tile.set_exit_direction(exit_dir)
                
                else:
                    tile = BasicConduitTile()
                    tile.set_exit_direction(exit_dir)
                    
                    # If it's legendary, maybe upgrade the conduit?
                    if rarity in ["Epic", "Legendary"]:
                        tile.merge_bonus = 0.1 * (1 if rarity == "Epic" else 2) # 10-20% bonus
                        tile.base_color = (255, 200, 100) # Gold-ish
                        tile.name = "Super Conduit"
                
                comp.place_tile(coord, tile)

    # Fill the rest of the grid with random tiles based on rarity
    import random
    
    for coord in comp.valid_coords:
        if coord not in comp.tile_slots:
            # Chance for special tiles based on rarity
            roll = random.random()
            tile = None
            
            chance_amp = 0.0
            chance_res = 0.0
            
            if rarity == "Uncommon": chance_amp = 0.1
            elif rarity == "Rare": chance_amp = 0.2; chance_res = 0.1
            elif rarity == "Epic": chance_amp = 0.3; chance_res = 0.2
            elif rarity == "Legendary": chance_amp = 0.4; chance_res = 0.3
            
            if roll < chance_amp:
                tile = AmplifierTile()
            elif roll < chance_amp + chance_res:
                tile = ResonatorTile()
            else:
                tile = HexTile(tile_type="Conductor", description="Conducts energy.")
                
            comp.place_tile(coord, tile)
            
    return comp
