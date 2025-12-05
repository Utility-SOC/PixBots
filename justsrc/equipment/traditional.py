# pixbots_enhanced/equipment/traditional.py
# Source: Version 2's equipment.py
import random
import logging

logger = logging.getLogger(__name__)

class Part:
    """Represents a traditional equipment part (e.g., head, torso)."""
    def __init__(self, name: str, slot: str, stats: dict):
        self.name = name
        self.slot = slot
        self.stats = stats # e.g., {"hp_bonus": 10, "armor_bonus": 2}

class Shield:
    """Represents a traditional energy shield."""
    def __init__(self, name: str, capacity: float, recharge_rate: float, efficiency: float):
        self.name = name
        self.energy_capacity = capacity
        self.current_energy = capacity
        self.recharge_rate = recharge_rate
        self.efficiency = efficiency # How much damage is absorbed per energy point

class Weapon:
    """Represents a traditional weapon."""
    def __init__(self, name: str, base_damage: float, base_range: float, energy_cost: float, synergies: list = None):
        self.name = name
        self.damage = base_damage
        self.range = base_range
        self.energy_cost = energy_cost
        self.synergies = synergies if synergies is not None else []

    def get_damage_with_variance(self):
        variance = self.damage * 0.1
        return random.uniform(self.damage - variance, self.damage + variance)