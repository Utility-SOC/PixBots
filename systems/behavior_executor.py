# pixbots/systems/behavior_executor.py
# Executes JSON-defined behaviors by mapping action_types to actual game logic

import logging
import math
import random
from typing import Dict, Any, Optional
import pygame

logger = logging.getLogger(__name__)

class BehaviorExecutor:
    """
    Maps JSON behavior definitions to actual game actions.
    This is the bridge between declarative JSON and imperative code.
    """
    
    def __init__(self, game_state):
        """
        Args:
            game_state: Reference to main game state (for spawning projectiles, effects, etc.)
        """
        self.game_state = game_state
        
        # Register all action handlers
        self.action_handlers = {
            # Movement behaviors
            "move_toward": self._execute_move_toward,
            "kite_away": self._execute_kite_away,
            "flanking_move": self._execute_flanking_move,
            "tactical_move": self._execute_tactical_move,
            "sprint_attack": self._execute_sprint_attack,
            
            # Combat behaviors
            "melee_attack": self._execute_melee_attack,
            "precision_shot": self._execute_precision_shot,
            "rapid_attack": self._execute_rapid_attack,
            "area_attack": self._execute_area_attack,
            "critical_shot": self._execute_critical_shot,
            "area_denial": self._execute_area_denial,
            
            # Stealth/utility behaviors
            "stealth": self._execute_stealth,
            "deploy_smoke": self._execute_deploy_smoke,
            "teleport_attack": self._execute_teleport_attack,
            "scout_alert": self._execute_scout_alert,
            
            # Tactical behaviors
            "group_up": self._execute_group_up,
            "defensive_stance": self._execute_defensive_stance,
            "enrage": self._execute_enrage,
            
            # Boss behaviors
            "summon_allies": self._execute_summon_allies,
            "combo": self._execute_combo,
        }
    
    def execute_behavior(self, enemy, behavior, player, current_time: float) -> bool:
        """
        Execute a behavior for an enemy.
        
        Args:
            enemy: The enemy executing the behavior
            behavior: BehaviorEntry from JSON
            player: The player target
            current_time: Current game time
            
        Returns:
            bool: True if behavior executed successfully
        """
        action_type = behavior.action_type
        params = behavior.parameters
        
        # Check for combo/compound behaviors
        if "+" in action_type:
            # Boss mutation - execute multiple behaviors in sequence
            sub_actions = action_type.split("+")
            for sub_action in sub_actions:
                if sub_action in self.action_handlers:
                    self.action_handlers[sub_action](enemy, params, player, current_time)
            return True
        
        # Check for amplified behaviors
        if action_type.startswith("amplified_"):
            base_action = action_type.replace("amplified_", "")
            if base_action in self.action_handlers:
                return self.action_handlers[base_action](enemy, params, player, current_time)
        
        # Standard behavior execution
        handler = self.action_handlers.get(action_type)
        if handler:
            return handler(enemy, params, player, current_time)
        else:
            logger.warning(f"No handler for action_type: {action_type}")
            return False
    
    # ===== MOVEMENT BEHAVIORS =====
    
    def _get_target_pos(self, enemy, player):
        """Calculates perceived target position, accounting for Cloak."""
        tx, ty = player.x, player.y
        
        # Check against player's cloak state
        if getattr(player, "is_cloaked", False):
            # Apply "Estimation Error" / Aggro Drop
            # Enemies guess randomly around the player
            # Bosses/Ambushers might have better tracking (less noise), but for now generic:
            import random
            noise_range = 300 # Significant error
            tx += random.uniform(-noise_range, noise_range)
            ty += random.uniform(-noise_range, noise_range)
            
        return tx, ty

    # ===== MOVEMENT BEHAVIORS =====
    
    def _execute_move_toward(self, enemy, params, player, current_time):
        """Simple move toward target."""
        speed_mult = params.get("speed_multiplier", 1.0)
        min_dist = params.get("min_distance", 50)
        
        tx, ty = self._get_target_pos(enemy, player)
        dx = tx - enemy.x
        dy = ty - enemy.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > min_dist:
            enemy.max_speed = enemy.base_speed * speed_mult if hasattr(enemy, 'base_speed') else 200 * speed_mult
            enemy.update_movement(dx, dy, 0.016)  # Assume ~60fps
        return True
    
    def _execute_kite_away(self, enemy, params, player, current_time):
        """Maintain distance from player (sniper behavior)."""
        ideal_range = params.get("ideal_range", 450)
        min_range = params.get("min_range", 350)
        retreat_speed = params.get("retreat_speed", 1.1)
        
        tx, ty = self._get_target_pos(enemy, player)
        dx = tx - enemy.x
        dy = ty - enemy.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist < min_range:
            # Too close - retreat
            enemy.update_movement(-dx, -dy, 0.016)
            enemy.max_speed *= retreat_speed
        elif dist > ideal_range * 1.5:
            # Too far - advance
            enemy.update_movement(dx, dy, 0.016)
        return True
    
    def _execute_flanking_move(self, enemy, params, player, current_time):
        """Circle around player (ambush behavior)."""
        direction = params.get("direction", "left")
        arc_degrees = params.get("arc_degrees", 120)
        speed_mult = params.get("speed_multiplier", 1.4)
        
        # Calculate perpendicular vector
        tx, ty = self._get_target_pos(enemy, player)
        dx = tx - enemy.x
        dy = ty - enemy.y
        
        # Rotate 90 degrees
        if direction == "left":
            flank_dx = -dy
            flank_dy = dx
        else:
            flank_dx = dy
            flank_dy = -dx
        
        enemy.max_speed *= speed_mult
        enemy.update_movement(flank_dx, flank_dy, 0.016)
        return True
    
    def _execute_tactical_move(self, enemy, params, player, current_time):
        """Reposition for cover/advantage."""
        # Simplified: move to random nearby position
        if not hasattr(enemy, 'tactical_target'):
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(100, 200)
            enemy.tactical_target = (
                enemy.x + math.cos(angle) * dist,
                enemy.y + math.sin(angle) * dist
            )
        
        tx, ty = enemy.tactical_target
        dx = tx - enemy.x
        dy = ty - enemy.y
        
        if math.sqrt(dx**2 + dy**2) < 20:
            del enemy.tactical_target
        else:
            enemy.update_movement(dx, dy, 0.016)
        return True
    
    def _execute_sprint_attack(self, enemy, params, player, current_time):
        """Berserker rush with speed boost."""
        speed_mult = params.get("speed_multiplier", 2.0)
        damage_bonus = params.get("damage_bonus", 1.3)
        
        # Set temporary buff
        if not hasattr(enemy, 'sprint_active'):
            enemy.sprint_active = True
            enemy.sprint_damage_mult = damage_bonus
            enemy.max_speed *= speed_mult
        
        self._execute_move_toward(enemy, params, player, current_time)
        return True
    
    # ===== COMBAT BEHAVIORS =====
    
    def _execute_melee_attack(self, enemy, params, player, current_time):
        """Shield bash / melee hit."""
        damage = params.get("damage", 10)
        knockback = params.get("knockback", 50)
        cooldown = params.get("cooldown", 2.0)
        
        # Check cooldown
        if hasattr(enemy, 'last_melee_time'):
            if current_time - enemy.last_melee_time < cooldown:
                return False
        
        # Check range
        tx, ty = self._get_target_pos(enemy, player)
        dx = tx - enemy.x
        dy = ty - enemy.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist < 60:  # Melee range
            # Deal damage to player
            if hasattr(self.game_state, 'combat_system'):
                self.game_state.combat_system.deal_damage(player, damage, enemy)
            
            # Apply knockback
            if knockback > 0:
                direction = math.atan2(dy, dx)
                player.x += math.cos(direction) * knockback
                player.y += math.sin(direction) * knockback
            
            enemy.last_melee_time = current_time
            return True
        
        return False
    
    def _execute_precision_shot(self, enemy, params, player, current_time):
        """Sniper long-range shot."""
        charge_time = params.get("charge_time", 1.5)
        damage = params.get("damage", 25)
        accuracy = params.get("accuracy", 0.95)
        
        # Simplified: just shoot if not on cooldown
        if not hasattr(enemy, 'last_shot_time'):
            enemy.last_shot_time = 0
        
        if current_time - enemy.last_shot_time >= charge_time:
            # Fire projectile
            if hasattr(self.game_state, 'spawn_projectile'):
                self.game_state.spawn_projectile(enemy, player, damage, speed=500)
            enemy.last_shot_time = current_time
            return True
        
        return False
    
    def _execute_rapid_attack(self, enemy, params, player, current_time):
        """Burst fire (ambush behavior)."""
        shots = params.get("shots", 3)
        delay = params.get("delay_between", 0.2)
        damage_per_shot = params.get("damage_per_shot", 10)
        
        if not hasattr(enemy, 'burst_state'):
            enemy.burst_state = {"shots_fired": 0, "last_shot": current_time}
        
        state = enemy.burst_state
        if state["shots_fired"] < shots:
            if current_time - state["last_shot"] >= delay:
                # Fire shot
                if hasattr(self.game_state, 'spawn_projectile'):
                    self.game_state.spawn_projectile(enemy, player, damage_per_shot, speed=300)
                state["shots_fired"] += 1
                state["last_shot"] = current_time
        else:
            # Burst complete
            del enemy.burst_state
            return True
        
        return False
    
    def _execute_area_attack(self, enemy, params, player, current_time):
        """Boss AOE blast."""
        radius = params.get("radius", 200)
        damage = params.get("damage", 20)
        knockback = params.get("knockback", 100)
        
        # Check if player in range
        dx = player.x - enemy.x
        dy = player.y - enemy.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist < radius:
            if hasattr(self.game_state, 'combat_system'):
                self.game_state.combat_system.deal_damage(player, damage, enemy)
            
            # Knockback
            direction = math.atan2(dy, dx)
            player.x += math.cos(direction) * knockback
            player.y += math.sin(direction) * knockback
        
        return True
    
    def _execute_critical_shot(self, enemy, params, player, current_time):
        """Headshot attempt."""
        damage_mult = params.get("damage_multiplier", 2.5)
        base_damage = enemy.weapon.get("damage", 15) if hasattr(enemy, 'weapon') else 15
        
        return self._execute_precision_shot(
            enemy,
            {"damage": base_damage * damage_mult, "charge_time": params.get("charge_time", 2.5)},
            player,
            current_time
        )
    
    def _execute_area_denial(self, enemy, params, player, current_time):
        """Suppressive fire."""
        # Simplified: rapid low-damage shots in player direction
        return self._execute_rapid_attack(
            enemy,
            {"shots": params.get("shots", 5), "damage_per_shot": 5},
            player,
            current_time
        )
    
    def _execute_scout_alert(self, enemy, params, player, current_time):
        """Scout alerts nearby enemies."""
        # Check LOS to player
        tx, ty = self._get_target_pos(enemy, player)
        dx = tx - enemy.x
        dy = ty - enemy.y
        dist = math.sqrt(dx**2 + dy**2)
        
        detection_range = params.get("detection_range", 600)
        if dist < detection_range:
            # ALERT!
            # 1/3 map size radius. Map is 100xTILE_SIZE. TILE_SIZE=64 usually? 
            # Assuming map width approx 6400. 1/3 is ~2100.
            alert_radius = params.get("alert_radius", 2000)
            
            # Check cooldown
            if hasattr(enemy, 'last_alert_time') and current_time - enemy.last_alert_time < 10.0:
                return True # On cooldown, but "executing"
                
            enemy.last_alert_time = current_time
            logger.info(f"{enemy.name} ALERTED enemies within {alert_radius}px!")
            
            # Find enemies in range
            count = 0
            if hasattr(self.game_state, 'all_bots'):
                for bot in self.game_state.all_bots:
                    if bot != enemy and bot != player and not getattr(bot, 'is_player', False):
                        bdx = bot.x - enemy.x
                        bdy = bot.y - enemy.y
                        if math.sqrt(bdx**2 + bdy**2) < alert_radius:
                            # Wake them up!
                            bot.target_pos = (player.x, player.y)
                            if hasattr(bot, 'state'):
                                bot.state = "chase"
                            # Reset idle timer so they move immediately
                            bot.move_timer = 0
                            count += 1
                            
            # Visual feedback? Maybe a sound or effect later
            if count > 0:
                logging.getLogger(__name__).info(f"  -> {count} enemies responded to alert.")
                
            # Flee after alerting
            return self._execute_kite_away(enemy, {"min_range": 500, "retreat_speed": 1.5}, player, current_time)
            
        return False
    
    # ===== UTILITY BEHAVIORS =====
    
    def _execute_stealth(self, enemy, params, player, current_time):
        """Cloak/ambush activate."""
        duration = params.get("duration", 5.0)
        detection_mult = params.get("detection_radius_multiplier", 0.3)
        
        if not hasattr(enemy, 'cloaked_until'):
            enemy.cloaked_until = current_time + duration
            enemy.detection_range *= detection_mult
            enemy.is_cloaked = True
            logger.info(f"{enemy.name} activated cloak")
        
        if current_time >= enemy.cloaked_until:
            enemy.is_cloaked = False
            del enemy.cloaked_until
        
        return True
    
    def _execute_deploy_smoke(self, enemy, params, player, current_time):
        """Smoke escape."""
        radius = params.get("radius", 150)
        duration = params.get("duration", 4.0)
        
        # Deploy smoke at current position
        if hasattr(self.game_state, 'spawn_effect'):
            self.game_state.spawn_effect("smoke", enemy.x, enemy.y, radius, duration)
        
        # Retreat
        return self._execute_kite_away(
            enemy,
            {"retreat_speed": params.get("retreat_speed", 1.8)},
            player,
            current_time
        )
    
    def _execute_teleport_attack(self, enemy, params, player, current_time):
        """Boss teleport strike."""
        teleport_range = params.get("teleport_range", 300)
        damage = params.get("damage", 30)
        
        # Teleport behind player
        angle = random.uniform(0, math.pi * 2)
        enemy.x = player.x + math.cos(angle) * 100
        enemy.y = player.y + math.sin(angle) * 100
        
        # Instant attack
        return self._execute_melee_attack(
            enemy,
            {"damage": damage, "cooldown": 0},
            player,
            current_time
        )
    
    def _execute_group_up(self, enemy, params, player, current_time):
        """Swarm formation."""
        if not enemy.squad_id or not hasattr(self.game_state, 'squad_manager'):
            return False
            
        squad = self.game_state.squad_manager.squads.get(enemy.squad_id)
        if not squad:
            return False
            
        target_pos = squad.get_formation_pos(enemy)
        if target_pos:
            tx, ty = target_pos
            dx = tx - enemy.x
            dy = ty - enemy.y
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist > 10:
                enemy.update_movement(dx, dy, 0.016)
                return True
        
        return False
    
    def _execute_defensive_stance(self, enemy, params, player, current_time):
        """Shield phase."""
        damage_reduction = params.get("damage_reduction", 0.75)
        duration = params.get("duration", 5.0)
        
        if not hasattr(enemy, 'shield_until'):
            enemy.shield_until = current_time + duration
            enemy.damage_reduction = damage_reduction
        
        if current_time >= enemy.shield_until:
            enemy.damage_reduction = 0
            del enemy.shield_until
        
        return True
    
    def _execute_enrage(self, enemy, params, player, current_time):
        """Boss rage mode."""
        health_threshold = params.get("health_threshold", 0.5)
        damage_boost = params.get("damage_boost", 1.5)
        
        if enemy.hp / enemy.max_hp < health_threshold:
            if not hasattr(enemy, 'is_enraged'):
                enemy.is_enraged = True
                enemy.damage_multiplier = damage_boost
                logger.info(f"{enemy.name} ENRAGED!")
        
        return True
    
    def _execute_summon_allies(self, enemy, params, player, current_time):
        """Boss summons grunts."""
        ally_type = params.get("ally_type", "grunt")
        count = params.get("count", 2)
        cooldown = params.get("cooldown", 20.0)
        
        if not hasattr(enemy, 'last_summon_time'):
            enemy.last_summon_time = 0
        
        if current_time - enemy.last_summon_time >= cooldown:
            if hasattr(self.game_state, 'spawn_enemy'):
                for _ in range(count):
                    angle = random.uniform(0, math.pi * 2)
                    spawn_x = enemy.x + math.cos(angle) * 200
                    spawn_y = enemy.y + math.sin(angle) * 200
                    self.game_state.spawn_enemy(ally_type, spawn_x, spawn_y)
            
            enemy.last_summon_time = current_time
            logger.info(f"{enemy.name} summoned {count} {ally_type}s!")
            return True
        
        return False
    
    def _execute_combo(self, enemy, params, player, current_time):
        """Boss combo behavior."""
        phases = params.get("phases", [])
        
        for phase in phases:
            if phase in self.action_handlers:
                self.action_handlers[phase](enemy, params, player, current_time)
        
        return True
