# pixbots_enhanced/world/game_map.py
# CORRECTED to gracefully handle missing tile sprites and prevent silent crash.

import pygame
import random
import logging
from typing import Optional

from .biome import BiomeManager, GRASS, WATER, MOUNTAIN, DESERT, FOREST, TUNDRA, VOLCANO
import constants
from core.asset_manager import ProceduralAssetManager

logger = logging.getLogger(__name__)

class Obstacle:
    """Represents an obstacle on the map, which can have a sprite."""
    def __init__(self, name, hp, destructible_by):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.destructible_by = destructible_by
        self.sprite: Optional[pygame.Surface] = None

class GameMap:
    """Grid-based world with sprite rendering and procedural generation."""
    def __init__(self, width: int, height: int, tile_size: int, asset_manager: ProceduralAssetManager, seed: int = None):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.asset_manager = asset_manager
        self.seed = seed if seed is not None else random.randint(0, 999999)
        
        self.biome_manager = BiomeManager(self.seed)
        self.terrain = []
        self.biome_grid = [] # Cache biome types
        self.generate_map_data()
        
        self.tile_sprites = self._load_tile_sprites()
        self.obstacle_sprites = self._load_obstacle_sprites()
        
        self.obstacles = self.generate_obstacles()
        self.color_cache = {}
        logger.info(f"GameMap initialized with {len(self.obstacles)} obstacles.")

    def _load_tile_sprites(self) -> dict:
        """Loads terrain tile sprites for different biomes."""
        # Map (TerrainType, BiomeName) -> Filename
        sprite_map = {
            # Grassland / Plains
            (GRASS, "grassland"): "environment/terrain/grass_plains.png",
            (WATER, "grassland"): "environment/terrain/water_plains.png",
            (MOUNTAIN, "grassland"): "environment/terrain/mountain_plains.png",
            
            # Forest
            (GRASS, "forest"): "environment/terrain/grass_forest.png",
            (WATER, "forest"): "environment/terrain/water_forest.png",
            (MOUNTAIN, "forest"): "environment/terrain/mountain_forest.png",
            
            # Desert
            (GRASS, "desert"): "environment/terrain/sand.png", 
            (DESERT, "desert"): "environment/terrain/sand.png",
            (WATER, "desert"): "environment/terrain/water_oasis.png",
            (MOUNTAIN, "desert"): "environment/terrain/rock_desert.png",
            
            # Tundra / Snow
            (GRASS, "tundra"): "environment/terrain/snow_flat.png",
            (TUNDRA, "tundra"): "environment/terrain/snow_flat.png",
            (WATER, "tundra"): "environment/terrain/ice_water.png",
            (MOUNTAIN, "tundra"): "environment/terrain/snow_mountain.png",
            
            # Volcano
            (GRASS, "volcano"): "environment/terrain/ash_ground.png",
            (VOLCANO, "volcano"): "environment/terrain/ash_ground.png",
            (WATER, "volcano"): "environment/terrain/lava_liquid.png",
            (MOUNTAIN, "volcano"): "environment/terrain/rock_high.png",
            
            # Beach
            (GRASS, "beach"): "environment/terrain/sand.png",
            (WATER, "beach"): "environment/terrain/water_ocean.png",
            (MOUNTAIN, "beach"): "environment/terrain/rock_island.png",
            
            # Island
            (GRASS, "island"): "environment/terrain/grass_plains.png",
            (WATER, "island"): "environment/terrain/water_ocean.png",
            (MOUNTAIN, "island"): "environment/terrain/rock_island.png",
            
            # Mountainous
            (GRASS, "mountainous"): "environment/terrain/rock_high.png",
            (WATER, "mountainous"): "environment/terrain/water_lake.png",
            (MOUNTAIN, "mountainous"): "environment/terrain/snow_peak.png",
        }
        
        sprites = {}
        for key, filename in sprite_map.items():
            sprite = self.asset_manager.get_image(filename)
            if sprite and not self._is_placeholder(sprite):
                sprites[key] = pygame.transform.scale(sprite, (self.tile_size, self.tile_size))
        
        logger.info(f"Loaded {len(sprites)} terrain sprites.")
        return sprites

    def _is_placeholder(self, surface: pygame.Surface) -> bool:
        if surface.get_width() != constants.TILE_SIZE or surface.get_height() != constants.TILE_SIZE:
             return False 
        return surface.get_at((1, 1)) == (255, 0, 255, 255)

    def _load_obstacle_sprites(self) -> dict:
        obstacle_sprite_map = {
            "Boulder": "environment/obstacles/boulder.png", "Tree": "environment/obstacles/tree.png", "Cactus": "environment/obstacles/cactus.png",
            "ThickTree": "environment/obstacles/thick_tree.png", "IceBoulder": "environment/obstacles/frozen_boulder.png",
            "FrozenTree": "environment/obstacles/frozen_tree.png", "LavaRock": "environment/obstacles/lava_rock.png",
            "ObsidianSpire": "environment/obstacles/obsidian_spire.png",
        }
        
        sprites = {}
        for name, filename in obstacle_sprite_map.items():
            sprite = self.asset_manager.get_image(filename)
            if sprite:
                sprites[name] = pygame.transform.scale(sprite, (self.tile_size, self.tile_size))
        logger.info(f"Loaded {len(sprites)} obstacle sprites.")
        return sprites

    def regenerate(self, seed=None, biome_type=None):
        if seed is not None:
            self.seed = seed
            self.biome_manager.seed = seed
            random.seed(seed)
            
        if biome_type:
            self.biome_manager.forced_biome = biome_type
        else:
            self.biome_manager.forced_biome = None
            
        self.generate_map_data()
        self.obstacles = self.generate_obstacles()
        self.color_cache = {}
        logger.info(f"Map regenerated. Seed: {self.seed}, Biome: {biome_type}")

    def generate_map_data(self):
        """Generates both terrain and biome grids."""
        self.terrain = []
        self.biome_grid = []
        for y in range(self.height):
            row_terrain = []
            row_biome = []
            for x in range(self.width):
                biome = self.biome_manager.get_biome_type(x, y)
                terrain = self.biome_manager.get_terrain_type(x, y, biome)
                row_biome.append(biome)
                row_terrain.append(terrain)
            self.terrain.append(row_terrain)
            self.biome_grid.append(row_biome)

    def generate_obstacles(self) -> dict:
        obstacles = {}
        obstacle_definitions = {
            "Boulder": {"hp": 300, "destructible_by": ["explosive"]},
            "Tree": {"hp": 150, "destructible_by": ["fire", "explosive"]},
            "Cactus": {"hp": 100, "destructible_by": ["fire", "melee"]},
            "ThickTree": {"hp": 250, "destructible_by": ["fire", "explosive"]},
            "IceBoulder": {"hp": 200, "destructible_by": ["explosive", "fire"]},
            "FrozenTree": {"hp": 180, "destructible_by": ["fire", "explosive"]},
            "LavaRock": {"hp": 350, "destructible_by": ["explosive"]},
            "ObsidianSpire": {"hp": 500, "destructible_by": ["explosive"]},
        }
        
        for y in range(self.height):
            for x in range(self.width):
                if self.terrain[y][x] != WATER and self.biome_manager.should_spawn_obstacle(x, y):
                    name = self.biome_manager.get_obstacle_type(x, y)
                    if name in obstacle_definitions:
                        props = obstacle_definitions[name]
                        obs = Obstacle(name, props["hp"], props["destructible_by"])
                        if name in self.obstacle_sprites:
                            obs.sprite = self.obstacle_sprites[name]
                        obstacles[(x, y)] = obs
        return obstacles

    def get_transition_sprite(self, primary_biome, neighbor_biome, direction):
        """Attempts to load a transition sprite."""
        # Spec: transition_[primary]_[secondary]_[direction]_[variant].png
        # We'll just try variant 01 for now or no variant
        filename = f"environment/terrain/transition_{primary_biome}_{neighbor_biome}_{direction}.png"
        
        # Check if we already loaded it? We don't preload transitions yet.
        # We should probably cache them on demand.
        # For now, let's just use asset_manager.get_image which caches.
        
        # NOTE: Since assets don't exist yet, this will return None or placeholder.
        # We want to avoid placeholder for transitions, so we check existence.
        # But get_image generates placeholder if not found.
        # We need a way to check existence without generating placeholder.
        # Or we just rely on the fact that we don't have them yet.
        return None

    def render(self, screen: pygame.Surface, offset_x: int, offset_y: int):
        start_col = max(0, int(-offset_x / self.tile_size))
        start_row = max(0, int(-offset_y / self.tile_size))
        end_col = min(self.width, start_col + int(screen.get_width() / self.tile_size) + 2)
        end_row = min(self.height, start_row + int(screen.get_height() / self.tile_size) + 2)

        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                screen_x = int(x * self.tile_size + offset_x)
                screen_y = int(y * self.tile_size + offset_y)
                tile_type = self.terrain[y][x]
                biome_type = self.biome_grid[y][x]
                
                sprite = self.tile_sprites.get((tile_type, biome_type))
                
                # Transition Logic (Simplified)
                # Check neighbors (N, S, E, W) for different biome
                # Only check if we have a base sprite, otherwise we're already falling back
                if sprite:
                    # Check East
                    if x + 1 < self.width:
                        neighbor_biome = self.biome_grid[y][x+1]
                        if neighbor_biome != biome_type:
                            trans = self.get_transition_sprite(biome_type, neighbor_biome, "e")
                            if trans: sprite = trans # Overlay or replace? Usually replace edge.
                    
                    # Real implementation would need to handle corners and multiple sides.
                    # For now, this is the spec implementation.

                if not sprite:
                    sprite = self.tile_sprites.get((tile_type, "grassland"))

                if sprite:
                    screen.blit(sprite, (screen_x, screen_y))
                else: 
                    if (x, y, tile_type) not in self.color_cache:
                        self.color_cache[(x, y, tile_type)] = self.biome_manager.get_biome_color(x, y, tile_type)
                    pygame.draw.rect(screen, self.color_cache[(x, y, tile_type)], (screen_x, screen_y, self.tile_size, self.tile_size))

                if (x, y) in self.obstacles:
                    obstacle = self.obstacles[(x, y)]
                    if obstacle.sprite:
                        screen.blit(obstacle.sprite, (screen_x, screen_y))
