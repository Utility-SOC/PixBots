# pixbots_enhanced/world/biome.py
# CORRECTED to be a stable, importable module.

import json
import os
import random
import math
import logging

try:
    from noise import pnoise2
except ImportError:
    logging.warning("'noise' library not found. Falling back to basic math functions for world gen.")
    def pnoise2(x, y, octaves=1, persistence=0.5, lacunarity=2.0, repeatx=1024, repeaty=1024, base=0):
        return (math.sin(x/10.0 + base) + math.cos(y/10.0 + base)) / 2.0

logger = logging.getLogger(__name__)

# Terrain constants
GRASS, WATER, MOUNTAIN, DESERT, FOREST, TUNDRA, VOLCANO = range(7)

TERRAIN_NAMES = {
    GRASS: "Grass", WATER: "Water", MOUNTAIN: "Mountain", DESERT: "Desert",
    FOREST: "Forest", TUNDRA: "Tundra", VOLCANO: "Volcano"
}

class BiomeManager:
    """Manages biome generation, characteristics, and transitions."""
    
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randint(0, 999999)
        random.seed(self.seed)
        self.current_biome = "grassland"
        self.biome_data = {}
        self.load_biome_data()
        
        self.biome_noise_scale = 0.05
        self.terrain_noise_scale = 0.1
        self.forced_biome = None # New attribute to force a specific biome
        logger.info(f"BiomeManager initialized with seed {self.seed}.")
        
    def load_biome_data(self):
        """Load biome definitions from JSON file, with a robust fallback."""
        try:
            # Assumes a 'data' folder in the project root
            with open(os.path.join("data", "biomes.json"), "r") as f:
                self.biome_data = json.load(f)
            logger.info("Loaded biome data from biomes.json.")
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning("biomes.json not found or invalid. Creating default biome data.")
            self.biome_data = self._create_default_biomes()
            try:
                os.makedirs("data", exist_ok=True)
                with open(os.path.join("data", "biomes.json"), "w") as f:
                    json.dump(self.biome_data, f, indent=2)
            except Exception as e:
                logger.error(f"Could not write default biomes.json: {e}")

    def get_biome_type(self, x, y):
        """Determine biome type based on position in the world."""
        if self.forced_biome:
            return self.forced_biome

        noise_val = pnoise2(x * self.biome_noise_scale, y * self.biome_noise_scale, 
                           octaves=3, persistence=0.5, lacunarity=2.0, base=self.seed % 255)
        noise_val = (noise_val + 1) / 2 # Normalize to 0-1
        
        if noise_val < 0.2: return "desert"
        elif noise_val < 0.4: return "grassland"
        elif noise_val < 0.6: return "forest"
        elif noise_val < 0.8: return "tundra"
        else: return "volcano"
    
    def get_terrain_type(self, x, y, biome_type=None, map_width=100, map_height=100):
        """Determine terrain type based on position and biome."""
        if biome_type is None:
            biome_type = self.get_biome_type(x, y)
        
        biome_info = self.biome_data.get(biome_type, self.biome_data["grassland"])
        
        terrain_noise = pnoise2(x * self.terrain_noise_scale, y * self.terrain_noise_scale, 
                               octaves=4, persistence=0.7, lacunarity=2.0, base=(self.seed + 10) % 255)
        terrain_noise = (terrain_noise + 1) / 2
        
        # Special Island Logic
        if biome_type == "island":
            cx, cy = map_width / 2, map_height / 2
            max_dist = min(map_width, map_height) * 0.5
            dist = math.sqrt((x - cx)**2 + (y - cy)**2)
            normalized_dist = dist / max_dist
            
            # Radial mask: 1 at center, 0 at edge
            mask = 1.0 - normalized_dist
            
            # Combine noise with mask. 
            # If mask is high (center), we want land. If low (edge), water.
            # terrain_noise is 0-1. 
            # Let's say value = terrain_noise * 0.3 + mask * 0.7
            value = terrain_noise * 0.3 + mask * 0.7
            
            if value < 0.4: return WATER
            elif value > 0.85: return MOUNTAIN
            else: return GRASS

        water_threshold = biome_info.get("water_threshold", 0.3)
        mountain_threshold = biome_info.get("mountain_threshold", 0.7)
        
        if terrain_noise < water_threshold: return WATER
        elif terrain_noise > mountain_threshold: return MOUNTAIN
        
        return {"desert": DESERT, "forest": FOREST, "tundra": TUNDRA, 
                "volcano": VOLCANO}.get(biome_type, GRASS)

    def get_biome_color(self, x, y, terrain_type=None):
        """Get the color for a specific position based on terrain and biome."""
        biome_type = self.get_biome_type(x, y)
        if terrain_type is None:
            terrain_type = self.get_terrain_type(x, y, biome_type)
        
        biome_info = self.biome_data.get(biome_type, self.biome_data["grassland"])
        
        if terrain_type == WATER: base_color = biome_info.get("water_color", [50, 100, 200])
        elif terrain_type == MOUNTAIN: base_color = biome_info.get("mountain_color", [120, 120, 120])
        else: base_color = biome_info.get("base_color", [50, 180, 50])
        
        variation = int(pnoise2(x * 0.5, y * 0.5, base=(self.seed + 20) % 255) * 15)
        r = max(0, min(255, base_color[0] + variation))
        g = max(0, min(255, base_color[1] + variation))
        b = max(0, min(255, base_color[2] + variation))
        
        return (r, g, b)
    
    def should_spawn_obstacle(self, x, y):
        """Determine if an obstacle should spawn at the given location."""
        biome_type = self.get_biome_type(x, y)
        biome_info = self.biome_data.get(biome_type, self.biome_data["grassland"])
        obstacle_chance = biome_info.get("obstacle_chance", 0.1)
        
        obstacle_noise = pnoise2(x * 0.2, y * 0.2, octaves=1, base=(self.seed + 30) % 255)
        return ((obstacle_noise + 1) / 2) < obstacle_chance
    
    def get_obstacle_type(self, x, y):
        """Get the type of obstacle to spawn at a given location."""
        biome_type = self.get_biome_type(x, y)
        biome_info = self.biome_data.get(biome_type, self.biome_data["grassland"])
        obstacle_types = biome_info.get("obstacle_types", ["Boulder", "Tree"])
        if not obstacle_types: return "Boulder" # Fallback
        
        selection_seed = hash((x, y, self.seed)) % len(obstacle_types)
        return obstacle_types[selection_seed]
    
    def _create_default_biomes(self):
        """Returns a dictionary of default biome data."""
        return {
            "grassland": {
                "name": "Grassland", "base_color": [50, 180, 50],
                "water_color": [50, 100, 200], "mountain_color": [120, 120, 120],
                "obstacle_chance": 0.1, "water_threshold": 0.3, "mountain_threshold": 0.7,
                "obstacle_types": ["Boulder", "Tree"]
            },
            "desert": {
                "name": "Desert", "base_color": [210, 180, 140],
                "water_color": [90, 140, 200], "mountain_color": [180, 160, 120],
                "obstacle_chance": 0.05, "water_threshold": 0.1, "mountain_threshold": 0.8,
                "obstacle_types": ["Boulder", "Cactus"]
            },
            "tundra": {
                "name": "Tundra", "base_color": [220, 220, 240],
                "water_color": [150, 200, 255], "mountain_color": [180, 180, 210],
                "obstacle_chance": 0.08, "water_threshold": 0.4, "mountain_threshold": 0.65,
                "obstacle_types": ["IceBoulder", "FrozenTree"]
            },
            "forest": {
                "name": "Forest", "base_color": [34, 139, 34],
                "water_color": [30, 144, 255], "mountain_color": [110, 139, 61],
                "obstacle_chance": 0.2, "water_threshold": 0.35, "mountain_threshold": 0.75,
                "obstacle_types": ["Tree", "ThickTree"]
            },
            "volcano": {
                "name": "Volcanic", "base_color": [100, 40, 40],
                "water_color": [200, 50, 10], "mountain_color": [80, 30, 30],
                "obstacle_chance": 0.15, "water_threshold": 0.2, "mountain_threshold": 0.6,
                "obstacle_types": ["LavaRock", "ObsidianSpire"]
            },
            "island": {
                "name": "Island", "base_color": [255, 255, 150], # Sandy
                "water_color": [0, 100, 200], "mountain_color": [100, 100, 100],
                "obstacle_chance": 0.1, "water_threshold": 0.4, "mountain_threshold": 0.8,
                "obstacle_types": ["Tree", "Boulder"]
            },
            "mountainous": {
                "name": "Mountainous", "base_color": [100, 100, 100], # Grey
                "water_color": [50, 50, 100], "mountain_color": [200, 200, 200], # Snowy peaks
                "obstacle_chance": 0.4, "water_threshold": 0.1, "mountain_threshold": 0.4, # Low threshold = lots of mountains
                "obstacle_types": ["Boulder", "IceBoulder"]
            },
            "beach": {
                "name": "Beach", "base_color": [240, 230, 140], # Khaki/Sand
                "water_color": [0, 150, 255], "mountain_color": [100, 100, 100],
                "obstacle_chance": 0.05, "water_threshold": 0.5, "mountain_threshold": 0.95, # Mostly water and sand
                "obstacle_types": ["Cactus", "Tree"] # Palm trees? Using Tree for now
            },
            "meadow": {
                "name": "Meadow", "base_color": [100, 200, 100], # Bright Green
                "water_color": [100, 150, 255], "mountain_color": [150, 150, 150],
                "obstacle_chance": 0.05, "water_threshold": 0.25, "mountain_threshold": 0.85, # Open space
                "obstacle_types": ["Tree", "Boulder"]
            }
        }
