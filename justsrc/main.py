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
# --- System Imports ---
from systems import music
from systems.combat_system import CombatSystem
from systems.ai_behavior_system import BehaviorSystem
from systems.behavior_executor import BehaviorExecutor

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
        self.state_manager = GameStateManager()
        self.asset_manager = ProceduralAssetManager()
        
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
        self.reactor_menu: Optional[ReactorDebugMenu] = None

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
        
        logger.info("Game initialized.")

    def run(self):
        """Main game loop."""
        while self.is_running:
            dt = self.clock.tick(constants.FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.render()
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
                if action == "new_game":
                    logger.info("Starting new game...")
                    self.initialize_game()
                    logger.info(f"Game initialized with map size {self.game_map.width}x{self.game_map.height}")
                    self.state_manager.set_state(constants.STATE_PLAY)
                elif action == "quit":
                    self.is_running = False

            elif current_state == constants.STATE_PLAY:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_v, pygame.K_c):
                    self.open_component_viewer()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Shooting
                    mx, my = pygame.mouse.get_pos()
                    world_x = mx + self.camera_x
                    world_y = my + self.camera_y
                    # Adjust for camera offset (camera_x is negative of player pos usually, wait. 
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
                    elif event.key == pygame.K_ESCAPE: 
                        self.state_manager.set_state(constants.STATE_PLAY)
                    
                    if biome:
                        import random
                        new_seed = random.randint(0, 999999)
                        self.game_map.regenerate(seed=new_seed, biome_type=biome)
                        
                        # Respawn player on valid land
                        # For island, center is safest. For others, random is fine but check collision.
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
                        self.state_manager.set_state(constants.STATE_PLAY)

            elif current_state == constants.STATE_DEBUG_SPAWN:
                if event.type == pygame.KEYDOWN:
                    if self.debug_spawn_step == "type":
                        if event.key == pygame.K_1: 
                            self.debug_spawn_step = "rarity"
                        elif event.key == pygame.K_2: 
                            self.debug_spawn_step = "enemy_class"
                        elif event.key == pygame.K_ESCAPE:
                            self.state_manager.set_state(constants.STATE_PLAY)

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
                                
                            enemy = Enemy(f"{enemy_class} Lvl {level}", ex, ey, level=level, ai_class=enemy_class)
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
                            if slot == "weapon":
                                # Spawn a random arm with a weapon mount
                                slot = "right_arm" # Default to right arm for now
                                comp = create_random_component(self.debug_selected_rarity, slot)
                                # Ensure it has a weapon mount if not already
                                # create_random_component adds one for arms, so we are good.
                                comp.name = f"{self.debug_selected_rarity} Weapon"
                            else:
                                comp = create_random_component(self.debug_selected_rarity, slot)
                                
                            self.player.inventory.append(comp)
                            logger.info(f"Debug Spawned: {comp.name}")
                            self.state_manager.set_state(constants.STATE_PLAY)
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
                            self.hex_editor = ComponentHexEditor(current_comp, self.screen)
                            self.state_manager.set_state(constants.STATE_HEX_EDITOR)

            elif current_state == constants.STATE_HEX_EDITOR and self.hex_editor:
                action = self.hex_editor.handle_input(event)
                if action == "close":
                    self.hex_editor.save_changes()
                    self.player.recalculate_stats()
                    self.hex_editor = None
                    self.state_manager.set_state(constants.STATE_COMPONENT_VIEWER)

    def update(self, dt: float):
        """Update game logic."""
        current_state = self.state_manager.get_state()
        if current_state == constants.STATE_PLAY and self.player:
            self.update_player_movement(dt)
            self.update_player_movement(dt)
            self.player.update(dt)
            
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
                        bot.update(dt, self.player, self.combat_system, current_time)
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
        self.player.update_movement(move_x, move_y, dt)
        
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
                options = ["1. Spawn Item", "2. Spawn Enemy"]
            elif self.debug_spawn_step == "enemy_class":
                options = ["1. Grunt", "2. Sniper", "3. Ambusher", "4. Boss"]
            elif self.debug_spawn_step == "rarity":
                options = ["1. Common", "2. Uncommon", "3. Rare", "4. Epic", "5. Legendary"]
            elif self.debug_spawn_step == "slot":
                options = ["1. Head", "2. Torso", "3. L-Arm", "4. R-Arm", "5. L-Leg", "6. R-Leg", "7. Back", "8. Weapon"]
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
                "5. Island", "6. Volcanic Waste", "7. Desert", "ESC. Cancel"
            ]
            y = 150
            for opt in options:
                surf = font.render(opt, True, (255, 255, 255))
                self.screen.blit(surf, (self.screen.get_width()//2 - surf.get_width()//2, y))
                y += 40

        pygame.display.flip()

    def initialize_game(self):
        """Sets up the player and world for a new game."""
        self.game_map = GameMap(width=100, height=100, tile_size=constants.TILE_SIZE, asset_manager=self.asset_manager)
        start_x = self.game_map.width * constants.TILE_SIZE / 2
        start_y = self.game_map.height * constants.TILE_SIZE / 2
        self.player = Player(name="Player", x=start_x, y=start_y)
        self.player.asset_manager = self.asset_manager

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

