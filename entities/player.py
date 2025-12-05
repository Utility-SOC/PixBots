# pixbots_enhanced/entities/player.py
# UPDATED to include a call to the parent's new update method.

from .bot import Bot
import pygame
import constants

class Player(Bot):
    """Player-specific bot class."""
    def __init__(self, name: str, x: float, y: float, use_components: bool = True):
        super().__init__(name, x, y)
        self.is_player = True
        self.inventory = []
        self.currencies = {"scrap": 0, "crystals": 0, "shards": 0}
        
        self.base_hp = 120
        self.base_hp = 120
        self.speed = 6.0 # Modifies max speed
        self.level = 1 # Player Level
        
        self.sprite_name = "player_bot.png"
        
        self.recalculate_stats()
        self.hp = self.max_hp
        
        # Combat
        self.weapon = {"damage": 10, "speed": 300, "cooldown": 0.5, "last_shot": 0}

    def shoot(self, target_x, target_y, combat_system, current_time):
        if current_time - self.weapon["last_shot"] < self.weapon["cooldown"]:
            return
            
        import math
        angle = math.atan2(target_y - self.y, target_x - self.x)
        
        # Find the weapon component (right arm usually, or whichever has the weapon mount)
        # For now, let's check right arm then left arm
        weapon_comp = self.components.get("right_arm")
        weapon_slot = "right_arm"
        
        if not weapon_comp:
            weapon_comp = self.components.get("left_arm")
            weapon_slot = "left_arm"
            
        damage = self.weapon["damage"]
        effects = {}
        
        if weapon_comp:
            # NEW: Get energy context from Torso!
            input_context = None
            input_direction = None
            torso = self.components.get("torso")
            
            import logging
            logger = logging.getLogger(__name__)
            
            if torso:
                # Debug Torso State
                logger.info(f"Player.shoot: Torso found. Name: {torso.name}, Core: {torso.core}")
                if torso.core:
                     logger.info(f"  -> Core Type: {torso.core.core_type}, Rate: {torso.core.generation_rate}")
                
                # Simulate torso flow to get exits
                _, _, torso_exits = torso.simulate_flow()
                logger.info(f"  -> Torso Exits: {list(torso_exits.keys())}")
                
                # Determine which direction leads to the arm
                if weapon_slot == "right_arm":
                    input_context = torso_exits.get(0) # East
                    input_direction = 3 # Enter from West
                elif weapon_slot == "left_arm":
                    input_context = torso_exits.get(3) # West
                    input_direction = 0 # Enter from East
                    
                # Fallback: If no output in expected direction, use the strongest output
                if not input_context and torso_exits:
                    best_dir = max(torso_exits, key=lambda d: torso_exits[d].get_total_magnitude())
                    input_context = torso_exits[best_dir]
                    # Keep expected input_direction to ensure flow enters the component
                    logger.info(f"Rerouting energy from Torso dir {best_dir} to {weapon_slot}")
            else:
                logger.warning("Player.shoot: No Torso component found!")
            
            # Pass input context to arm simulation
            if input_context:
                logger.debug(f"Player.shoot: Input Context to {weapon_slot}: {input_context.synergies}, Mag: {input_context.get_total_magnitude()}")
            else:
                logger.warning(f"Player.shoot: NO Input Context to {weapon_slot}")

            _, stats, _ = weapon_comp.simulate_flow(input_context, input_direction)
            
            # Use calculated damage if available (and greater than base)
            if stats.get("weapon_damage", 0) > 0:
                damage = stats["weapon_damage"]
            
            effects = stats.get("active_synergy_effects", {})
            # Pass the synergy name so CombatSystem knows what it is (e.g. "vampiric")
            if "active_synergy" in stats:
                effects["synergy_name"] = str(stats["active_synergy"]).lower().split('.')[-1]
            
            # Pass rarity for Vampiric calculation
            effects["rarity"] = weapon_comp.quality

            # Debug logging for damage issues
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Shooting! Damage: {damage}, Synergy: {stats.get('active_synergy')}, Effects: {effects}")
            
        # Determine spread count based on active input vectors
        weapon_inputs = stats.get("weapon_inputs", [])
        spread_count = len(weapon_inputs) if weapon_inputs else 1
        spread_count = max(1, spread_count) # Ensure at least 1
        
        base_angle = angle
        spread_step = 0.15 # Radians (~8.5 degrees)
        
        start_angle = base_angle - (spread_count - 1) * spread_step / 2
        
        for i in range(spread_count):
            current_angle = start_angle + i * spread_step
            
            combat_system.spawn_projectile(
                self.x, self.y, current_angle, 
                self.weapon["speed"], damage, 
                "physical", "player",
                effects=effects
            )
        
        self.weapon["last_shot"] = current_time
        
    # NEW: Ensure the bot's core update logic is called for the player.
    def update(self, dt: float):
        """Player-specific update logic, which also calls the base bot update."""
        super().update(dt)
        # Add any player-specific update logic here in the future
        
    def add_to_inventory(self, item):
        self.inventory.append(item)

    def add_currency(self, currency_type: str, amount: int):
        if currency_type in self.currencies:
            self.currencies[currency_type] += amount

    def render(self, screen, camera_x, camera_y):
        screen_x = int(self.x + camera_x)
        screen_y = int(self.y + camera_y)
        
        # Draw base
        pygame.draw.circle(screen, (50, 50, 255), (screen_x, screen_y), constants.TILE_SIZE // 2)
        
        # Draw components (simplified)
        for slot, comp in self.components.items():
            if comp:
                # Offset based on slot
                ox, oy = 0, 0
                if slot == "head": oy = -10
                elif slot == "left_arm": ox = -15
                elif slot == "right_arm": ox = 15
                elif slot == "left_leg": ox = -10; oy = 15
                elif slot == "right_leg": ox = 10; oy = 15
                
                color = (200, 200, 200)
                if comp.quality == "Uncommon": color = (50, 255, 50)
                elif comp.quality == "Rare": color = (50, 50, 255)
                elif comp.quality == "Epic": color = (200, 50, 200)
                elif comp.quality == "Legendary": color = (255, 165, 0)
                
                pygame.draw.rect(screen, color, (screen_x + ox - 5, screen_y + oy - 5, 10, 10))

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
        return player
