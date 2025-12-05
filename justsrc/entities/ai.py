# G:\work\pixelbots\entities\ai.py
import math
import logging

logger = logging.getLogger(__name__)

class AIController:
    """Provides static methods for controlling non-player bot AI."""

    DETECTION_RADIUS = 10.0 # in game units/tiles
    FLEE_HP_THRESHOLD = 0.25

    @staticmethod
    def decide_action(bot: 'Bot', player: 'Player', dt: float):
        if bot.hp <= 0: return

        distance_to_player = math.hypot(bot.x - player.x, bot.y - player.y)
        is_low_health = (bot.hp / bot.max_hp) < AIController.FLEE_HP_THRESHOLD

        if is_low_health:
            AIController.flee_from(bot, player, dt)
            return

        weapon_range = 5.0 * 32 # Assuming range is in tiles, convert to pixels
        if distance_to_player <= weapon_range:
            logger.debug(f"'{bot.name}' is in range to attack.")
            # bot.fire_weapon(...) would be called here.
        elif distance_to_player <= AIController.DETECTION_RADIUS * 32:
            AIController.move_towards(bot, player, dt)

    @staticmethod
    def move_towards(bot, target, dt):
        dx = target.x - bot.x
        dy = target.y - bot.y
        bot.update_movement(dx, dy, dt)

    @staticmethod
    def flee_from(bot, target, dt):
        dx = bot.x - target.x
        dy = bot.y - target.y
        bot.update_movement(dx, dy, dt)

