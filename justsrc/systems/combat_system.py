import pygame
import math
import constants
from entities.projectile import Projectile

class CombatSystem:
    def __init__(self, asset_manager, behavior_system=None):
        self.asset_manager = asset_manager
        self.projectiles = []
        self.behavior_system = behavior_system  # For AI learning

    def update(self, dt, game_map, all_bots):
        # Update projectiles
        for p in self.projectiles:
            p.update(dt)
        
        # Remove inactive projectiles
        self.projectiles = [p for p in self.projectiles if p.active]
        
        # Collision Detection
        for p in self.projectiles:
            if not p.active: continue
            
            # Wall Collision
            tile_x = int(p.x / constants.TILE_SIZE)
            tile_y = int(p.y / constants.TILE_SIZE)
            
            if not (0 <= tile_x < game_map.width and 0 <= tile_y < game_map.height):
                p.active = False
                continue
                
            if game_map.terrain[tile_y][tile_x] in constants.NON_WALKABLE_TERRAIN:
                p.active = False
                continue
                
            # Entity Collision
            for bot in all_bots:
                # Don't hit yourself
                if p.owner == "player" and bot.name == "Player": continue
                if p.owner == "enemy" and bot.name != "Player": continue
                
                dist = math.sqrt((p.x - bot.x)**2 + (p.y - bot.y)**2)
                if dist < constants.TILE_SIZE / 2: # Simple hit box
                    # Track health before damage for learning
                    health_before = bot.hp
                    
                    bot.take_damage(p.damage)
                    p.active = False
                    
                    # If player took damage, track it for AI learning
                    if bot.name == "Player" and self.behavior_system is not None:
                        from entities.enemy import Enemy
                        # Find which enemy shot this projectile
                        for enemy in all_bots:
                            if isinstance(enemy, Enemy) and p.owner == "enemy":
                                enemy_id = str(id(enemy))
                                self.behavior_system.track_player_damage(
                                    damage_amount=p.damage,
                                    player_health_before=health_before,
                                    player_health_after=bot.hp,
                                    enemy_id=enemy_id,
                                    enemy_class=enemy.ai_class
                                )
                                break
                    
                    break

    def render(self, screen, camera_x, camera_y):
        for p in self.projectiles:
            p.render(screen, camera_x, camera_y)

    def spawn_projectile(self, x, y, angle, speed, damage, damage_type, owner):
        p = Projectile(x, y, angle, speed, damage, damage_type, owner)
        self.projectiles.append(p)

    def deal_damage(self, target, amount, source=None):
        """Apply direct damage to a target (e.g. melee)."""
        health_before = target.hp
        target.take_damage(amount)
        
        # Track for AI learning if player is hit
        if target.name == "Player" and self.behavior_system is not None and source is not None:
            from entities.enemy import Enemy
            if isinstance(source, Enemy):
                enemy_id = str(id(source))
                self.behavior_system.track_player_damage(
                    damage_amount=amount,
                    player_health_before=health_before,
                    player_health_after=target.hp,
                    enemy_id=enemy_id,
                    enemy_class=source.ai_class
                )
