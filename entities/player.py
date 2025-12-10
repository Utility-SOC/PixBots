
from .bot import Bot
import pygame
import constants
from hex_system.hex_tile import SecondaryOutputTile, TargetSystem

class Player(Bot):
    """Player-specific bot class."""
    def __init__(self, name: str, x: float, y: float, use_components: bool = True):
        super().__init__(name, x, y)
        self.is_player = True
        self.inventory = []
        self.currencies = {"scrap": 0, "crystals": 0, "shards": 0}
        
        self.base_hp = 120
        self.max_hp = 120
        self.speed = 6.0 # Modifies max speed
        self.level = 1 # Player Level
        self.alpha = 255 # Explicitly init alpha for visibility safety (Fixes invisible bug)
        
        self.sprite_name = "player_bot.png"
        
        self.recalculate_stats()
        self.hp = self.max_hp
        self.angle = 0.0 # Initialize facing angle
        
        # Combat
        self.weapon = {"damage": 10, "speed": 300, "cooldown": 0.5, "last_shot": 0}
        
        # Shield Logic
        self.shield = 0.0
        self.max_shield = 0.0
        self.has_shield = False
        self.time_since_last_hit = 0.0
        self.shield_regen_delay = 3.0 # Seconds before regen starts

        # Phase 1: SUCM and Secondary Outputs
        from equipment.sucm import SUCM
        self.sucm = SUCM()
        self.secondary_actions = [] # list of dicts
        self.fire_queue = [] # List of (time, callable) for staggered fire
        
        # Orbital Mechanics
        self.orbital_mode = False 
        self.orbital_mode_prev = False
        self.active_orbitals = [] # Track active orbital projectiles

    def take_damage(self, amount: float):
        # Intercept damage for Shield
        self.time_since_last_hit = 0.0 # Reset regen timer
        
        remaining_dmg = amount
        if self.shield > 0:
            absorbed = min(self.shield, amount)
            self.shield -= absorbed
            remaining_dmg -= absorbed
            # Visual feedback for shield hit could go here
                
        if remaining_dmg > 0:
            super().take_damage(remaining_dmg)

    def shoot(self, target_x, target_y, combat_system, current_time):
        if current_time - self.weapon["last_shot"] < self.weapon["cooldown"]:
            return
            
        import math
        angle = math.atan2(target_y - self.y, target_x - self.x)
        self.angle = angle
        
        import logging
        logger = logging.getLogger(__name__)
        
        # R2: Body Simulation & Multi-Weapon Firing
        torso = self.components.get("torso")
        torso_exits = {}
        processed_components = [] # List of (comp, stats)
        
        # 1. Simulate Torso
        if torso:
             _, t_stats, torso_exits = torso.simulate_flow()
             if t_stats.get("weapon_damage", 0) > 0:
                 processed_components.append((torso, t_stats))
        
        # 2. Simulate Connected Components
        connection_map = {
            "right_arm": {"from": 0, "to": 3}, # Torso E -> Arm W
            "left_arm":  {"from": 3, "to": 0}, # Torso W -> Arm E
            "head":      {"from": 1, "to": 4}, # Torso NE -> Head SW
            "back":      {"from": 2, "to": 5}, # Torso NW -> Back SE
            "right_leg": {"from": 5, "to": 2}, # Torso SE -> R.Leg NW
            "left_leg":  {"from": 4, "to": 1}, # Torso SW -> L.Leg NE
            "legs":      {"from": 5, "to": 2}  # Legacy/Fallback
        }
        
        for slot, comp in self.components.items():
            if not comp or slot == "torso": continue
            
            context = None
            input_dir = 0
            
            if slot in connection_map:
                conn = connection_map[slot]
                context = torso_exits.get(conn["from"])
                input_dir = conn["to"]
            
            _, stats, _ = comp.simulate_flow(context, input_dir)
            
            if stats.get("weapon_damage", 0) > 0:
                processed_components.append((comp, stats))

        # 3. Fire Weapons (Wave-based Staggered)
        fired_any = False
        pending_groups = [] # List of {'damage': float, 'actions': []}
        
        for comp, stats in processed_components:
            fired_any = True
            damage = stats["weapon_damage"]
            
            # Create a group for this component's wave
            current_group = {'damage': damage, 'actions': []}
            
            effects = stats.get("active_synergy_effects", {})
            if "active_synergy" in stats:
                effects["synergy_name"] = str(stats["active_synergy"]).lower().split('.')[-1]
            effects["rarity"] = comp.quality
            
            # R3: Kinetic Synergy Spread
            kinetic_rate = stats.get("synergy_magnitudes", {}).get("kinetic", 0.0)
            spread_factor = max(0.0, 1.0 - (kinetic_rate / 100.0))
            
            weapon_inputs = stats.get("weapon_inputs", [])
            spread_count = len(weapon_inputs) if weapon_inputs else 1
            spread_count = max(1, spread_count)
            
            base_spread = 0.15
            current_spread_step = base_spread * spread_factor
            
            # Center the spread
            start_angle = angle - (spread_count - 1) * current_spread_step / 2
            
            for i in range(spread_count):
                curr_angle = start_angle + i * current_spread_step
                
                # Collect shots instead of firing immediately
                # S5: Orbital Defense Logic OR Manual Override (Z Key)
                # If Z is held (orbital_mode), FORCE orbital behavior
                if self.orbital_mode or (effects and "orbital_config" in effects):
                    # Use existing config if present, or create default
                    orb_config = effects.get("orbital_config", {}).copy()
                    
                    # If forcing via Z, ensure we have defaults
                    if not orb_config:
                         orb_config = {
                             "radius": 100.0,
                             "orbit_speed": 3.0,
                             "ttl": 999.0 # Infinite until release
                         }
                    
                    orb_config["angle_offset"] = curr_angle
                    orb_config["damage"] = damage
                    
                    action = self._queue_orbital(combat_system, orb_config, effects)
                    current_group['actions'].append(action)

                else:
                    action = self._queue_shot(
                        combat_system, 
                        self.x, self.y, curr_angle, 
                        self.weapon["speed"], damage, 
                        "physical", "player", 
                        effects
                    )
                    current_group['actions'].append(action)
            
            # Add the finished group to pending lists
            if current_group['actions']:
                pending_groups.append(current_group)
        
        # DEBUG: Check wave count
        if len(pending_groups) > 0:
            logger.info(f"Player.shoot: Created {len(pending_groups)} weapon groups (waves).")


        if pending_groups:
            # Sort Groups by Damage (Descending) - Most powerful WEAPON fires first
            # "First weapon out front, then 1/6th x later the next fires"
            pending_groups.sort(key=lambda x: x['damage'], reverse=True)
            
            # Stagger logic: Delay between WAVES (groups), but shots WITHIN a wave are simultaneous
            delay_step = self.weapon["cooldown"] / 6.0
            
            for i, group in enumerate(pending_groups):
                fire_time = current_time + (i * delay_step)
                
                # Schedule ALL shots for this weapon at this time
                for action in group['actions']:
                    self.fire_queue.append((fire_time, action))

        if fired_any:
            self.weapon["last_shot"] = current_time

    # Helper to capture arguments for delayed execution
    def _queue_shot(self, combat_system, x, y, angle, speed, damage, p_type, owner, effects):
        def action():
            combat_system.spawn_projectile(x, y, angle, speed, damage, p_type, owner, effects=effects)
        return action

    def _queue_orbital(self, combat_system, config, effects):
        from entities.orbital_defense import Orbital
        def action():
            orb = Orbital(self, config, effects)
            if "ttl" in config:
                orb.lifetime = config["ttl"]
            combat_system.projectiles.append(orb)
            # Track it for release logic
            self.active_orbitals.append(orb)
        return action

    def activate_secondary(self, action, dt: float):
        tile = action["tile"]
        comp = action["component"]
        
        # New Logic: Use the 'charge' calculated by the tile's consumption
        # This charge is stored in the component's stats from simulate_flow
        system_type = tile.target_system.value
        charge_key = f"system_{system_type}_charge"
        
        available_power = comp.stats.get(charge_key, 0.0)
        
        # If no flow through tile, no power.
        if available_power <= 0.1:
            return 

        if tile.target_system == TargetSystem.ROCKET_LEGS or tile.target_system == TargetSystem.ACCELERATOR:
             # Apply continuous force in facing direction
             import math
             # Power 100 -> Force 2000? Scale factor
             force = available_power * 20.0 * dt
             fx = math.cos(self.angle) * force
             fy = math.sin(self.angle) * force
             self.velocity_x += fx
             self.velocity_y += fy
             
        elif tile.target_system == TargetSystem.SHIELD:
             # Recharge Shield (Active Boost on top of Passive?)
             if self.has_shield:
                 recharge_rate = available_power * 0.5 # Efficiency
                 self.shield = min(self.max_shield, self.shield + recharge_rate * dt)

        elif tile.target_system == TargetSystem.CLOAK:
             # Cloak Logic
             # Set State (will be reset next frame in update if key released)
             self.is_cloaked = True
             self.alpha = 50
             
        elif tile.target_system == TargetSystem.SUCM:
             # Self-repair
             repair_rate = available_power * 0.1
             self.heal(repair_rate * dt)

    def update(self, dt: float):
        """Player-specific update logic."""
        # Reset Transient States
        self.is_cloaked = False
        self.alpha = 255
        
        super().update(dt) # Physics and Status Effects
        
        # Shield Regeneration (Passive always-on logic)
        if self.has_shield:
             self.time_since_last_hit += dt
             if self.time_since_last_hit > self.shield_regen_delay and self.shield < self.max_shield:
                 regen_rate = 20.0 # HP/sec
                 self.shield = min(self.max_shield, self.shield + regen_rate * dt)
        
        # Process Fire Queue (Staggered Shots)
        current_time = pygame.time.get_ticks() / 1000.0
        remaining_queue = []
        for fire_time, action_func in self.fire_queue:
            if current_time >= fire_time:
                action_func()
            else:
                remaining_queue.append((fire_time, action_func))
        self.fire_queue = remaining_queue
        
        # Update Components
        for comp in self.components.values():
            if comp:
                comp.update(dt)

        # Update Active Orbitals Clean-up
        # Remove dead/released orbitals from tracking list
        self.active_orbitals = [orb for orb in self.active_orbitals if orb.active and getattr(orb, "active_orbit", False)]

        # Input Handling (Secondary Actions & Modes)
        keys = pygame.key.get_pressed()
        
        # Helper to find specific system action
        def activate_system(target_sys_list):
            if not isinstance(target_sys_list, list): target_sys_list = [target_sys_list]
            for action in self.secondary_actions:
                if action["tile"].target_system in target_sys_list:
                    self.activate_secondary(action, dt)
        
        # 1. Shift: Accelerator / Rocket Legs (Dash)
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            activate_system([TargetSystem.ROCKET_LEGS])
            
        # 2. Ctrl: Cloak
        if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
            activate_system(TargetSystem.CLOAK)
            
        # 3. Z: Orbital Mode Logic
        if keys[pygame.K_z]:
            self.orbital_mode = True
            # Auto-fire main weapon handled by main loop? 
            # If we want "Automatic" firing, we must signal Main.
            # OR we can just fire here if we have reference to combat system.
            # We don't. Main loop calls 'player.shoot'.
            # We will rely on user holding Mouse Button OR Main loop checking 'player.orbital_mode' to auto-fire.
            # For now, we just set the mode flag, and 'shoot' uses it.
        else:
            if self.orbital_mode_prev: # Was True, now False -> RELEASE
                # Release Logic
                self.orbital_mode = False
                for orb in self.active_orbitals:
                    orb.release()
                self.active_orbitals = [] # Clear tracking
            self.orbital_mode = False
            
        self.orbital_mode_prev = self.orbital_mode

        # Handle Manual 1-4
        def trigger_action(index):
            if index < len(self.secondary_actions):
                action = self.secondary_actions[index]
                self.activate_secondary(action, dt)

        if keys[pygame.K_1]: trigger_action(0)
        if keys[pygame.K_2]: trigger_action(1)
        if keys[pygame.K_3]: trigger_action(2)
        if keys[pygame.K_4]: trigger_action(3)

    def recalculate_stats(self):
        super().recalculate_stats()
        
        # S2: Scan for Secondary Outputs
        self.secondary_actions = []
        self.has_shield = False
        # Do not reset self.shield HP here to avoid losing charge on equip change
        
        for slot, comp in self.components.items():
            if not comp: continue
            
            for coord, tile in comp.tile_slots.items():
                if isinstance(tile, SecondaryOutputTile):
                    if tile.target_system == TargetSystem.SHIELD:
                        self.has_shield = True
                        if hasattr(self, "max_shield"):
                             self.max_shield = 100.0 * comp.level
                    else:
                        self.secondary_actions.append({
                            "tile": tile,
                            "component": comp,
                            "slot": slot
                        })

    def add_to_inventory(self, item):
        self.inventory.append(item)

    def add_currency(self, currency_type: str, amount: int):
        if currency_type in self.currencies:
            self.currencies[currency_type] += amount

    def handle_pickup(self, item) -> bool:
        """
        S1: Standardized pickup handler for valid loot items.
        """
        # 1. Equipment (Duck Typing)
        if hasattr(item, "slot") and hasattr(item, "tile_slots"):
             self.add_to_inventory(item)
             return True
             
        # 2. Dictionary-based Items
        if isinstance(item, dict):
            item_type = item.get("type", "unknown")
            
            if item_type == "energy_pack":
                amount = item.get("amount", 25)
                self.add_currency("shards", amount)
                return True
                
            elif item_type == "currency":
                c_type = item.get("currency_type", "scrap")
                amount = item.get("amount", 1)
                self.add_currency(c_type, amount)
                return True
                
        return False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "currencies": self.currencies,
            "components": {slot: comp.to_dict() for slot, comp in self.components.items() if comp},
            "inventory": [comp.to_dict() for comp in self.inventory]
        }

    @staticmethod
    def from_dict(data: dict, asset_manager=None) -> 'Player':
        player = Player(data["name"], data["x"], data["y"])
        if asset_manager:
            player.asset_manager = asset_manager
        player.hp = data.get("hp", 100)
        player.max_hp = data.get("max_hp", 100)
        player.currencies = data.get("currencies", {"scrap": 0, "crystals": 0, "shards": 0})
        
        from equipment.component import ComponentEquipment
        
        # Restore Components
        if "components" in data:
            for slot, comp_data in data["components"].items():
                comp = ComponentEquipment.from_dict(comp_data)
                player.equip_component(comp)
                
        # Restore Inventory
        if "inventory" in data:
            for comp_data in data["inventory"]:
                comp = ComponentEquipment.from_dict(comp_data)
                player.inventory.append(comp)
                
        player.recalculate_stats()
        player.alpha = 255 # Force visibility on load
        return player
