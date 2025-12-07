import pygame
import math
import constants
import random
import logging
from entities.projectile import Projectile
from entities.vortex import Vortex

logger = logging.getLogger(__name__)

class VisualEffect:
    def __init__(self, effect_type, x, y, **kwargs):
        self.type = effect_type
        self.x = x
        self.y = y
        self.lifetime = kwargs.get("duration", 0.5)
        self.max_lifetime = self.lifetime
        self.data = kwargs
        
    def update(self, dt):
        self.lifetime -= dt
        
    def render(self, screen, camera_x, camera_y):
        if self.lifetime <= 0: return
        
        alpha = int((self.lifetime / self.max_lifetime) * 255)
        
        if self.type == "lightning_bolt":
            start = (self.x + camera_x, self.y + camera_y)
            end_x, end_y = self.data.get("end_pos", (self.x, self.y))
            end = (end_x + camera_x, end_y + camera_y)
            
            # Draw jagged line
            color = (200, 200, 255)
            points = [start]
            steps = 5
            dx = (end[0] - start[0]) / steps
            dy = (end[1] - start[1]) / steps
            
            for i in range(1, steps):
                # Jitter perpendicular to direction
                perp_x = -dy
                perp_y = dx
                # Normalize
                plen = math.sqrt(perp_x**2 + perp_y**2)
                if plen > 0:
                    perp_x /= plen
                    perp_y /= plen
                
                jitter = random.randint(-10, 10)
                px = start[0] + dx * i + perp_x * jitter
                py = start[1] + dy * i + perp_y * jitter
                points.append((px, py))
            points.append(end)
            
            if len(points) > 1:
                pygame.draw.lines(screen, color, False, points, 2)
                
        elif self.type == "implosion":
            # Draw shrinking circle
            radius = self.data.get("radius", 50) * (self.lifetime / self.max_lifetime)
            color = (150, 50, 200)
            cx = self.x + camera_x
            cy = self.y + camera_y
            if radius > 1:
                pygame.draw.circle(screen, color, (int(cx), int(cy)), int(radius), 2)

class ZoneEffect(VisualEffect):
    def __init__(self, effect_type, x, y, radius, duration, **kwargs):
        super().__init__(effect_type, x, y, duration=duration, **kwargs)
        self.radius = radius
        self.active = True
        self.element = kwargs.get("element", "neutral") # water, fire, etc.
        
    def update(self, dt, all_bots, projectiles, combat_system):
        super().update(dt)
        if self.lifetime <= 0: 
            self.active = False
            return

        # 1. Apply Effects to Bots
        for bot in all_bots:
            dist_sq = (bot.x - self.x)**2 + (bot.y - self.y)**2
            if dist_sq < self.radius**2:
                self._apply_zone_logic(bot, dt)
                
        # 2. Check Projectile Interactions
        for p in projectiles:
            if not p.active: continue
            dist_sq = (p.x - self.x)**2 + (p.y - self.y)**2
            if dist_sq < self.radius**2:
                self._handle_projectile_interaction(p, combat_system)

    def _apply_zone_logic(self, bot, dt):
        if self.element == "water":
            bot.apply_status_effect("wet", 0.1, 0) # Just mark them wet
        elif self.element == "electrified_water":
            bot.take_damage(20 * dt) # DoT
            bot.apply_status_effect("shock", 0.5, 0)
        elif self.element == "fire":
            bot.apply_status_effect("burn", 1.0, 5)
        elif self.element == "steam":
            # Slow down
            pass 

    def _handle_projectile_interaction(self, p, combat_system):
        # Elemental Reactions
        synergy = p.effects.get("synergy_name") if p.effects else None
        
        if self.element == "water":
            if synergy == "lightning":
                # Transform to Electrified Water
                self.element = "electrified_water"
                self.lifetime = 5.0 # Refresh duration
                combat_system.visual_effects.append(VisualEffect("lightning_bolt", self.x, self.y, end_pos=(self.x+random.randint(-20,20), self.y+random.randint(-20,20)), duration=0.5))
                p.active = False # Consume projectile? Maybe
            elif synergy == "fire":
                # Create Steam
                self.element = "steam"
                self.lifetime = 3.0
                p.active = False
            elif synergy == "ice":
                # Freeze
                self.element = "ice"
                self.lifetime = 5.0
                p.active = False

    def render(self, screen, camera_x, camera_y):
        if self.lifetime <= 0: return
        
        cx = self.x + camera_x
        cy = self.y + camera_y
        
        color = (100, 100, 100)
        if self.element == "water": color = (0, 100, 255, 100)
        elif self.element == "electrified_water": color = (200, 200, 255, 150)
        elif self.element == "fire": color = (255, 100, 0, 100)
        elif self.element == "steam": color = (200, 200, 200, 100)
        elif self.element == "ice": color = (150, 255, 255, 150)
        
        # Draw transparent circle
        s = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        pygame.draw.circle(s, color, (self.radius, self.radius), self.radius)
        screen.blit(s, (cx-self.radius, cy-self.radius))
        
        # Draw border
        pygame.draw.circle(screen, (color[0], color[1], color[2]), (int(cx), int(cy)), int(self.radius), 2)

