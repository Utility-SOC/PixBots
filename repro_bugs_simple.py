
import sys
from unittest.mock import MagicMock

# Mock pygame
sys.modules["pygame"] = MagicMock()

from equipment.component import ComponentEquipment
from hex_system.hex_tile import WeaponMountTile, TileCategory, BasicConduitTile
from hex_system.hex_coord import HexCoord
from hex_system.energy_packet import ProjectileContext, SynergyType

def test_kinetic():
    print("\n--- Testing Kinetic Magnitude ---")
    comp = ComponentEquipment(name="KineticGun", slot="right_arm", grid_width=3, grid_height=3)
    comp.valid_coords = {HexCoord(0,0), HexCoord(1,0)}
    comp.tile_slots[HexCoord(0,0)] = BasicConduitTile("Conduit", TileCategory.CONDUIT)
    comp.tile_slots[HexCoord(1,0)] = WeaponMountTile("Gun", TileCategory.OUTPUT)
    
    ctx = ProjectileContext(synergies={SynergyType.KINETIC: 100.0})
    _, stats, _ = comp.simulate_flow(input_context=ctx, input_direction=3)
    
    magnitudes = stats.get("synergy_magnitudes", {})
    print(f"Magnitudes: {magnitudes}")
    
    if magnitudes.get("kinetic") == 100.0:
        print("PASS: Kinetic Magnitude")
    else:
        print("FAIL: Kinetic Magnitude")

def test_vampiric():
    print("\n--- Testing Vampirism Power ---")
    comp = ComponentEquipment(name="VampGun", slot="right_arm", grid_width=3, grid_height=3)
    comp.valid_coords = {HexCoord(0,0), HexCoord(1,0)}
    comp.tile_slots[HexCoord(0,0)] = BasicConduitTile("Conduit", TileCategory.CONDUIT)
    comp.tile_slots[HexCoord(1,0)] = WeaponMountTile("Gun", TileCategory.OUTPUT)
    
    ctx = ProjectileContext(synergies={SynergyType.VAMPIRIC: 100.0})
    _, stats, _ = comp.simulate_flow(input_context=ctx, input_direction=3)
    
    effects = stats.get("active_synergy_effects", {})
    print(f"Effects: {effects}")
    
    if "vampiric_power" in effects and effects["vampiric_power"] == 100.0:
        print("PASS: Vampiric Power")
    else:
        print("FAIL: Vampiric Power")

if __name__ == "__main__":
    try:
        test_kinetic()
        test_vampiric()
    except Exception as e:
        import traceback
        traceback.print_exc()
