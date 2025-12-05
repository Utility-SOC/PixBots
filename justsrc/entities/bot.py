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
        
        self.recalculate_stats()
        logger.debug(f"Initialized bot '{self.name}'.")

    def update(self, dt: float):
        pass # Cooldowns would be updated here.

    def update_movement(self, input_x: float, input_y: float, dt: float):
        mag = math.sqrt(input_x**2 + input_y**2)
        if mag > 0:
            norm_x, norm_y = input_x / mag, input_y / mag
            self.velocity_x += norm_x * self.acceleration * dt
            self.velocity_y += norm_y * self.acceleration * dt
        else:
            self.velocity_x *= self.deceleration
            self.velocity_y *= self.deceleration
            if abs(self.velocity_x) < 1: self.velocity_x = 0
            if abs(self.velocity_y) < 1: self.velocity_y = 0

        current_speed = math.sqrt(self.velocity_x**2 + self.velocity_y**2)
        if current_speed > self.max_speed:
            scale = self.max_speed / current_speed
            self.velocity_x *= scale
            self.velocity_y *= scale

        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt

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

    def render(self, screen: pygame.Surface, offset_x: int, offset_y: int):
        if self.sprite is None and self.asset_manager:
            self.sprite = self.asset_manager.get_image(self.sprite_name)

        if self.sprite:
            sx = int(self.x + offset_x - self.sprite.get_width() / 2)
            sy = int(self.y + offset_y - self.sprite.get_height() / 2)
            screen.blit(self.sprite, (sx, sy))
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

