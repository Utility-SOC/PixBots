from .bot import Bot
import math
import random
import pygame
import logging
from .sprite_generator import ProceduralBotGenerator

class Enemy(Bot):
    # Static generator instance to share across enemies (optional, but good for caching if we add it)
    _generator = ProceduralBotGenerator()

    def __init__(self, name, x, y, level=1, ai_class="grunt", biome="forest"):
        self.ai_class = ai_class
        
        # Generate unique seed for this enemy based on position and random factor
        # This ensures if we reload the game with same seed, enemies might look similar if we used map seed,
        # but here we want variety.
        seed = random.randint(0, 999999)
        
        if ai_class == "sniper":
            sprite, metadata = self._generator.generate_sniper(seed)
        elif ai_class == "ambusher":
            sprite, metadata = self._generator.generate_ambusher(biome, seed)
        elif ai_class == "Boss":
            sprite, metadata = self._generator.generate_boss(seed)
        else: # Grunt
            sprite, metadata = self._generator.generate_grunt(seed)
        
        # Bot expects 'sprite' kwarg to be a path string, but we have a Surface.
        # So we pass a dummy string and set self.sprite manually.
        super().__init__(name, x, y, hp=50 + (level * 10), sprite="procedural_generated")
        self.sprite = sprite
        
        # Apply metadata (weapons)
        if metadata and "weapons" in metadata:
            self.weapons = metadata["weapons"]
        if self.sprite:
            self.mask = pygame.mask.from_surface(self.sprite)
        self.level = level
        self.is_player = False
        self.target = None
        
        # AI Settings based on class
        self.weapons = []
        if self.ai_class == "sniper":
            self.detection_range = 600
            self.attack_range = 500
            self.weapons.append({"damage": 15 + level * 2, "speed": 500, "cooldown": 2.5, "last_shot": 0, "synergy": None})
            self.max_speed = 150 # Slower
        elif self.ai_class == "ambusher":
            self.detection_range = 400
            self.attack_range = 150
            self.weapons.append({"damage": 10 + level, "speed": 300, "cooldown": 0.8, "last_shot": 0, "synergy": None})
            self.max_speed = 250 # Fast
        elif self.ai_class == "Boss":
            self.detection_range = 800
            self.attack_range = 400
            # Bosses will get weapons assigned by generator or default here
            # Default fallback if generator didn't assign
            self.weapons.append({"damage": 25 + level * 3, "speed": 250, "cooldown": 1.0, "last_shot": 0, "synergy": None})
            self.max_speed = 120 # Slow but imposing
            self.hp *= 5 # Massive HP pool
        else: # Grunt
            self.detection_range = 400
            self.attack_range = 200
            self.weapons.append({"damage": 5 + level, "speed": 200, "cooldown": 1.5, "last_shot": 0, "synergy": None})
        
        # Tactics
        self.tactics = ["attack"]
        if level >= 3: self.tactics.append("buff")
        if level >= 5: self.tactics.append("shield")
        
        self.buff_active = False
        self.shield_active = False
        self.shield_cooldown = 0
        self.buff_cooldown = 0
        
        # AI State
        self.state = "idle" # idle, chase, attack, flee
        self.move_timer = 0
        self.move_dir = (0, 0)
        
        # Random Synergy
        # 20% chance per level to have a synergy (Level 1 = 20%, Level 5 = 100%)
        self.synergy = None
        if random.random() < (level * 0.2):
            synergies = ["fire", "ice", "vortex", "explosion", "kinetic", "vampiric"]
            self.synergy = random.choice(synergies)
            # Boss always has a synergy
            if self.ai_class == "Boss":
                self.synergy = random.choice(["vortex", "explosion", "fire"]) # Bosses get the cool ones

    def update(self, dt, player, combat_system, current_time, game_map=None):
        super().update(dt)
        self.target = player
        
        dist = math.sqrt((self.target.x - self.x)**2 + (self.target.y - self.y)**2)
        
        if self.state == "idle":
            if dist < self.detection_range:
                self.state = "chase"
            else:
                # Random movement
                self.move_timer -= dt
                if self.move_timer <= 0:
                    self.move_timer = random.uniform(1.0, 3.0)
                    angle = random.uniform(0, math.pi * 2)
                    self.move_dir = (math.cos(angle), math.sin(angle))
                self.update_movement(self.move_dir[0], self.move_dir[1], dt, game_map)
                
        elif self.state == "chase":
            if self.ai_class == "sniper":
                if dist < self.attack_range * 0.5:
                    self.state = "flee"
                elif dist < self.attack_range:
                    self.state = "attack"
                elif dist > self.detection_range * 1.5:
                    self.state = "idle"
                else:
                    # Move to range
                    dx = self.target.x - self.x
                    dy = self.target.y - self.y
                    self.update_movement(dx, dy, dt, game_map)
            else: # Grunt / Ambusher
                if dist < self.attack_range:
                    self.state = "attack"
                elif dist > self.detection_range * 1.5:
                    self.state = "idle"
                else:
                    # Move towards player
                    dx = self.target.x - self.x
                    dy = self.target.y - self.y
                    self.update_movement(dx, dy, dt, game_map)

        elif self.state == "flee":
             if dist > self.attack_range * 0.8:
                 self.state = "attack"
             else:
                 # Run away!
                 dx = self.x - self.target.x
                 dy = self.y - self.target.y
                 self.update_movement(dx, dy, dt, game_map)
                
        elif self.state == "attack":
            if dist > self.attack_range * 1.2:
                self.state = "chase"
            elif self.ai_class == "sniper" and dist < self.attack_range * 0.4:
                self.state = "flee"
            else:
                # Stop and shoot (or keep moving if ambusher?)
                if self.ai_class == "ambusher":
                     # Circle strafe? For now just chase/attack
                     dx = self.target.x - self.x
                     dy = self.target.y - self.y
                     self.update_movement(dx, dy, dt, game_map)
                else:
                    self.update_movement(0, 0, dt, game_map)
                
                # Try tactics
                self.try_tactics(dt)
                
                self.shoot(self.target.x, self.target.y, combat_system, current_time)

    def try_tactics(self, dt):
        if self.shield_cooldown > 0: self.shield_cooldown -= dt
        if self.buff_cooldown > 0: self.buff_cooldown -= dt
        
        if "shield" in self.tactics and not self.shield_active and self.shield_cooldown <= 0:
            if self.hp < self.max_hp * 0.5:
                self.shield_active = True
                self.shield_cooldown = 10.0 
                logging.getLogger(__name__).info(f"{self.name} activated SHIELD!")

        if "buff" in self.tactics and not self.buff_active and self.buff_cooldown <= 0:
            if random.random() < 0.01: 
                self.buff_active = True
                if self.weapons:
                    self.weapons[0]["damage"] *= 1.5
                self.buff_cooldown = 15.0
                logging.getLogger(__name__).info(f"{self.name} activated BUFF!")

    def take_damage(self, amount):
        import constants
        if self.ai_class == "Boss" and getattr(constants, "BOSS_INVULNERABLE", False):
            return # No damage
            
        if self.shield_active:
            amount *= 0.5 # 50% reduction
        super().take_damage(amount)

    def shoot(self, target_x, target_y, combat_system, current_time):
        for weapon in self.weapons:
            if current_time - weapon["last_shot"] < weapon["cooldown"]:
                continue
                
            angle = math.atan2(target_y - self.y, target_x - self.x)
            
            # Add some inaccuracy
            angle += random.uniform(-0.1, 0.1)
            
            effects = {}
            # Use weapon specific synergy if available, else fallback to bot synergy
            synergy = weapon.get("synergy") or self.synergy
            
            if synergy:
                effects["synergy_name"] = synergy
                # Add specific params if needed
                if synergy == "vortex":
                    effects["spawn_vortex"] = {"radius": 100, "strength": 50, "duration": 3.0}
                elif synergy == "explosion":
                    effects["explosion_radius"] = 60
                    effects["explosion_force"] = 200
                elif synergy == "vampiric":
                    effects["vampiric_power"] = 50.0 # Enemies heal less
            
            combat_system.spawn_projectile(
                self.x, self.y, angle, 
                weapon["speed"], weapon["damage"], 
                "energy", "enemy",
                effects=effects
            )
            weapon["last_shot"] = current_time