class CombatSystem:
    def __init__(self, asset_manager, behavior_system=None):
        self.asset_manager = asset_manager
        self.projectiles = []
        self.vortices = [] # Legacy Vortex entities
        self.visual_effects = [] # New Visual Effects
        self.zone_effects = [] # New Zone Effects
        self.behavior_system = behavior_system  # For AI learning

    def update(self, dt, game_map, all_bots):
        # Update Visual Effects
        for effect in self.visual_effects:
            effect.update(dt)
        self.visual_effects = [e for e in self.visual_effects if e.lifetime > 0]

        # Update Zone Effects
        for zone in self.zone_effects:
            zone.update(dt, all_bots, self.projectiles, self)
        self.zone_effects = [z for z in self.zone_effects if z.active]

        # Update Legacy Vortices
        for v in self.vortices:
            v.update(dt)
        self.vortices = [v for v in self.vortices if v.active]

        # Legacy Vortex Physics (if any exist)
        for v in self.vortices:
            for bot in all_bots:
                if bot.name == "Player" and v.owner == "player": continue
                dx = v.x - bot.x
                dy = v.y - bot.y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < v.radius and dist > 10:
                    force = v.strength / (dist * 0.1)
                    angle = math.atan2(dy, dx)
                    bot.x += math.cos(angle) * force * dt
                    bot.y += math.sin(angle) * force * dt

        # Update Projectiles
        for p in self.projectiles:
            p.update(dt)
            
            # Vortex Projectile Continuous Drag
            if p.active and p.effects and p.effects.get("synergy_name") == "vortex":
                drag_radius = 200.0 
                drag_strength = p.damage * 8.0
                
                for bot in all_bots:
                    if p.owner == "player" and bot.name == "Player": continue
                    if p.owner == "enemy" and bot.name != "Player": continue
                    
                    dx = p.x - bot.x
                    dy = p.y - bot.y
                    dist_sq = dx*dx + dy*dy
                    
                    if 100 < dist_sq < drag_radius**2:
                        dist = math.sqrt(dist_sq)
                        nx = dx / dist
                        ny = dy / dist
                        force = drag_strength / (dist * 0.1) * dt
                        bot.x += nx * force
                        bot.y += ny * force
        
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
                if p.owner == "player" and bot.name == "Player": continue
                if p.owner == "enemy" and bot.name != "Player": continue
                
                # Bounding Box Check (Generous)
                radius = constants.TILE_SIZE
                if bot.sprite:
                    radius = max(bot.sprite.get_width(), bot.sprite.get_height()) / 2
                
                dist = math.sqrt((p.x - bot.x)**2 + (p.y - bot.y)**2)
                if dist < radius:
                    # Pixel-Perfect Mask Check
                    hit = True
                    if bot.mask and bot.sprite:
                        # Calculate offset relative to sprite top-left
                        # Sprite is centered at bot.x, bot.y
                        sx = bot.x - bot.sprite.get_width() / 2
                        sy = bot.y - bot.sprite.get_height() / 2
                        offset_x = int(p.x - sx)
                        offset_y = int(p.y - sy)
                        
                        # Check bounds
                        if 0 <= offset_x < bot.sprite.get_width() and 0 <= offset_y < bot.sprite.get_height():
                            if not bot.mask.get_at((offset_x, offset_y)):
                                hit = False
                        else:
                            hit = False
                    
                    if hit:
                        health_before = bot.hp
                        
                        # Apply Status Effects
                        if p.effects and "status_effect" in p.effects:
                            status_name = p.effects["status_effect"]
                            duration = p.effects.get("duration", 5.0)
                            power = p.damage * 0.2 
                            bot.apply_status_effect(status_name, duration, power)
                        
                        # Synergy Specifics
                        # Handle multiple active synergies
                        active_synergies = p.effects.get("active_synergies", [])
                        # Fallback for legacy/single synergy
                        if not active_synergies and p.effects.get("synergy_name"):
                            active_synergies = [p.effects.get("synergy_name")]
                            
                        for synergy in active_synergies:
                            if synergy == "fire":
                                bot.apply_status_effect("burn", 3.0, p.damage * 0.2)
                                
                            if synergy == "ice":
                                bot.apply_status_effect("freeze", 3.0, 0)
                                
                            if synergy == "lightning":
                                chain_range = 250.0
                                chain_dmg = p.damage * 0.7
                                
                                nearest = None
                                min_d = float('inf')
                                for other in all_bots:
                                    if other == bot: continue
                                    if p.owner == "player" and other.name == "Player": continue
                                    if p.owner == "enemy" and other.name != "Player": continue
                                    
                                    d_sq = (bot.x - other.x)**2 + (bot.y - other.y)**2
                                    if d_sq < chain_range**2 and d_sq < min_d:
                                        min_d = d_sq
                                        nearest = other
                                
                                if nearest:
                                    nearest.take_damage(chain_dmg)
                                    self.visual_effects.append(VisualEffect(
                                        "lightning_bolt", bot.x, bot.y, 
                                        end_pos=(nearest.x, nearest.y), duration=0.2
                                    ))
        
                            if synergy == "vortex":
                                 self.visual_effects.append(VisualEffect(
                                    "implosion", p.x, p.y, radius=100, duration=0.3
                                ))
                                # Vortex Implosion (Instant Pull)
                                 implosion_radius = 200.0
                                 implosion_strength = 50.0
                                 for other_bot in all_bots:
                                     if other_bot == bot: continue
                                     if p.owner == "player" and other_bot.name == "Player": continue
                                     if p.owner == "enemy" and other_bot.name != "Player": continue
                                     
                                     dx = p.x - other_bot.x
                                     dy = p.y - other_bot.y
                                     dist_sq = dx*dx + dy*dy
                                     if dist_sq < implosion_radius**2:
                                         dist = math.sqrt(dist_sq)
                                         if dist > 10:
                                             pull = min(dist - 10, implosion_strength)
                                             other_bot.x += (dx / dist) * pull
                                             other_bot.y += (dy / dist) * pull
        
                            if synergy == "explosion":
                                # Explosion logic: Push away + Damage
                                explosion_radius = 150.0
                                explosion_force = 500.0
                                self.visual_effects.append(VisualEffect(
                                    "implosion", p.x, p.y, radius=explosion_radius, duration=0.2 # Reuse implosion visual for now
                                ))
                                
                                for other_bot in all_bots:
                                    if p.owner == "player" and other_bot.name == "Player": continue
                                    if p.owner == "enemy" and other_bot.name != "Player": continue
                                    
                                    dx = other_bot.x - p.x
                                    dy = other_bot.y - p.y
                                    dist_sq = dx*dx + dy*dy
                                    if dist_sq < explosion_radius**2:
                                        dist = math.sqrt(dist_sq)
                                        if dist < 1: dist = 1
                                        angle = math.atan2(dy, dx)
                                        other_bot.knockback(explosion_force, angle)
                                        other_bot.take_damage(p.damage * 0.5)
        
                            if synergy == "kinetic":
                                # Kinetic Knockback
                                knockback_force = 300.0
                                bot.knockback(knockback_force, p.angle)
    
                            # Vampiric
                            if synergy == "vampiric":
                                # Formula: Healing = (Base_Rarity_Percentage) * (Reactor_Power / 100)
                                # Base Rarity Percentage: Common=5%, Uncommon=10%, Rare=15%, Epic=20%, Legendary=25%
                                rarity = p.effects.get("rarity", "Common")
                                base_pct = 0.05
                                if rarity == "Uncommon": base_pct = 0.10
                                elif rarity == "Rare": base_pct = 0.15
                                elif rarity == "Epic": base_pct = 0.20
                                elif rarity == "Legendary": base_pct = 0.25
                                
                                # Reactor Power comes from the magnitude of the Vampiric synergy
                                # We need to pass this in effects. Let's assume 'vampiric_power' is passed.
                                reactor_power = p.effects.get("vampiric_power", 100.0)
                                
                                heal_pct = base_pct * (reactor_power / 100.0)
                                heal_amount = p.damage * heal_pct
                                
                                if p.owner == "player":
                                    for b in all_bots:
                                        if b.name == "Player":
                                            b.heal(heal_amount)
                                            break
    
                        bot.take_damage(p.damage)
                        
                        # Pierce Logic
                        if p.pierce_count > 0:
                            p.pierce_count -= 1
                            p.hit_list.append(id(bot))
                            p.lifetime = constants.PROJECTILE_LIFETIME # Reset range
                            # Do NOT set active = False
                        else:
                            p.active = False
                        
                        # AI Learning
                        if bot.name == "Player" and self.behavior_system is not None:
                            from entities.enemy import Enemy
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
                        
                        if p.active: # If piercing, continue to check other collisions? 
                            # No, usually one hit per frame per projectile is enough to avoid hitting same target multiple times if we didn't use hit_list correctly
                            # But we use hit_list. 
                            # However, if we break here, we stop checking other bots for this projectile this frame.
                            # Which is correct, we hit one thing.
                            break
                        else:
                            break

        # Enemy-Enemy Collision & Vortex Smash & Contagion
        enemies = [b for b in all_bots if b.name != "Player" and b.hp > 0]
        for i, bot1 in enumerate(enemies):
            # Contagion Spread
            if "poison" in bot1.status_effects:
                for bot2 in enemies:
                    if bot1 == bot2: continue
                    if "poison" in bot2.status_effects: continue
                    
                    d_sq = (bot1.x - bot2.x)**2 + (bot1.y - bot2.y)**2
                    if d_sq < (constants.TILE_SIZE * 2)**2: # Spread range
                        # Spread poison!
                        p_effect = bot1.status_effects["poison"]
                        bot2.apply_status_effect("poison", p_effect["duration"], p_effect["power"])

            for j in range(i + 1, len(enemies)):
                bot2 = enemies[j]
                
                dx = bot1.x - bot2.x
                dy = bot1.y - bot2.y
                dist_sq = dx*dx + dy*dy
                min_dist = constants.TILE_SIZE * 0.8
                
                if dist_sq < min_dist**2:
                    dist = math.sqrt(dist_sq)
                    if dist < 0.1: dist = 0.1
                    
                    # Separation
                    overlap = min_dist - dist
                    nx = dx / dist
                    ny = dy / dist
                    
                    sep_amount = overlap * 0.1
                    bot1.x += nx * sep_amount
                    bot1.y += ny * sep_amount
                    bot2.x -= nx * sep_amount
                    bot2.y -= ny * sep_amount
                    
                    # Smash Damage
                    near_vortex = False
                    for p in self.projectiles:
                        if p.active and p.effects and p.effects.get("synergy_name") == "vortex":
                            if p.owner == "enemy": continue # No friendly fire from enemy vortices
                            if (p.x - bot1.x)**2 + (p.y - bot1.y)**2 < 250**2:
                                near_vortex = True
                                break
                    
                    if near_vortex:
                        smash_dmg = overlap * 2.0 
                        bot1.take_damage(smash_dmg)
                        bot2.take_damage(smash_dmg)

    def render(self, screen, camera_x, camera_y):
        for v in self.vortices:
            v.render(screen, camera_x, camera_y)
        for z in self.zone_effects:
            z.render(screen, camera_x, camera_y)
        for p in self.projectiles:
            p.render(screen, camera_x, camera_y)
        for effect in self.visual_effects:
            effect.render(screen, camera_x, camera_y)

    def spawn_projectile(self, x, y, angle, speed, damage, damage_type, owner, effects=None):
        p = Projectile(x, y, angle, speed, damage, damage_type, owner, effects)
        self.projectiles.append(p)

    def spawn_vortex(self, x, y, radius, strength, duration, owner):
        v = Vortex(x, y, radius, strength, duration, owner)
        self.vortices.append(v)

    def deal_damage(self, target, amount, source=None):
        health_before = target.hp
        target.take_damage(amount)
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

    def spawn_zone_effect(self, effect_type, x, y, radius, duration, **kwargs):
        z = ZoneEffect(effect_type, x, y, radius, duration, **kwargs)
        self.zone_effects.append(z)
