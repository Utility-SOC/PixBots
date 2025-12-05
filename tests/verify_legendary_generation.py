
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from equipment.component import create_random_component
from hex_system.hex_tile import AmplifierTile, BasicConduitTile

def verify_legendary_generation():
    print("Generating Legendary Weapon...")
    comp = create_random_component("Legendary", "right_arm")
    
    print(f"Generated: {comp.name}")
    print(f"Total Tiles: {len(comp.tile_slots)}")
    
    amplifiers = [t for t in comp.tile_slots.values() if isinstance(t, AmplifierTile)]
    conduits = [t for t in comp.tile_slots.values() if isinstance(t, BasicConduitTile) and not isinstance(t, AmplifierTile)]
    
    print(f"Amplifiers: {len(amplifiers)}")
    print(f"Conduits: {len(conduits)}")
    
    # Check if we have a path
    # We can't easily visualize here, but having Amplifiers is a good sign.
    if len(amplifiers) > 0:
        print("SUCCESS: Amplifiers present on Legendary item.")
    else:
        print("FAILURE: No Amplifiers found on Legendary item.")

    # Check for Super Conduits
    super_conduits = [t for t in conduits if getattr(t, 'name', '') == "Super Conduit"]
    print(f"Super Conduits: {len(super_conduits)}")
    
    if len(super_conduits) > 0:
         print("SUCCESS: Super Conduits present.")

if __name__ == "__main__":
    verify_legendary_generation()
