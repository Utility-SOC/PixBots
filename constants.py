# G:\work\pixelbots\constants.py
import os

# Core Game Info
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
CAPTION = "Pixbots"
FPS = 60

# Game States
STATE_MENU = "menu"
STATE_PLAY = "play"
STATE_PAUSE = "pause"
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
ASSETS_DIR = "assets"
DATA_DIR = "data"
SAVES_DIR = "saves"
SPRITES_DIR = os.path.join(ASSETS_DIR, "sprites")

# Terrain Types
GRASS, WATER, MOUNTAIN, DESERT, FOREST, TUNDRA, VOLCANO = range(7)
NON_WALKABLE_TERRAIN = {WATER, MOUNTAIN}
