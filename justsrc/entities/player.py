# pixbots_enhanced/entities/player.py
# UPDATED to include a call to the parent's new update method.

from .bot import Bot

class Player(Bot):
    """Player-specific bot class."""
    def __init__(self, name: str, x: float, y: float, use_components: bool = True):
        super().__init__(name, x, y)
        self.is_player = True
        self.inventory = []
        self.currencies = {"scrap": 0, "crystals": 0}
        
        self.base_hp = 120
        self.speed = 6.0 # Modifies max speed
        
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
        
        combat_system.spawn_projectile(
            self.x, self.y, angle, 
            self.weapon["speed"], self.weapon["damage"], 
            "physical", "player"
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
