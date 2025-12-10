# G:\work\pixelbots\main.py
import pygame
import os
import sys
import logging

# --- Setup Logging ---
# It's best practice to configure logging as the very first thing.
import logging_setup
logging_setup.configure_logging()

# Now we can get our logger
logger = logging.getLogger(__name__)

# --- Core Imports ---
import constants
from core.game_state import GameStateManager
from core.asset_manager import ProceduralAssetManager

# --- System Imports ---
from systems import music
from systems.combat_system import CombatSystem
from systems.ai_behavior_system import BehaviorSystem
from systems.behavior_executor import BehaviorExecutor
from systems.saveload import SaveLoadSystem

# --- World Imports ---
from world.game_map import GameMap

# --- Entity Imports ---
from entities.player import Player
from entities.enemy import Enemy
from equipment.component import (
    ComponentEquipment, create_starter_torso, create_starter_arm, 
    create_starter_leg, create_starter_head, create_starter_back,
    create_random_component
)

# --- UI Imports ---
from ui.main_menu import MainMenu
from ui.component_viewer import ComponentViewer
from ui.hex_editor import ComponentHexEditor
from ui.crafting_menu import CraftingMenu
from ui.equipment_menu import EquipmentMenu
from ui.reactor_menu import ReactorDebugMenu
from ui.help_screen import HelpScreen

from typing import Optional

