# G:\work\pixelbots\entities\bot.py
import pygame
import logging
import math
from typing import Dict, Optional

from core.asset_manager import ProceduralAssetManager
from equipment.component import ComponentEquipment

logger = logging.getLogger(__name__)

class Bot:
    """Unified bot class for all characters."""

    def __init__(self, name: str, x: float, y: float, **kwargs):
        self.name = name
        self.x = float(x)
        self.y = float(y)
        
        # Physics
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.acceleration = 1200.0
        self.deceleration = 0.95
        self.max_speed = 200.0

        # Stats
        self.base_hp = kwargs.get("hp", 100)
        self.max_hp = self.base_hp
        self.hp = self.max_hp
        self.total_armor = 0
        self.speed_bonus = 0

        # Equipment
        self.components: Dict[str, Optional[ComponentEquipment]] = {
            s: None for s in ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "back"]
        }

        # Visuals
        self.asset_manager: Optional[ProceduralAssetManager] = None
        self.sprite_name = kwargs.get("sprite", "bots/default_bot32.png")
        self.sprite: Optional[pygame.Surface] = None
        self.mask: Optional[pygame.mask.Mask] = None
        
        self.status_effects = {} # name -> {duration, power, tick_timer}
        
        self.recalculate_stats()
        logger.debug(f"Initialized bot '{self.name}'.")

    def update(self, dt: float):
        self.update_status_effects(dt)

    def update_status_effects(self, dt: float):
        expired = []
        for name, effect in self.status_effects.items():
            effect["duration"] -= dt
            if effect["duration"] <= 0:
                expired.append(name)
                continue
                
            # Handle tick effects
            if name == "burn":
                effect["tick_timer"] -= dt
                if effect["tick_timer"] <= 0:
                    damage = effect["power"]
                    self.take_damage(damage)
                    effect["tick_timer"] = 1.0 # Tick every second
            elif name == "decay":
                effect["tick_timer"] -= dt
                if effect["tick_timer"] <= 0:
                    damage = effect["power"] * 0.5
                    self.take_damage(damage)
                    effect["tick_timer"] = 0.5 # Tick faster
            elif name == "poison":
                effect["tick_timer"] -= dt
                if effect["tick_timer"] <= 0:
                    damage = effect["power"]
                    self.take_damage(damage)
                    effect["tick_timer"] = 1.0 # Tick every second
            
            # Handle stat modifiers (applied every frame or just once? 
            # Better to apply in recalculate_stats or get_speed/get_armor)
            # For now, speed is handled dynamically in update_movement if needed, 
            # but let's just modify a temp multiplier? 
            # Simpler: check status effects in get_current_speed()
            
        for name in expired:
            del self.status_effects[name]
            if name == "freeze":
                logger.debug(f"{self.name} is no longer frozen.")

    def apply_status_effect(self, name: str, duration: float, power: float):
        if name in self.status_effects:
            # Refresh duration, maybe stack power?
            self.status_effects[name]["duration"] = max(self.status_effects[name]["duration"], duration)
            self.status_effects[name]["power"] = max(self.status_effects[name]["power"], power)
        else:
            self.status_effects[name] = {"duration": duration, "power": power, "tick_timer": 1.0}
            logger.debug(f"{self.name} applied status: {name}")

    def update_movement(self, input_x: float, input_y: float, dt: float, game_map=None):
        # Apply Status Effects to Movement
        accel = self.acceleration
        max_spd = self.max_speed
        
        if "freeze" in self.status_effects:
            accel *= 0.5
            max_spd *= 0.5
            
        mag = math.sqrt(input_x**2 + input_y**2)
        if mag > 0:
            norm_x, norm_y = input_x / mag, input_y / mag
            self.velocity_x += norm_x * accel * dt
            self.velocity_y += norm_y * accel * dt
        else:
            self.velocity_x *= self.deceleration
            self.velocity_y *= self.deceleration
            if abs(self.velocity_x) < 1: self.velocity_x = 0
            if abs(self.velocity_y) < 1: self.velocity_y = 0

        current_speed = math.sqrt(self.velocity_x**2 + self.velocity_y**2)
        if current_speed > max_spd:
            # Soft clamp: allow exceeding but decay rapidly (for knockback)
            if current_speed > max_spd * 1.1:
                # Knockback territory: Fast decay
                self.velocity_x *= 0.92
                self.velocity_y *= 0.92
            else:
                # Normal movement cap
                scale = max_spd / current_speed
                self.velocity_x *= scale
                self.velocity_y *= scale

        # Predict next position
        next_x = self.x + self.velocity_x * dt
        next_y = self.y + self.velocity_y * dt
        
        # Collision Detection (if game_map provided)
        if game_map:
            import constants
            tile_size = constants.TILE_SIZE
            
            # Check X collision
            tx = int(next_x / tile_size)
            ty = int(self.y / tile_size)
            
            collision_x = False
            if not (0 <= tx < game_map.width and 0 <= ty < game_map.height):
                collision_x = True
            elif game_map.terrain[ty][tx] in constants.NON_WALKABLE_TERRAIN or (tx, ty) in game_map.obstacles:
                collision_x = True
                
            if collision_x:
                # Collision Damage check
                if abs(self.velocity_x) > 300: # Threshold for impact damage
                    dmg = abs(self.velocity_x) * 0.1
                    self.take_damage(dmg)
                    logger.debug(f"{self.name} hit wall X with speed {self.velocity_x}, took {dmg} damage")
                
                self.velocity_x = 0
                next_x = self.x # Cancel X movement
            
            # Check Y collision
            tx = int(next_x / tile_size) # Use updated X
            ty = int(next_y / tile_size)
            
            collision_y = False
            if not (0 <= tx < game_map.width and 0 <= ty < game_map.height):
                collision_y = True
            elif game_map.terrain[ty][tx] in constants.NON_WALKABLE_TERRAIN or (tx, ty) in game_map.obstacles:
                collision_y = True
                
            if collision_y:
                # Collision Damage check
                if abs(self.velocity_y) > 300:
                    dmg = abs(self.velocity_y) * 0.1
                    self.take_damage(dmg)
                    logger.debug(f"{self.name} hit wall Y with speed {self.velocity_y}, took {dmg} damage")
                
                self.velocity_y = 0
                next_y = self.y # Cancel Y movement

        self.x = next_x
        self.y = next_y

    def knockback(self, force: float, angle: float):
        """Applies a knockback force to the bot."""
        import math
        self.velocity_x += math.cos(angle) * force
        self.velocity_y += math.sin(angle) * force

    def recalculate_stats(self):
        self.total_armor = 0
        self.max_hp = self.base_hp
        self.speed_bonus = 0
        for comp in self.components.values():
            if comp:
                stats = comp.calculate_stats()
                self.total_armor += stats.get("armor", 0)
                self.max_hp += stats.get("hp", 0)
                self.speed_bonus += stats.get("speed", 0)
        # Logarithmic scaling: 150 base, + 50 * log(bonus + 1)
        # If bonus is 1 (common leg), speed = 150 + 50 * 0.69 = 185
        # If bonus is 10 (many upgrades), speed = 150 + 50 * 2.39 = 270
        # This prevents game-breaking speed at high levels while rewarding early upgrades.
        self.max_speed = 150.0 + (math.log(self.speed_bonus + 1) * 50.0)
        self.hp = min(self.hp, self.max_hp)

    def equip_component(self, component: ComponentEquipment):
        if component and component.slot in self.components:
            self.components[component.slot] = component
            self.recalculate_stats()
            return True
        return False

    def take_damage(self, amount: float):
        actual_damage = max(1, amount - self.total_armor)
        self.hp -= actual_damage
        logger.debug(f"'{self.name}' took {actual_damage:.1f} damage ({self.hp:.1f}/{self.max_hp:.1f} HP)")
        if self.hp <= 0:
            self.hp = 0
            logger.info(f"'{self.name}' has been destroyed!")

    def heal(self, amount: float):
        """Restores health to the bot."""
        old_hp = self.hp
        self.hp = min(self.hp + amount, self.max_hp)
        healed = self.hp - old_hp
        if healed > 0:
            logger.debug(f"'{self.name}' healed for {healed:.1f} ({self.hp:.1f}/{self.max_hp:.1f} HP)")

    def render(self, screen: pygame.Surface, offset_x: int, offset_y: int):
        if self.sprite is None and self.asset_manager:
            self.sprite = self.asset_manager.get_image(self.sprite_name)
            if self.sprite:
                self.mask = pygame.mask.from_surface(self.sprite)

        if self.sprite:
            sx = int(self.x + offset_x - self.sprite.get_width() / 2)
            sy = int(self.y + offset_y - self.sprite.get_height() / 2)
            screen.blit(self.sprite, (sx, sy))
            
            # Render Status Effects
            if self.status_effects:
                # Simple visual indicators (colored circles for now)
                # We can stack them or cycle them. Let's stack small dots above the health bar.
                effect_colors = {
                    "burn": (255, 100, 0),
                    "freeze": (100, 200, 255),
                    "shock": (255, 255, 0),
                    "poison": (50, 200, 50),
                    "decay": (150, 50, 200)
                }
                
                x_offset = 0
                for name in self.status_effects:
                    color = effect_colors.get(name, (255, 255, 255))
                    # Draw a small circle above the bot
                    pygame.draw.circle(screen, color, (sx + 5 + x_offset, sy - 8), 3)
                    x_offset += 8
            
            self.render_health_bar(screen, sx, sy)

    def render_health_bar(self, screen, sx, sy):
        if self.hp < self.max_hp:
            bar_w = self.sprite.get_width()
            bar_h = 5
            hp_pct = self.hp / self.max_hp if self.max_hp > 0 else 0
            bg_rect = (sx, sy - bar_h - 4, bar_w, bar_h)
            hp_rect = (sx, sy - bar_h - 4, int(bar_w * hp_pct), bar_h)
            pygame.draw.rect(screen, (80, 0, 0), bg_rect)
            pygame.draw.rect(screen, (0, 220, 0), hp_rect)

