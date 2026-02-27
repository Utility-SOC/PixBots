import json
import os

target_file = r"g:\work\pixelbots\equipment\component.py"

with open(target_file, "r") as f:
    original_code = f.read()

# We want to replace everything from '# --- Factory Functions ---' to the end of the file.
split_token = "# --- Factory Functions ---"
parts = original_code.split(split_token)

if len(parts) != 2:
    print("Could not find the split token exactly once.")
    exit(1)

top_part = parts[0]

new_bottom_part = """# --- Factory Functions ---
import json
import os
import random
from hex_system.hex_coord import HexCoord

_COMPONENT_DATA = None

def _load_component_data():
    global _COMPONENT_DATA
    if _COMPONENT_DATA is None:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_path = os.path.join(base_path, "data", "components.json")
        try:
            with open(data_path, 'r') as f:
                _COMPONENT_DATA = json.load(f)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to load components.json: {e}")
            _COMPONENT_DATA = {"starter": {}, "shapes": {}}

def _create_from_template(category: str, template_id: str) -> 'ComponentEquipment':
    _load_component_data()
    data = _COMPONENT_DATA.get(category, {}).get(template_id)
    if not data:
        # Fallback
        return ComponentEquipment(name=f"Fallback {template_id}", slot=template_id)
    
    comp = ComponentEquipment(
        name=data.get("name", "Unknown"),
        slot=data.get("slot", "torso"),
        quality=data.get("quality", "Common"),
        base_armor=data.get("base_armor", 0),
        base_hp=data.get("base_hp", 0)
    )
    
    comp.valid_coords = {HexCoord(c[0], c[1]) for c in data.get("valid_coords", [])}
    
    from hex_system.hex_tile import HexTile, ReactorTile, ResonatorTile, SplitterTile, WeaponMountTile, AmplifierTile, TileCategory
    from hex_system.energy_packet import EnergyCore, SynergyType
    
    if "core" in data:
        cdata = data["core"]
        ctype = getattr(SynergyType, cdata["type"].upper(), SynergyType.RAW)
        comp.core = EnergyCore(core_type=ctype, generation_rate=cdata["rate"], position=HexCoord(cdata["pos"][0], cdata["pos"][1]))
    
    fill_tile_type = data.get("fill_tile", "Conductor")
    
    # Place special tiles
    for tdata in data.get("tiles", []):
        pos = HexCoord(tdata["pos"][0], tdata["pos"][1])
        ttype = tdata["type"]
        tile = None
        if ttype == "Reactor": tile = ReactorTile()
        elif ttype == "Resonator": tile = ResonatorTile()
        elif ttype == "Splitter": tile = SplitterTile()
        elif ttype == "Amplifier": tile = AmplifierTile()
        elif ttype == "Weapon Mount":
            cat = getattr(TileCategory, tdata.get("category", "OUTPUT"))
            tile = WeaponMountTile(tile_type="Weapon Mount", category=cat, weapon_type=tdata.get("weapon_type", "beam"))
        
        if tile:
            comp.place_tile(pos, tile)
            
    # Fill remaining
    for coord in comp.valid_coords:
        if coord not in comp.tile_slots:
            comp.place_tile(coord, HexTile(tile_type=fill_tile_type, description="Conducts energy."))
            
    return comp

def create_starter_torso() -> 'ComponentEquipment':
    return _create_from_template("starter", "torso")

def create_starter_arm(slot: str) -> 'ComponentEquipment':
    if slot not in ["left_arm", "right_arm"]:
        raise ValueError("Arm slot must be 'left_arm' or 'right_arm'")
    return _create_from_template("starter", slot)

def create_starter_leg(slot: str) -> 'ComponentEquipment':
    if slot not in ["left_leg", "right_leg"]:
        raise ValueError("Leg slot must be 'left_leg' or 'right_leg'")
    return _create_from_template("starter", slot)

def create_starter_head() -> 'ComponentEquipment':
    return _create_from_template("starter", "head")

def create_starter_back() -> 'ComponentEquipment':
    return _create_from_template("starter", "back")

def create_random_component(rarity: str = "Common", slot: str = None) -> 'ComponentEquipment':
    _load_component_data()
    slots = ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "back"]
    if slot is None:
        slot = random.choice(slots)
        
    base_armor = random.randint(1, 5)
    base_hp = random.randint(10, 50)
    base_speed = 0.0
    
    if rarity == "Uncommon":
        base_armor += 2; base_hp += 20
    elif rarity == "Rare":
        base_armor += 5; base_hp += 50
    elif rarity == "Epic":
        base_armor += 10; base_hp += 100
    elif rarity == "Legendary":
        base_armor += 20; base_hp += 200
        
    comp = ComponentEquipment(name=f"{rarity} {slot}", slot=slot, quality=rarity, base_armor=base_armor, base_hp=base_hp, base_speed=base_speed)
    
    shapes = _COMPONENT_DATA.get("shapes", {})
    # Map arm/leg to slot
    shape_key = slot
    if "arm" in slot: shape_key = "arm"
    if "leg" in slot: shape_key = "leg"
    
    rarity_shapes = shapes.get(shape_key, {}).get(rarity, shapes.get(shape_key, {}).get("Common", []))
    if not rarity_shapes:
        rarity_shapes = [{"w": 3, "h": 3, "remove": []}] # fallback
        
    shape = random.choice(rarity_shapes)
    valid_coords = set()
    
    if "coords" in shape:
        valid_coords = {HexCoord(c[0], c[1]) for c in shape["coords"]}
    else:
        for q in range(shape.get("w", 3)):
            for r in range(shape.get("h", 3)):
                valid_coords.add(HexCoord(q, r))
        for r_coord in shape.get("remove", []):
            rc = HexCoord(r_coord[0], r_coord[1])
            if rc in valid_coords: valid_coords.remove(rc)
        for a_coord in shape.get("add", []):
            valid_coords.add(HexCoord(a_coord[0], a_coord[1]))
            
    comp.valid_coords = valid_coords
    qs = [c.q for c in valid_coords]
    rs = [c.r for c in valid_coords]
    if valid_coords:
        comp.grid_width = max(qs) - min(qs) + 1
        comp.grid_height = max(rs) - min(rs) + 1
        comp.max_tile_capacity = len(valid_coords)
    
    from hex_system.hex_tile import HexTile, AmplifierTile, ResonatorTile, WeaponMountTile, TileCategory, SplitterTile
    
    if "arm" in slot:
        entry, exit_hex = comp.get_entry_exit_hexes()
        mount_pos = exit_hex if exit_hex else HexCoord(1, 1)
        if mount_pos not in comp.valid_coords:
            if valid_coords:
                mount_pos = list(comp.valid_coords)[-1]
            else:
                mount_pos = HexCoord(0,0)
        comp.place_tile(mount_pos, WeaponMountTile(tile_type="Weapon Mount", category=TileCategory.OUTPUT, weapon_type="beam"))
        
    if slot == "torso":
        from hex_system.energy_packet import EnergyCore, SynergyType
        syn_type = random.choice(list(SynergyType))
        rate = {"Common": 10.0, "Uncommon": 20.0, "Rare": 40.0, "Epic": 70.0, "Legendary": 100.0}.get(rarity, 10.0)
        comp.core = EnergyCore(generation_rate=rate, core_type=syn_type)
        
        if valid_coords:
            center_q = sum(qs) // len(qs)
            center_r = sum(rs) // len(rs)
            center = HexCoord(center_q, center_r)
            if center not in comp.valid_coords:
                center = list(comp.valid_coords)[0]
        else:
            center = HexCoord(0,0)
            
        comp.core.position = center
        from hex_system.hex_tile import ReactorTile
        comp.place_tile(center, ReactorTile())
        
    chance_amp = {"Uncommon": 0.1, "Rare": 0.2, "Epic": 0.3, "Legendary": 0.4}.get(rarity, 0.0)
    chance_res = {"Uncommon": 0.0, "Rare": 0.1, "Epic": 0.2, "Legendary": 0.3}.get(rarity, 0.0)
    
    for coord in comp.valid_coords:
        if coord not in comp.tile_slots:
            roll = random.random()
            if roll < chance_amp: tile = AmplifierTile()
            elif roll < chance_amp + chance_res: tile = ResonatorTile()
            else: tile = HexTile(tile_type="Conductor", description="Conducts energy.")
            comp.place_tile(coord, tile)
            
    return comp
"""

with open(target_file, "w") as f:
    f.write(top_part + new_bottom_part)
print("Updated component.py successfully.")