class Game:
    def __init__(self):
        # Initialize Mixer FIRST for proper audio buffering
        try:
            pygame.mixer.pre_init(44100, -16, 2, 2048)
            pygame.mixer.init()
            pygame.mixer.set_num_channels(32)
        except Exception as e:
            logger.error(f"Failed to pre-init mixer: {e}")

        pygame.init()
        music.init()

        # Screen and clock setup
        pygame.display.set_caption(constants.CAPTION)
        self.screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.is_running = True

        # Core Systems
        self.state_manager = GameStateManager()
        self.asset_manager = ProceduralAssetManager()
        self.save_load_system = SaveLoadSystem("saves", "data")
        self.current_profile = "default"
        
        # AI Behavior System (initialize first)
        self.behavior_system = BehaviorSystem()
        self.behavior_executor = BehaviorExecutor(self)
        
        # Combat system needs behavior system for damage tracking
        self.combat_system = CombatSystem(self.asset_manager, self.behavior_system)

        # UI Screens
        self.main_menu = MainMenu(self.screen, self.asset_manager)
        self.component_viewer = ComponentViewer(self.screen, self.asset_manager)
        self.hex_editor: Optional[ComponentHexEditor] = None
        self.crafting_menu: Optional[CraftingMenu] = None
        self.equipment_menu: Optional[EquipmentMenu] = None
        self.equipment_menu: Optional[EquipmentMenu] = None
        self.reactor_menu: Optional[ReactorDebugMenu] = None
        self.help_screen = HelpScreen(self.screen, self.asset_manager)

        # World and Camera
        self.game_map: Optional[GameMap] = None
        self.camera_x = 0
        self.camera_y = 0

        # Game Objects
        self.player: Optional[Player] = None
        self.all_bots = []
        
        # Debug State
        self.debug_spawn_step = "rarity" # rarity, slot
        self.debug_selected_rarity = "Common"
        
        self.music_check_timer = 0.0
        
        logger.info("Game initialized.")

    def run(self):
        """Main game loop."""
        logger.info("Entering main game loop.")
        frame_count = 0
        while self.is_running:
            dt = self.clock.tick(constants.FPS) / 1000.0
            if frame_count < 10:
                logger.info(f"Frame {frame_count} start")
            
            self.handle_events()
            if frame_count < 10: logger.info(f"Frame {frame_count} events handled")
            
            self.update(dt)
            if frame_count < 10: logger.info(f"Frame {frame_count} update done")
            
            self.render()
            if frame_count < 10: logger.info(f"Frame {frame_count} render done")
            
            frame_count += 1
        self.cleanup()

    def handle_events(self):
        """Process all inputs and events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
                return

            current_state = self.state_manager.get_state()

            if current_state == constants.STATE_MENU:
                action = self.main_menu.handle_input(event)
                if action == "select_slot_new":
                    from ui.save_slot_menu import SaveSlotMenu
                    self.save_slot_menu = SaveSlotMenu(self.screen, self.asset_manager, self.save_load_system, mode="new")
                    self.state_manager.set_state(constants.STATE_SAVE_SLOT)
                elif action == "select_slot_load":
                    from ui.save_slot_menu import SaveSlotMenu
                    self.save_slot_menu = SaveSlotMenu(self.screen, self.asset_manager, self.save_load_system, mode="load")
                    self.state_manager.set_state(constants.STATE_SAVE_SLOT)
                elif action == "quit":
                    self.is_running = False

            elif current_state == constants.STATE_SAVE_SLOT:
                if hasattr(self, 'save_slot_menu'):
                    slot = self.save_slot_menu.handle_input(event)
                    if slot == "back":
                        self.state_manager.set_state(constants.STATE_MENU)
                    elif slot:
                        # Slot selected
                        self.current_profile = slot
                        if self.save_slot_menu.mode == "new":
                            logger.info(f"Starting new game in {slot}...")
                            self.initialize_game()
                            self.state_manager.set_state(constants.STATE_PLAY)
                        else:
                            logger.info(f"Loading game from {slot}...")
                            result = self.save_load_system.load_game(self.current_profile, self.asset_manager)
                            if result:
                                loaded_player, map_seed = result
                                self.player = loaded_player
                                
                                # Re-init map with saved seed
                                if map_seed is None: map_seed = 12345
                                self.game_map = GameMap(width=100, height=100, tile_size=constants.TILE_SIZE, asset_manager=self.asset_manager, seed=map_seed)
                                
                                self.state_manager.set_state(constants.STATE_PLAY)
                                
                                # Safety Check
                                px_tile = int(self.player.x / constants.TILE_SIZE)
                                py_tile = int(self.player.y / constants.TILE_SIZE)
                                logger.info(f"Game loaded from {slot}.")
                            else:
                                logger.warning("No save found in slot.")
                                # Maybe stay in menu or show error?
                                self.state_manager.set_state(constants.STATE_MENU)

            elif current_state == constants.STATE_PAUSE:
                if not hasattr(self, 'pause_menu'):
                    from ui.pause_menu import PauseMenu
                    self.pause_menu = PauseMenu(self.screen, self.asset_manager)
                
                action = self.pause_menu.handle_input(event)
                if action == "resume":
                    self.state_manager.set_state(constants.STATE_PLAY)
                elif action == "main_menu":
                    self.state_manager.set_state(constants.STATE_MENU)
                elif action == "quit":
                    self.is_running = False
                elif action == "save_load_menu":
                    # For now, just save (quick save)
                    seed = self.game_map.seed if self.game_map else None
                    if self.save_load_system.save_game(self.current_profile, self.player, seed):
                        print("Game Saved!")
                    self.state_manager.set_state(constants.STATE_PLAY) # Resume after save? Or stay?
                    # Ideally show a message "Saved"
                # Handle other actions...

            elif current_state == constants.STATE_PLAY:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state_manager.set_state(constants.STATE_PAUSE)
                    return # Consume event

                if event.type == pygame.KEYDOWN and event.key in (pygame.K_v, pygame.K_c):
                    self.open_component_viewer()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Shooting
                    mx, my = pygame.mouse.get_pos()
                    # Camera logic: screen_x = world_x + camera_x. So world_x = screen_x - camera_x
                    world_x = mx - self.camera_x
                    world_y = my - self.camera_y
                    
                    current_time = pygame.time.get_ticks() / 1000.0
                    self.player.shoot(world_x, world_y, self.combat_system, current_time)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_b:
                    # Debug spawn enemy
                    import random
                    ex = self.player.x + random.randint(-300, 300)
                    ey = self.player.y + random.randint(-300, 300)
                    level = random.randint(1, 10)
                    enemy = Enemy(f"Enemy Lvl {level}", ex, ey, level=level)
                    enemy.asset_manager = self.asset_manager
                    self.all_bots.append(enemy)
                    logger.info(f"Spawned enemy {enemy.name} at {ex}, {ey}")
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_k:
                    # Open Crafting
                    self.crafting_menu = CraftingMenu(self.screen, self.asset_manager, self.player)
                    self.state_manager.set_state(constants.STATE_CRAFTING)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    # Open Equipment menu
                    self.equipment_menu = EquipmentMenu(self.screen, self.asset_manager, self.player)
                    self.state_manager.set_state(constants.STATE_EQUIPMENT)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    # Open Reactor Debug menu
                    logger.info("Opening Reactor Debug Menu")
                    self.reactor_menu = ReactorDebugMenu(self.screen, self.player)
                    self.state_manager.set_state(constants.STATE_REACTOR)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_i:
                    # Open Debug Spawn
                    self.state_manager.set_state(constants.STATE_DEBUG_SPAWN)
                    self.debug_spawn_step = "type" # Start at type selection
                    logger.info("Entered Debug Spawn Mode")
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_j:
                    # Open Debug Biome
                    self.state_manager.set_state(constants.STATE_DEBUG_BIOME)
                    logger.info("Entered Debug Biome Mode")
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F8:
                    # Debug: Equip Full Legendary Gear
                    logger.info("Debug: Equipping Full Legendary Gear")
                    from equipment.component import create_random_component
                    slots = ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "back"]
                    for slot in slots:
                        comp = create_random_component("Legendary", slot)
                        # Ensure weapon mount for arms
                        if "arm" in slot:
                            comp.name = f"Legendary {slot.replace('_', ' ').title()}"
                        self.player.equip_component(comp)
                    self.player.recalculate_stats()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F9:
                    # Load Game
                    result = self.save_load_system.load_game(self.current_profile, self.asset_manager)
                    if result:
                        loaded_player, map_seed = result
                        self.player = loaded_player
                        # Re-link player to game map if needed (not strictly needed as player has x,y)
                        # But we need to ensure all_bots has the new player
                        self.all_bots[0] = self.player
                        
                        # Link player to UI
                        self.component_viewer.player = self.player
                        
                        print("Game Loaded!")
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F5:
                    # Save Game
                    if self.save_load_system.save_game(self.current_profile, self.player):
                        print("Game Saved!")
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F10:
                    # Debug: Toggle Boss Invulnerability
                    constants.BOSS_INVULNERABLE = not getattr(constants, "BOSS_INVULNERABLE", False)
                    logger.info(f"Debug: Boss Invulnerability set to {constants.BOSS_INVULNERABLE}")
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F7:
                    # Debug: Equip Multi-Vector Test Weapon
                    logger.info("Debug: Equipping Multi-Vector Test Weapon (F7)")
                    from equipment.component import ComponentEquipment
                    from hex_system.hex_coord import HexCoord
                    from hex_system.hex_tile import WeaponMountTile, TileCategory, HexTile, BasicConduitTile
                    
                    # Create a 5x5 Legendary Right Arm
                    comp = ComponentEquipment(name="Multi-Vector Test Arm", slot="right_arm", quality="Legendary", base_armor=10)
                    comp.grid_width = 5
                    comp.grid_height = 5
                    comp.valid_coords = set()
                    for q in range(5):
                        for r in range(5):
                            comp.valid_coords.add(HexCoord(q,r))
                    
                    comp.max_tile_capacity = 25
                    
                    # Place Weapon Mount in Center (2,2)
                    mount = WeaponMountTile(tile_type="Weapon Mount", category=TileCategory.OUTPUT, weapon_type="beam")
                    comp.place_tile(HexCoord(2,2), mount)
                    
                    # Add a default Splitter at entry (0,2) to get them started
                    from hex_system.hex_tile import SplitterTile
                    splitter = SplitterTile(split_count=2)
                    splitter.set_exit_direction(0, 0) # East -> (1,2)
                    splitter.set_exit_direction(1, 1) # NE -> (1,1)
                    comp.place_tile(HexCoord(0,2), splitter)
                    
                    self.player.equip_component(comp)
                    self.player.recalculate_stats()
                    logger.info("Equipped Multi-Vector Test Arm (5x5).")

                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F6:
                    # Debug: Spawn Cohort
                    logger.info("Debug: Spawning Enemy Cohort (F6)")
                    import random
                    # from entities.enemy import Enemy
                    
                    # Spawn 5-8 enemies around the player
                    count = random.randint(5, 8)
                    for _ in range(count):
                        # Random position near player
                        offset_x = random.randint(-400, 400)
                        offset_y = random.randint(-400, 400)
                        # Ensure not too close
                        if abs(offset_x) < 100: offset_x += 100 if offset_x > 0 else -100
                        if abs(offset_y) < 100: offset_y += 100 if offset_y > 0 else -100
                        
                        x = self.player.x + offset_x
                        y = self.player.y + offset_y
                        
                        # Random level based on player level
                        lvl = max(1, self.player.level + random.randint(-1, 2))
                        
                        biome = "forest"
                        if self.game_map and hasattr(self.game_map, "biome_manager"):
                            biome = self.game_map.biome_manager.current_biome
                            
                        enemy = Enemy("Enemy", x, y, level=lvl, biome=biome)
                        enemy.asset_manager = self.asset_manager
                        self.all_bots.append(enemy)
                        
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F7:
                    # Debug: Equip Multi-Vector Test Weapon
                    logger.info("Debug: Equipping Multi-Vector Test Weapon (F7)")
                    from equipment.component import ComponentEquipment
                    from hex_system.hex_coord import HexCoord
                    from hex_system.hex_tile import WeaponMountTile, TileCategory, HexTile, BasicConduitTile
                    
                    # Create a 5x5 Legendary Right Arm
                    comp = ComponentEquipment(name="Multi-Vector Test Arm", slot="right_arm", quality="Legendary", base_armor=10)
                    comp.grid_width = 5
                    comp.grid_height = 5
                    comp.valid_coords = set()
                    for q in range(5):
                        for r in range(5):
                            comp.valid_coords.add(HexCoord(q,r))
                    
                    comp.max_tile_capacity = 25
                    
                    # Place Weapon Mount in Center (2,2)
                    mount = WeaponMountTile(tile_type="Weapon Mount", category=TileCategory.OUTPUT, weapon_type="beam")
                    comp.place_tile(HexCoord(2,2), mount)
                    
                    # Add a default Splitter at entry (0,2) to get them started
                    from hex_system.hex_tile import SplitterTile
                    splitter = SplitterTile(split_count=2)
                    splitter.set_exit_direction(0, 0) # East -> (1,2)
                    splitter.set_exit_direction(1, 1) # NE -> (1,1)
                    comp.place_tile(HexCoord(0,2), splitter)
                    
                    self.player.equip_component(comp)
                    self.player.recalculate_stats()
                    logger.info("Equipped Multi-Vector Test Arm (5x5).")

                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                    # Open Help Screen
                    self.state_manager.set_state(constants.STATE_HELP)
                    
            elif current_state == constants.STATE_HELP:
                action = self.help_screen.handle_input(event)
                if action == "close":
                    self.state_manager.set_state(constants.STATE_PLAY)

            elif current_state == constants.STATE_DEBUG_BIOME:
                if event.type == pygame.KEYDOWN:
                    biome = None
                    if event.key == pygame.K_1: biome = "tundra" # Snow
                    elif event.key == pygame.K_2: biome = "mountainous"
                    elif event.key == pygame.K_3: biome = "beach"
                    elif event.key == pygame.K_4: biome = "grassland" # Plains
                    elif event.key == pygame.K_5: biome = "island"
                    elif event.key == pygame.K_6: biome = "volcano" # Volcanic Waste
                    elif event.key == pygame.K_7: biome = "desert"
                    elif event.key == pygame.K_8: biome = "meadow"
                    elif event.key == pygame.K_ESCAPE: 
                        self.state_manager.set_state(constants.STATE_PLAY)
                    
                    if biome:
                        import random
                        new_seed = random.randint(0, 999999)
                        self.game_map.regenerate(seed=new_seed, biome_type=biome)
                        
                        # Respawn player on valid land
                        cx, cy = self.game_map.width // 2, self.game_map.height // 2
                        found_spot = False
                        
                        # Spiral search from center
                        for r in range(0, max(self.game_map.width, self.game_map.height)):
                            for dx in range(-r, r + 1):
                                for dy in range(-r, r + 1):
                                    tx, ty = cx + dx, cy + dy
                                    if 0 <= tx < self.game_map.width and 0 <= ty < self.game_map.height:
                                        if self.game_map.terrain[ty][tx] != constants.WATER and (tx, ty) not in self.game_map.obstacles:
                                            self.player.x = tx * constants.TILE_SIZE + constants.TILE_SIZE / 2
                                            self.player.y = ty * constants.TILE_SIZE + constants.TILE_SIZE / 2
                                            found_spot = True
                                            break
                                if found_spot: break
                            if found_spot: break
                        
                        logger.info(f"Regenerated map with biome: {biome}")
                        music.play_music(biome)
                        self.state_manager.set_state(constants.STATE_PLAY)

            elif current_state == constants.STATE_DEBUG_SPAWN:
                if event.type == pygame.KEYDOWN:
                    if self.debug_spawn_step == "type":
                        if event.key == pygame.K_1: 
                            self.debug_spawn_step = "rarity"
                        elif event.key == pygame.K_2: 
                            self.debug_spawn_step = "enemy_class"
                        elif event.key == pygame.K_3:
                            self.debug_spawn_step = "core_rate"
                            self.debug_core_config = {"rate": 100.0, "synergy": "fire", "direction": "omni"}
                        elif event.key == pygame.K_ESCAPE:
                            self.state_manager.set_state(constants.STATE_PLAY)

                    elif self.debug_spawn_step == "core_rate":
                        rate = None
                        if event.key == pygame.K_1: rate = 10.0
                        elif event.key == pygame.K_2: rate = 50.0
                        elif event.key == pygame.K_3: rate = 100.0
                        elif event.key == pygame.K_4: rate = 500.0
                        elif event.key == pygame.K_5: rate = 1000.0
                        elif event.key == pygame.K_ESCAPE:
                            self.state_manager.set_state(constants.STATE_PLAY)
                        
                        if rate:
                            self.debug_core_config["rate"] = rate
                            self.debug_spawn_step = "core_synergy"

                    elif self.debug_spawn_step == "core_synergy":
                        syn = None
                        if event.key == pygame.K_1: syn = "fire"
                        elif event.key == pygame.K_2: syn = "ice"
                        elif event.key == pygame.K_3: syn = "lightning"
                        elif event.key == pygame.K_4: syn = "raw"
                        elif event.key == pygame.K_5: syn = "vortex"
                        elif event.key == pygame.K_6: syn = "explosion"
                        elif event.key == pygame.K_ESCAPE:
                            self.state_manager.set_state(constants.STATE_PLAY)
                            
                        if syn:
                            self.debug_core_config["synergy"] = syn
                            self.debug_spawn_step = "core_direction"

                    elif self.debug_spawn_step == "core_direction":
                        direction = None
                        if event.key == pygame.K_1: direction = "omni"
                        elif event.key == pygame.K_2: direction = 0 # Top
                        elif event.key == pygame.K_3: direction = 1 # Top-Right
                        elif event.key == pygame.K_4: direction = 2 # Bottom-Right
                        elif event.key == pygame.K_5: direction = 3 # Bottom
                        elif event.key == pygame.K_6: direction = 4 # Bottom-Left
                        elif event.key == pygame.K_7: direction = 5 # Top-Left
                        elif event.key == pygame.K_ESCAPE:
                            self.state_manager.set_state(constants.STATE_PLAY)
                            
                        if direction is not None:
                            self.debug_core_config["direction"] = direction
                            
                            # Spawn the core!
                            from hex_system.energy_packet import SynergyType, EnergyCore
                            from hex_system.hex_coord import HexCoord
                            
                            # Map string to enum
                            syn_map = {
                                "fire": SynergyType.FIRE, "ice": SynergyType.ICE, 
                                "lightning": SynergyType.LIGHTNING, "raw": SynergyType.RAW,
                                "vortex": SynergyType.VORTEX, "explosion": SynergyType.EXPLOSION
                            }
                            core_type = syn_map.get(self.debug_core_config["synergy"], SynergyType.RAW)
                            
                            # Create Torso
                            torso = create_starter_torso()
                            torso.name = f"Debug Core ({self.debug_core_config['synergy']})"
                            torso.core = EnergyCore(
                                core_type=core_type, 
                                generation_rate=self.debug_core_config["rate"],
                                position=HexCoord(1, 1)
                            )
                            
                            # Configure direction
                            d = self.debug_core_config["direction"]
                            if d == "omni":
                                torso.core.configure_omnidirectional()
                            else:
                                torso.core.configure_focused(d)
                                
                            self.player.inventory.append(torso)
                            logger.info(f"Debug Spawned Core: {torso.name}, Rate: {torso.core.generation_rate}, Dir: {d}")
                            
                            self.state_manager.set_state(constants.STATE_PLAY)
                            self.debug_spawn_step = "type"

                    elif self.debug_spawn_step == "enemy_class":
                        enemy_class = None
                        if event.key == pygame.K_1: enemy_class = "Grunt"
                        elif event.key == pygame.K_2: enemy_class = "Sniper"
                        elif event.key == pygame.K_3: enemy_class = "Ambusher"
                        elif event.key == pygame.K_4: enemy_class = "Boss"
                        elif event.key == pygame.K_ESCAPE:
                            self.state_manager.set_state(constants.STATE_PLAY)
                        
                        if enemy_class:
                            import random
                            ex = self.player.x + random.randint(-300, 300)
                            ey = self.player.y + random.randint(-300, 300)
                            level = random.randint(1, 10)
                            if enemy_class == "Boss":
                                level = 20 # Bosses are high level
                            
                            biome = "forest"
                            if self.game_map and hasattr(self.game_map, "biome_manager"):
                                biome = self.game_map.biome_manager.current_biome

                            enemy = Enemy(f"{enemy_class} Lvl {level}", ex, ey, level=level, ai_class=enemy_class, biome=biome)
                            enemy.asset_manager = self.asset_manager
                            self.all_bots.append(enemy)
                            logger.info(f"Spawned enemy {enemy.name} ({enemy_class}) at {ex}, {ey}")
                            self.state_manager.set_state(constants.STATE_PLAY)

                    elif self.debug_spawn_step == "rarity":
                        rarity = None
                        if event.key == pygame.K_1: rarity = "Common"
                        elif event.key == pygame.K_2: rarity = "Uncommon"
                        elif event.key == pygame.K_3: rarity = "Rare"
                        elif event.key == pygame.K_4: rarity = "Epic"
                        elif event.key == pygame.K_5: rarity = "Legendary"
                        elif event.key == pygame.K_ESCAPE: 
                            self.state_manager.set_state(constants.STATE_PLAY)
                        
                        if rarity:
                            self.debug_selected_rarity = rarity
                            self.debug_spawn_step = "slot"
                            
                    elif self.debug_spawn_step == "slot":
                        slot = None
                        if event.key == pygame.K_1: slot = "head"
                        elif event.key == pygame.K_2: slot = "torso"
                        elif event.key == pygame.K_3: slot = "left_arm"
                        elif event.key == pygame.K_4: slot = "right_arm"
                        elif event.key == pygame.K_5: slot = "left_leg"
                        elif event.key == pygame.K_6: slot = "right_leg"
                        elif event.key == pygame.K_7: slot = "back"
                        elif event.key == pygame.K_8: slot = "weapon" # Special case
                        elif event.key == pygame.K_ESCAPE:
                            self.state_manager.set_state(constants.STATE_PLAY)
                            
                        if slot:
                            from equipment.component import create_random_component
                            if slot == "weapon":
                                # Spawn a random arm with a weapon mount
                                slot = "right_arm" # Default to right arm for now
                                comp = create_random_component(self.debug_selected_rarity, slot)
                                # Ensure it has a weapon mount if not already
                                comp.name = f"{self.debug_selected_rarity} Weapon"
                            else:
                                comp = create_random_component(self.debug_selected_rarity, slot)
                                
                            self.player.inventory.append(comp)
                            logger.info(f"Debug Spawned: {comp.name}")
                            self.state_manager.set_state(constants.STATE_PLAY)
                            self.debug_spawn_step = "rarity" # Reset

            elif current_state == constants.STATE_CRAFTING and self.crafting_menu:
                action = self.crafting_menu.handle_input(event)
                if action == "close":
                    self.crafting_menu = None
                    self.state_manager.set_state(constants.STATE_PLAY)

            elif current_state == constants.STATE_EQUIPMENT and self.equipment_menu:
                action = self.equipment_menu.handle_input(event)
                if action == "close":
                    self.equipment_menu = None
                    self.state_manager.set_state(constants.STATE_PLAY)

            elif current_state == constants.STATE_REACTOR and self.reactor_menu:
                action = self.reactor_menu.handle_input(event)
                if action == "close":
                    self.reactor_menu = None
                    self.state_manager.set_state(constants.STATE_PLAY)

            elif current_state == constants.STATE_COMPONENT_VIEWER:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.state_manager.set_state(constants.STATE_PLAY)
                    elif event.key == pygame.K_LEFT:
                        self.component_viewer.cycle_component(-1)
                    elif event.key == pygame.K_RIGHT:
                        self.component_viewer.cycle_component(1)
                    elif event.key == pygame.K_e:
                        current_comp = self.component_viewer.get_current_component()
                        if current_comp:
                            # NEW: Try to get real input context from Torso if available
                            input_context = None
                            if current_comp.slot != "torso" and self.player:
                                torso = self.player.components.get("torso")
                                if torso:
                                    _, _, torso_exits = torso.simulate_flow()
                                    # Determine which exit feeds this component
                                    slot = current_comp.slot
                                    dir_idx = -1
                                    
                                    if slot == "right_arm": dir_idx = 0
                                    elif slot == "left_arm": dir_idx = 3
                                    elif slot == "head": dir_idx = 1 # NE (Yellow Diamond)
                                    elif slot == "back": dir_idx = 2 # NW (Purple Square)
                                    
                                    elif "leg" in slot:
                                        if "right" in slot: dir_idx = 5
                                        else: dir_idx = 4
                                    
                                    if dir_idx != -1:
                                        input_context = torso_exits.get(dir_idx)
                                    
                                    # FALLBACK: Use Wireless Power if context is missing but Core exists
                                    if not input_context and torso.core:
                                        from hex_system.energy_packet import ProjectileContext
                                        base_mag = torso.core.generation_rate * 0.5
                                        input_context = ProjectileContext(synergies={torso.core.core_type: base_mag})
                                        logger.info(f"  -> Using Wireless Fallback for {slot} (50% efficiency)")

                                    # Debug Log
                                    logger.info(f"Opening Editor for {current_comp.slot}. Torso Exits: {list(torso_exits.keys())}")
                                    if input_context:
                                        logger.info(f"  -> Found Context: {input_context.synergies}")
                                    else:
                                        logger.info(f"  -> NO Context found for direction {dir_idx}")
                            
                            self.hex_editor = ComponentHexEditor(current_comp, self.screen, input_context=input_context)
                            self.state_manager.set_state(constants.STATE_HEX_EDITOR)

            elif current_state == constants.STATE_HEX_EDITOR and self.hex_editor:
                action = self.hex_editor.handle_input(event)
                if action == "close":
                    self.hex_editor.save_changes()
                    if self.player:
                        self.player.recalculate_stats()
                    self.hex_editor = None
                    self.state_manager.set_state(constants.STATE_COMPONENT_VIEWER)

    def update(self, dt: float):
        """Update game logic."""
        current_state = self.state_manager.get_state()
        if current_state == constants.STATE_PLAY and self.player:
            self.update_player_movement(dt)
            self.player.update(dt)
            
            # Auto-Fire for Orbital Mode (Z-Key)
            if getattr(self.player, "orbital_mode", False):
                mx, my = pygame.mouse.get_pos()
                world_x = mx - self.camera_x
                world_y = my - self.camera_y
                current_time = pygame.time.get_ticks() / 1000.0
                self.player.shoot(world_x, world_y, self.combat_system, current_time)
            
            # Update Music based on Biome
            self.music_check_timer += dt
            if self.music_check_timer > 0.5:
                self.music_check_timer = 0
                px = int(self.player.x / constants.TILE_SIZE)
                py = int(self.player.y / constants.TILE_SIZE)
                if self.game_map and 0 <= px < self.game_map.width and 0 <= py < self.game_map.height:
                    biome = self.game_map.biome_manager.get_biome_type(px, py)
                    music.play_music(biome)
            
            current_time = pygame.time.get_ticks() / 1000.0
            
            # Update all bots (including enemies)
            for bot in self.all_bots:
                if bot != self.player:
                    if isinstance(bot, Enemy):
                        # Use AI behavior system
                        enemy_id = str(id(bot))
                        
                        # Select behavior based on learned weights
                        behavior = self.behavior_system.get_weighted_behavior(bot.ai_class)
                        
                        if behavior:
                            # Execute the behavior
                            success = self.behavior_executor.execute_behavior(
                                bot, behavior, self.player, current_time
                            )
                            
                            # Record behavior in memory
                            if success:
                                self.behavior_system.record_behavior(
                                    enemy_id, bot.ai_class, behavior.id
                                )
                        
                        # Still call normal update for fallback logic
                        bot.update(dt, self.player, self.combat_system, current_time, self.game_map)
                    else:
                        bot.update(dt)
            
            # Update Combat
            self.combat_system.update(dt, self.game_map, self.all_bots)
            
            # Remove dead bots
            self.all_bots = [b for b in self.all_bots if b.hp > 0]
            if self.player.hp <= 0:
                logger.info("Player died!")
                # Respawn logic or game over could go here
                self.initialize_game() 
            
            self.update_camera()
        elif current_state == constants.STATE_HEX_EDITOR and self.hex_editor:
            self.hex_editor.update()

    def update_player_movement(self, dt: float):
        keys = pygame.key.get_pressed()
        move_x = (keys[pygame.K_d] - keys[pygame.K_a])
        move_y = (keys[pygame.K_s] - keys[pygame.K_w])
        
        old_x, old_y = self.player.x, self.player.y
        self.player.update_movement(move_x, move_y, dt, self.game_map)
        
        # Collision Detection
        px_tile = int(self.player.x / constants.TILE_SIZE)
        py_tile = int(self.player.y / constants.TILE_SIZE)
        if not (0 <= px_tile < self.game_map.width and 0 <= py_tile < self.game_map.height):
            self.player.x, self.player.y = old_x, old_y
        else:
            tile_type = self.game_map.terrain[py_tile][px_tile]
            if (px_tile, py_tile) in self.game_map.obstacles or tile_type in constants.NON_WALKABLE_TERRAIN:
                self.player.x, self.player.y = old_x, old_y

    def update_camera(self):
        self.camera_x = -self.player.x + self.screen.get_width() / 2
        self.camera_y = -self.player.y + self.screen.get_height() / 2

    def render(self):
        """Draw everything to the screen."""
        current_state = self.state_manager.get_state()
        self.screen.fill((20, 20, 30))

        if current_state == constants.STATE_PLAY and self.player:
            if self.game_map: self.game_map.render(self.screen, self.camera_x, self.camera_y)
            if self.game_map: self.game_map.render(self.screen, self.camera_x, self.camera_y)
            for bot in self.all_bots: bot.render(self.screen, self.camera_x, self.camera_y)
            self.combat_system.render(self.screen, self.camera_x, self.camera_y)
            self.draw_play_ui()
        elif current_state == constants.STATE_MENU:
            self.main_menu.draw()
        elif current_state == constants.STATE_SAVE_SLOT:
            if hasattr(self, 'save_slot_menu'):
                self.save_slot_menu.draw()
        elif current_state == constants.STATE_PAUSE:
            # Draw game behind it (optional, but looks nice)
            if self.player and self.game_map:
                self.game_map.render(self.screen, self.camera_x, self.camera_y)
                for bot in self.all_bots: bot.render(self.screen, self.camera_x, self.camera_y)
                self.combat_system.render(self.screen, self.camera_x, self.camera_y)
                self.draw_play_ui()
            
            if hasattr(self, 'pause_menu'):
                self.pause_menu.draw()
        elif current_state == constants.STATE_COMPONENT_VIEWER:
            self.component_viewer.draw(self.screen)
        elif current_state == constants.STATE_HEX_EDITOR and self.hex_editor:
            self.hex_editor.draw()
        elif current_state == constants.STATE_CRAFTING and self.crafting_menu:
            self.crafting_menu.draw()
        elif current_state == constants.STATE_EQUIPMENT and self.equipment_menu:
            self.equipment_menu.draw()
        elif current_state == constants.STATE_REACTOR and self.reactor_menu:
            self.reactor_menu.draw()
        elif current_state == constants.STATE_HELP:
            self.help_screen.draw()
        elif current_state == constants.STATE_DEBUG_SPAWN:
            # Draw transparent overlay
            s = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
            s.set_alpha(128)
            s.fill((0,0,0))
            self.screen.blit(s, (0,0))
            
            font = pygame.font.Font(None, 36)
            text = font.render("DEBUG SPAWN MODE", True, (255, 50, 50))
            self.screen.blit(text, (self.screen.get_width()//2 - text.get_width()//2, 100))
            
            if self.debug_spawn_step == "type":
                options = ["1. Spawn Item", "2. Spawn Enemy", "3. Spawn Core"]
            elif self.debug_spawn_step == "enemy_class":
                options = ["1. Grunt", "2. Sniper", "3. Ambusher", "4. Boss"]
            elif self.debug_spawn_step == "rarity":
                options = ["1. Common", "2. Uncommon", "3. Rare", "4. Epic", "5. Legendary"]
            elif self.debug_spawn_step == "slot":
                options = ["1. Head", "2. Torso", "3. L-Arm", "4. R-Arm", "5. L-Leg", "6. R-Leg", "7. Back", "8. Weapon"]
            elif self.debug_spawn_step == "core_rate":
                options = ["1. 10/s", "2. 50/s", "3. 100/s", "4. 500/s", "5. 1000/s"]
            elif self.debug_spawn_step == "core_synergy":
                options = ["1. Fire", "2. Ice", "3. Lightning", "4. Raw", "5. Vortex"]
            elif self.debug_spawn_step == "core_direction":
                options = ["1. Omni", "2. Top (0)", "3. Top-Right (1)", "4. Bot-Right (2)", "5. Bot (3)", "6. Bot-Left (4)", "7. Top-Left (5)"]
            else:
                options = []
                
            for i, opt in enumerate(options):
                opt_surf = font.render(opt, True, (255, 255, 255))
                self.screen.blit(opt_surf, (self.screen.get_width()//2 - opt_surf.get_width()//2, 150 + i * 40))
            


                

        elif current_state == constants.STATE_DEBUG_BIOME:
            # Draw transparent overlay
            s = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
            s.set_alpha(128)
            s.fill((0,0,0))
            self.screen.blit(s, (0,0))
            
            font = pygame.font.Font(None, 36)
            text = font.render("DEBUG BIOME SWITCHER", True, (50, 255, 50))
            self.screen.blit(text, (self.screen.get_width()//2 - text.get_width()//2, 100))
            
            options = [
                "1. Snow (Tundra)", "2. Mountainous", "3. Beach", "4. Plains (Grass)", 
                "5. Island", "6. Volcanic Waste", "7. Desert", "8. Meadow", "ESC. Cancel"
            ]
            y = 150
            for opt in options:
                surf = font.render(opt, True, (255, 255, 255))
                self.screen.blit(surf, (self.screen.get_width()//2 - surf.get_width()//2, y))
                y += 40

        pygame.display.flip()

    def initialize_game(self):
        """Sets up the player and world for a new game."""
        self.game_map = GameMap(width=100, height=100, tile_size=constants.TILE_SIZE, asset_manager=self.asset_manager, biome_type=None)
        
        # Find a safe spawn point near the center
        cx, cy = self.game_map.width // 2, self.game_map.height // 2
        spawn_x, spawn_y = cx * constants.TILE_SIZE, cy * constants.TILE_SIZE
        
        # Spiral search for valid land
        found_spot = False
        for r in range(0, 20): # Search radius 20 tiles
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    tx, ty = cx + dx, cy + dy
                    if 0 <= tx < self.game_map.width and 0 <= ty < self.game_map.height:
                        if self.game_map.terrain[ty][tx] != constants.WATER and (tx, ty) not in self.game_map.obstacles:
                            spawn_x = tx * constants.TILE_SIZE + constants.TILE_SIZE / 2
                            spawn_y = ty * constants.TILE_SIZE + constants.TILE_SIZE / 2
                            found_spot = True
                            break
                if found_spot: break
            if found_spot: break
            
        self.player = Player(name="Player", x=spawn_x, y=spawn_y)
        self.player.asset_manager = self.asset_manager
        
        # Link player to UI
        self.component_viewer.player = self.player

        # Starter Equipment
        self.player.equip_component(create_starter_torso())
        self.player.equip_component(create_starter_head())
        self.player.equip_component(create_starter_leg("left_leg"))
        self.player.equip_component(create_starter_leg("right_leg"))
        self.player.equip_component(create_starter_arm("left_arm"))
        self.player.equip_component(create_starter_arm("right_arm"))
        
        # Add some inventory items for testing crafting
        self.player.inventory.append(create_starter_arm("left_arm"))
        self.player.inventory.append(create_starter_arm("left_arm"))
        self.player.inventory.append(create_starter_head())
        self.player.inventory.append(create_starter_head())
        logger.info("Started new game.")

        self.all_bots = [self.player]
        music.play_music(biome_name=self.game_map.biome_manager.current_biome)

    def open_component_viewer(self):
        if self.player:
            components = [c for c in self.player.components.values() if c]
            self.component_viewer.set_components(components)
            self.state_manager.set_state(constants.STATE_COMPONENT_VIEWER)

    def draw_play_ui(self):
        if not self.player: return
        font = self.asset_manager.get_font(None, 20)
        stats_text = f"HP: {int(self.player.hp)}/{int(self.player.max_hp)} | Armor: {self.player.total_armor}"
        text_surf = font.render(stats_text, True, (255, 255, 255))
        self.screen.blit(text_surf, (10, 10))

    def cleanup(self):
        logger.info("Shutting down game.")
        if self.player and self.game_map:
            self.save_load_system.save_game(self.current_profile, self.player, self.game_map.seed)
        music.shutdown()
        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    try:
        game = Game()
        game.run()
    except Exception as e:
        logger.critical("An unrecoverable error occurred.", exc_info=True)
        pygame.quit()
        sys.exit()
