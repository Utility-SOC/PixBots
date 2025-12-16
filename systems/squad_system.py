
import uuid
import logging
import math
from typing import Dict, List, Optional
import json
import os

logger = logging.getLogger(__name__)

class Squad:
    """A tactical group of enemies working together."""
    def __init__(self, squad_id: str, squad_type: str, config: dict):
        self.id = squad_id
        self.type = squad_type
        self.name = config.get("name", "Unknown Squad")
        self.playbook_name = config.get("playbook", "default")
        self.formation = config.get("formation", "blob")
        
        self.members: List = [] # List of Enemy entities
        self.blackboard: Dict = {
            "target_pos": None,
            "state": "grouping", # grouping, engaging, retreating
            "squad_center": (0, 0)
        }
        
    def add_member(self, enemy):
        """Register an enemy to this squad."""
        if enemy not in self.members:
            self.members.append(enemy)
            enemy.squad_id = self.id
            logger.info(f"Enemy {enemy.name} joined squad {self.name} ({self.id})")

    def remove_member(self, enemy):
        if enemy in self.members:
            self.members.remove(enemy)
            if not self.members:
                logger.info(f"Squad {self.name} wiped out.")

    def update(self, dt, game_state):
        """Update squad-level logic (blackboard, formation centers)."""
        if not self.members:
            return

        # 1. Update Squad Center
        avg_x = sum(e.x for e in self.members) / len(self.members)
        avg_y = sum(e.y for e in self.members) / len(self.members)
        self.blackboard["squad_center"] = (avg_x, avg_y)

        # 2. Update Target (shared knowledge)
        # If ANY member sees the player, ALL members know where the player is.
        # This overrides individual LOS checks eventually.
        can_see_target = False
        target_pos = None
        
        for e in self.members:
            # Assume enemy has 'target_pos' from its own update logic
            if hasattr(e, 'target_pos') and e.target_pos:
                # Basic check: is target_pos fresh? 
                # For now, just trust the first member who has a target
                target_pos = e.target_pos
                can_see_target = True
                break
        
        if can_see_target:
            self.blackboard["target_pos"] = target_pos

    def get_formation_pos(self, enemy) -> Optional[tuple]:
        """Calculates where a specific unit should be based on formation."""
        if not self.blackboard["target_pos"]:
            return None
            
        center = self.blackboard["squad_center"]
        tx, ty = self.blackboard["target_pos"]
        
        # Vector to target
        dx = tx - center[0]
        dy = ty - center[1]
        dist = math.sqrt(dx*dx + dy*dy)
        if dist == 0: return None
        
        forward_x, forward_y = dx/dist, dy/dist
        right_x, right_y = -forward_y, forward_x
        
        # Sort members by ID for consistent slot assignment
        sorted_members = sorted(self.members, key=lambda e: id(e))
        try:
            rank = sorted_members.index(enemy)
        except ValueError:
            return None

        # Formations
        spacing = 60
        
        if self.formation == "wedge":
            # Leader (0) in front. Others fan out back-left and back-right.
            # 0: center
            # 1: back left
            # 2: back right
            # 3: back far left...
            
            row = int((math.sqrt(1 + 8*rank) - 1) / 2) # Triangle number math roughly
            # Simplified Wedge:
            # Rank 0: (0, 0)
            # Rank 1: (-1, -1) relative
            # Rank 2: (1, -1)
            # Rank 3: (-2, -2)
            
            if rank == 0:
                offset_f = 0
                offset_r = 0
            else:
                side = 1 if rank % 2 == 0 else -1
                depth = (rank + 1) // 2
                offset_f = -depth * spacing
                offset_r = side * depth * spacing * 0.8
                
            fx = center[0] + forward_x * offset_f + right_x * offset_r
            fy = center[1] + forward_y * offset_f + right_y * offset_r
            return (fx, fy)

        elif self.formation == "line":
            # Abreast perpendicular to target
            width = (len(self.members) - 1) * spacing
            start_r = -width / 2
            offset_r = start_r + rank * spacing
            
            fx = center[0] + right_x * offset_r
            fy = center[1] + right_y * offset_r
            return (fx, fy)
            
        return None


class SquadManager:
    """Central manager for all squads."""
    def __init__(self, game_state):
        self.game_state = game_state
        self.squads: Dict[str, Squad] = {}
        self.squad_configs = {}
        self.load_configs()

    def load_configs(self):
        path = os.path.join("data", "squads.json")
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                self.squad_configs = data.get("squads", {})
                logger.info(f"Loaded {len(self.squad_configs)} squad configs.")
        else:
            logger.warning("data/squads.json not found!")

    def create_squad(self, squad_type: str, x: float, y: float) -> Optional[Squad]:
        if squad_type not in self.squad_configs:
            logger.error(f"Unknown squad type: {squad_type}")
            return None
            
        config = self.squad_configs[squad_type]
        squad_id = str(uuid.uuid4())
        new_squad = Squad(squad_id, squad_type, config)
        self.squads[squad_id] = new_squad
        
        logger.info(f"Spawning Squad: {config['name']} at ({x}, {y})")
        
        # Spawn Members
        composition = config.get("composition", {})
        # composition: {"Grunt": 3, "Sniper": 1}
        
        # We need a way to spawn enemies programmatically.
        # Assuming game_state has 'spawn_enemy(type, x, y)'
        
        offset_r = 50
        count = 0
        for enemy_type, qty in composition.items():
            for _ in range(qty):
                # Spread them out slightly so they don't stack
                sx = x + (count % 3) * offset_r
                sy = y + (count // 3) * offset_r
                count += 1
                
                # Spawn
                if hasattr(self.game_state, "spawn_enemy"):
                    enemy = self.game_state.spawn_enemy(enemy_type.lower(), sx, sy)
                    if enemy:
                        new_squad.add_member(enemy)
        
        return new_squad

    def update(self, dt):
        # Update all active squads
        active_ids = list(self.squads.keys())
        for sid in active_ids:
            squad = self.squads[sid]
            # Cull empty squads
            if not squad.members:
                logger.info(f"Squad {squad.name} disbanded (all members dead).")
                del self.squads[sid]
                continue
                
            squad.update(dt, self.game_state)
