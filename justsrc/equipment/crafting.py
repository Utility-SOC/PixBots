# pixbots_enhanced/equipment/crafting.py
# Source: Extracted from Version 2's equipment.py

import random
import math
import logging
from .traditional import Weapon

logger = logging.getLogger(__name__)

class CraftingSystem:
    """Handles crafting and merging of equipment."""
    def __init__(self):
        # In a full game, these would be loaded from data files
        self.synergy_compatibility = {"fire": ["ice", "poison"], "ice": ["fire", "lightning"]}
        logger.info("CraftingSystem initialized.")

    def merge_weapons(self, w1: Weapon, w2: Weapon) -> Optional[Weapon]:
        if not isinstance(w1, Weapon) or not isinstance(w2, Weapon):
            return None

        logger.info(f"Merging '{w1.name}' and '{w2.name}'.")

        new_damage = (w1.damage + w2.damage) / 2.0 * 1.1 # 10% merge bonus
        new_range = max(w1.range, w2.range)
        new_cost = (w1.energy_cost + w2.energy_cost) / 2.0
        
        combined_synergies = list(set(w1.synergies + w2.synergies))
        
        # Simple name merge
        name1_part = w1.name.split(" ")[-1]
        name2_part = w2.name.split(" ")[-1]
        new_name = f"Fused {name1_part}-{name2_part}"

        return Weapon(new_name, new_damage, new_range, new_cost, combined_synergies)