import random
from typing import Optional
from hex_system.hex_tile import HexTile, AmplifierTile, ResonatorTile, SplitterTile, BasicConduitTile, TileCategory

class LootManager:
    """
    Handles generation of loot (tiles/components) and merging logic.
    """
    
    RARITIES = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
    
    @staticmethod
    def create_lootable_tile(rarity: str = "Common") -> HexTile:
        """Generates a random tile with the given rarity."""
        tile_types = [
            "amplifier", "resonator", "splitter", "conduit"
        ]
        
        # Weights could be adjusted
        choice = random.choice(tile_types)
        
        tile = None
        if choice == "amplifier":
            # Higher rarity = higher base amplification
            base_amp = 1.2
            if rarity == "Uncommon": base_amp = 1.3
            elif rarity == "Rare": base_amp = 1.5
            elif rarity == "Epic": base_amp = 1.8
            elif rarity == "Legendary": base_amp = 2.5
            
            tile = AmplifierTile(amplification=base_amp)
            
        elif choice == "resonator":
            tile = ResonatorTile()
            # Random synergy?
            from hex_system.energy_packet import SynergyType
            syns = list(SynergyType)
            # Remove RAW
            syns = [s for s in syns if s != SynergyType.RAW]
            tile.synergies = [random.choice(syns)]
            
        elif choice == "splitter":
            tile = SplitterTile()
            
        elif choice == "conduit":
            tile = BasicConduitTile()
            
        if tile:
            tile.quality = rarity
            tile.name = f"{rarity} {tile.tile_type}"
            
        return tile

    @staticmethod
    def merge_tiles(base_tile: HexTile, feeder_tile: HexTile) -> bool:
        """
        Merges feeder_tile into base_tile.
        Returns True if successful.
        """
        if base_tile.tile_type != feeder_tile.tile_type:
            return False
            
        # Calculate bonus based on feeder rarity
        # Common: 1%, Uncommon: 5%, Rare: 10%, Epic: 25%, Legendary: 50%
        bonus_map = {
            "Common": 0.01,
            "Uncommon": 0.05,
            "Rare": 0.10,
            "Epic": 0.25,
            "Legendary": 0.50
        }
        
        bonus = bonus_map.get(feeder_tile.quality, 0.01)
        
        # Apply bonus
        base_tile.merge_bonus += bonus
        base_tile.merge_count += 1
        
        # Check for Rarity Upgrade
        # Threshold: 50% bonus (0.50) triggers upgrade to next rarity?
        # User said: "once the % bonus gets to 50% it upgrades to the next rarity"
        # And "each subsequent conduit merged... adds another 1%"
        
        # Let's check if we crossed a threshold
        # We need to reset bonus or keep it? 
        # "upgrades to the next rarity" usually implies base stats increase.
        
        current_rarity_idx = LootManager.RARITIES.index(base_tile.quality)
        if current_rarity_idx < len(LootManager.RARITIES) - 1:
            # Check if we have enough bonus for upgrade
            # Let's say every 0.5 (50%) accumulated bonus triggers an upgrade
            # But we should probably consume that bonus into base stats?
            
            if base_tile.merge_bonus >= 0.50:
                # Upgrade!
                new_rarity = LootManager.RARITIES[current_rarity_idx + 1]
                base_tile.quality = new_rarity
                base_tile.name = f"{new_rarity} {base_tile.tile_type}"
                base_tile.merge_bonus -= 0.50 # Consume bonus
                
                # Improve base stats
                if isinstance(base_tile, AmplifierTile):
                    base_tile.amplification += 0.2 # Big jump
                # Add other stat upgrades here
                
                return True
                
        return True
