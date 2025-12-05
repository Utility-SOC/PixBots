import sys
import os
import pygame

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hex_system.energy_packet import ProjectileContext, SynergyType, ProjectileModifier
from hex_system.hex_tile import SplitterTile, AmplifierTile, HexTile
from systems.loot_manager import LootManager
from systems.visual_compositor import VisualCompositor

def test_projectile_flow():
    print("Testing Projectile Flow...")
    
    # Test Splitter
    splitter = SplitterTile()
    ctx = ProjectileContext(damage_multiplier=1.0)
    
    results = splitter.process_energy(ctx, 0)
    
    if len(results) == 2:
        print("PASS: Splitter produced 2 contexts.")
    else:
        print(f"FAIL: Splitter produced {len(results)} contexts.")
        
    # Check split penalty/logic
    # We added a modifier for split penalty
    if results[0].modifiers:
        print(f"PASS: Splitter added modifier: {results[0].modifiers[0]}")
    else:
        print("FAIL: Splitter did not add modifier.")

def test_merging_logic():
    print("\nTesting Merging Logic...")
    
    base = AmplifierTile(amplification=1.2)
    base.quality = "Common"
    
    feeder = AmplifierTile(amplification=1.2)
    feeder.quality = "Common" # Adds 0.01 bonus
    
    # Merge 1
    LootManager.merge_tiles(base, feeder)
    
    if abs(base.merge_bonus - 0.01) < 0.0001:
        print("PASS: Merge added 0.01 bonus.")
    else:
        print(f"FAIL: Merge bonus is {base.merge_bonus}, expected 0.01")
        
    # Merge until upgrade
    # We need 0.50 total bonus. We have 0.01. Need 49 more.
    for _ in range(49):
        LootManager.merge_tiles(base, feeder)
        
    if base.quality == "Uncommon":
        print("PASS: Rarity upgraded to Uncommon.")
        print(f"PASS: Merge bonus reset/consumed: {base.merge_bonus}")
    else:
        print(f"FAIL: Rarity is {base.quality}, expected Uncommon. Bonus: {base.merge_bonus}")

def test_visual_compositor():
    print("\nTesting Visual Compositor...")
    pygame.init()
    try:
        comp = VisualCompositor(None)
        img = comp.compose_weapon("basic_barrel", "basic_body", "basic_stock", (255, 0, 0))
        if img:
            print("PASS: VisualCompositor returned an image.")
            # Save for manual inspection if needed
            pygame.image.save(img, "test_output_weapon.png")
        else:
            print("FAIL: VisualCompositor returned None.")
    except Exception as e:
        print(f"FAIL: VisualCompositor crashed: {e}")

if __name__ == "__main__":
    test_projectile_flow()
    test_merging_logic()
    test_visual_compositor()
