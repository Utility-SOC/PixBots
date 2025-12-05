import random
from equipment.component import ComponentEquipment

class CraftingSystem:
    def __init__(self):
        pass

    def fuse_components(self, comp1: ComponentEquipment, comp2: ComponentEquipment) -> ComponentEquipment:
        """Fuses two components into a new one."""
        if comp1.slot != comp2.slot:
            return None # Can only fuse same slot items
            
        new_quality = comp1.quality
        if comp1.quality == comp2.quality:
            qualities = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
            try:
                idx = qualities.index(comp1.quality)
                if idx < len(qualities) - 1:
                    new_quality = qualities[idx + 1]
            except ValueError:
                pass

        # Calculate merge count
        new_merge_count = comp1.merge_count + comp2.merge_count + 1
        
        # Generate Name
        base_name = comp1.name.split('+')[0].strip() # Remove existing +X
        new_name = f"{base_name} +{new_merge_count}"
        
        new_armor = int((comp1.base_armor + comp2.base_armor) * 0.6)
        new_hp = int((comp1.base_hp + comp2.base_hp) * 0.6)
        new_speed = (comp1.base_speed + comp2.base_speed) * 0.6
        
        new_comp = ComponentEquipment(
            name=new_name,
            slot=comp1.slot,
            quality=new_quality,
            base_armor=new_armor,
            base_hp=new_hp,
            base_speed=new_speed,
            merge_count=new_merge_count
        )
        
        # Grid expansion is handled by __post_init__ in ComponentEquipment based on quality
        # But we need to preserve existing tiles if possible? 
        # For now, let's just create a fresh grid. Merging usually consumes items to make a better base.
        
        return new_comp
