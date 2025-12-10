
import sys
from unittest.mock import MagicMock

# Mock pygame
sys.modules["pygame"] = MagicMock()

from equipment.component import ComponentEquipment
from hex_system.hex_tile import WeaponMountTile, TileCategory, BasicConduitTile
from hex_system.hex_coord import HexCoord
from hex_system.energy_packet import ProjectileContext, SynergyType

def test_kinetic_key():
    print("\n--- Testing Kinetic Key Type ---")
    comp = ComponentEquipment(name="KineticGun", slot="right_arm", grid_width=3, grid_height=3)
    comp.valid_coords = {HexCoord(0,0), HexCoord(1,0)}
    comp.tile_slots[HexCoord(0,0)] = BasicConduitTile("Conduit", TileCategory.CONDUIT)
    comp.tile_slots[HexCoord(1,0)] = WeaponMountTile("Gun", TileCategory.OUTPUT)
    
    ctx = ProjectileContext(synergies={SynergyType.KINETIC: 100.0})
    _, stats, _ = comp.simulate_flow(input_context=ctx, input_direction=3)
    
    magnitudes = stats.get("synergy_magnitudes", {})
    print(f"Magnitudes keys: {list(magnitudes.keys())}")
    
    if "kinetic" in magnitudes:
        print("PASS: 'kinetic' string key found")
    else:
        print("FAIL: 'kinetic' string key NOT found")

if __name__ == "__main__":
    test_kinetic_key()
