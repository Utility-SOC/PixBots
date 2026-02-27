# G:\work\pixelbots\constants.py
import os
import sys

# Core Game Info
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
CAPTION = "Pixbots"
FPS = 60

# Game States
STATE_MENU = "menu"
STATE_PLAY = "play"
STATE_PAUSE = "pause"
STATE_GARAGE = "garage"
STATE_MISSION_SELECT = "mission_select"
STATE_MISSION_SUMMARY = "mission_summary"
STATE_COMPONENT_VIEWER = "component_viewer"
STATE_HEX_EDITOR = "hex_editor"
STATE_CRAFTING = "crafting"
STATE_DEBUG_SPAWN = "debug_spawn"
STATE_DEBUG_BIOME = "debug_biome"
STATE_COMBAT = "combat"
STATE_EQUIPMENT = "equipment"
STATE_REACTOR = "reactor"  # Debug reactor menu
STATE_HELP = "help"
STATE_SAVE_SLOT = "save_slot"

# Combat Constants
PROJECTILE_SPEED = 300
PROJECTILE_LIFETIME = 2.0
DAMAGE_TYPE_PHYSICAL = "physical"
DAMAGE_TYPE_ENERGY = "energy"


# Core Sizes
TILE_SIZE = 32

# Directories
def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

ASSETS_DIR = get_resource_path("assets")
DATA_DIR = get_resource_path("data")
SAVES_DIR = "saves"
SPRITES_DIR = os.path.join(ASSETS_DIR, "sprites")

# Terrain Types
GRASS, WATER, MOUNTAIN, DESERT, FOREST, TUNDRA, VOLCANO = range(7)
NON_WALKABLE_TERRAIN = {WATER, MOUNTAIN}
