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
        
        # Copy existing grid from the first component (the "base")
        new_comp.valid_coords = set(comp1.valid_coords)
        new_comp.tile_slots = {}
        
        # Deep copy tiles? Or just reference?
        # Tiles are dataclasses, so they are mutable. We should probably clone them.
        # For now, let's just copy the reference, but ideally we'd clone.
        # Actually, let's just copy the dictionary structure.
        for coord, tile in comp1.tile_slots.items():
            new_comp.tile_slots[coord] = tile
            
        # If it's a torso, preserve the core!
        if comp1.slot == "torso" and comp1.core:
            import copy
            new_comp.core = copy.deepcopy(comp1.core)
            
            # Merge Synergies from comp2 if available
            if comp2.slot == "torso" and comp2.core:
                for syn_type, magnitude in comp2.core.synergy_outputs.items():
                    if syn_type in new_comp.core.synergy_outputs:
                        new_comp.core.synergy_outputs[syn_type] += magnitude
                    else:
                        new_comp.core.synergy_outputs[syn_type] = magnitude
                
                # Re-distribute energy (reset to omni for now to ensure new synergy is usable)
                new_comp.core.configure_omnidirectional()
            
            # Ensure the ReactorTile is also present
            from hex_system.hex_tile import ReactorTile
            if comp1.core.position:
                new_comp.place_tile(comp1.core.position, ReactorTile())
                
        # UPGRADE GRID: Chance to improve a tile
        # Fusion should feel like progress.
        import random
        from hex_system.hex_tile import HexTile, AmplifierTile, ResonatorTile
        
        # 1. Fill empty spots?
        # 2. Upgrade existing tiles?
        
        # Let's try to upgrade 1-3 random tiles
        upgrade_count = random.randint(1, 3)
        candidates = [c for c, t in new_comp.tile_slots.items() if t.tile_type == "Conductor"]
        
        if candidates:
            for _ in range(upgrade_count):
                if not candidates: break
                target = random.choice(candidates)
                candidates.remove(target)
                
                # Upgrade Conductor -> Amplifier (70%) or Resonator (30%)
                if random.random() < 0.7:
                    new_comp.place_tile(target, AmplifierTile())
                else:
                    new_comp.place_tile(target, ResonatorTile())
        
        return new_comp
