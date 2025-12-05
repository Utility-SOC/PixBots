# pixbots/systems/ai_behavior_system.py
# JSON-based AI behavior system with memory, learning, mutation, and graduation

import json
import logging
import random
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from collections import deque
import time
from .behavior_constellation import BehaviorConstellationMatrix

logger = logging.getLogger(__name__)

@dataclass
class BehaviorEntry:
    """Single JSON-encoded behavior."""
    id: str
    enemy_class: str  # grunt, ambush, sniper, boss
    action_type: str  # move_toward, cloak_activate, aim_shot, etc.
    parameters: Dict = field(default_factory=dict)
    success_weight: float = 1.0
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @staticmethod
    def from_dict(data: dict) -> 'BehaviorEntry':
        return BehaviorEntry(**data)

@dataclass
class DamageEvent:
    """Records when player takes damage and which behaviors led to it."""
    timestamp: float
    behavior_sequence: List[str]  # IDs of last X behaviors
    damage_dealt: float
    player_health_before: float
    player_health_after: float
    enemy_id: str
    
    def to_dict(self) -> dict:
        return asdict(self)

class BehaviorMemory:
    """Tracks last X behaviors and their outcomes for an enemy."""
    def __init__(self, memory_size: int = 10):
        self.memory_size = memory_size
        self.recent_behaviors: deque = deque(maxlen=memory_size)
        self.damage_events: List[DamageEvent] = []
    
    def record_behavior(self, behavior_id: str):
        """Add behavior to memory."""
        self.recent_behaviors.append(behavior_id)
    
    def record_damage(self, damage_amount: float, player_health_before: float, 
                     player_health_after: float, enemy_id: str):
        """Record successful damage event with recent behaviors."""
        event = DamageEvent(
            timestamp=time.time(),
            behavior_sequence=list(self.recent_behaviors),
            damage_dealt=damage_amount,
            player_health_before=player_health_before,
            player_health_after=player_health_after,
            enemy_id=enemy_id
        )
        self.damage_events.append(event)
        return event
    
    def get_recent_behaviors(self) -> List[str]:
        """Get list of recent behavior IDs."""
        return list(self.recent_behaviors)

class BehaviorMutator:
    """Boss-only: Combines and mutates successful behaviors."""
    def __init__(self):
        self.mutations: Dict[str, BehaviorEntry] = {}
        self.mutation_counter = 0
    
    def mutate_behavior(self, parent1: BehaviorEntry, parent2: BehaviorEntry) -> BehaviorEntry:
        """Combine two behaviors into a new mutation."""
        self.mutation_counter += 1
        mutation_id = f"mutation_{self.mutation_counter}_{parent1.id}_{parent2.id}"
        
        # Combine parameters from both parents
        combined_params = {**parent1.parameters, **parent2.parameters}
        
        # Amplify some parameters
        for key in combined_params:
            if isinstance(combined_params[key], (int, float)):
                combined_params[key] *= random.uniform(1.1, 1.3)
        
        mutation = BehaviorEntry(
            id=mutation_id,
            enemy_class="boss",
            action_type=f"{parent1.action_type}+{parent2.action_type}",
            parameters=combined_params,
            success_weight=max(parent1.success_weight, parent2.success_weight) * 1.2
        )
        
        self.mutations[mutation_id] = mutation
        logger.info(f"Created mutation: {mutation_id} from {parent1.id} + {parent2.id}")
        return mutation
    
    def amplify_behavior(self, behavior: BehaviorEntry, factor: float = 1.5) -> BehaviorEntry:
        """Amplify parameters of a successful behavior."""
        self.mutation_counter += 1
        amplified_id = f"amplified_{self.mutation_counter}_{behavior.id}"
        
        amplified_params = behavior.parameters.copy()
        for key in amplified_params:
            if isinstance(amplified_params[key], (int, float)):
                amplified_params[key] *= factor
        
        amplified = BehaviorEntry(
            id=amplified_id,
            enemy_class=behavior.enemy_class,
            action_type=f"amplified_{behavior.action_type}",
            parameters=amplified_params,
            success_weight=behavior.success_weight * 1.3
        )
        
        self.mutations[amplified_id] = amplified
        return amplified

class DamageCorrelator:
    """Analyzes damage events to identify successful behaviors."""
    def __init__(self):
        self.behavior_success_rates: Dict[str, float] = {}
        self.behavior_damage_totals: Dict[str, float] = {}
        self.behavior_usage_counts: Dict[str, int] = {}
    
    def analyze_damage_events(self, damage_events: List[DamageEvent]) -> Dict[str, float]:
        """Analyze recent damage events and return updated weights."""
        updated_weights = {}
        
        for event in damage_events:
            # Each behavior in sequence gets credit for the damage
            credit_per_behavior = event.damage_dealt / len(event.behavior_sequence) if event.behavior_sequence else 0
            
            for behavior_id in event.behavior_sequence:
                # Update totals
                self.behavior_damage_totals[behavior_id] = \
                    self.behavior_damage_totals.get(behavior_id, 0) + credit_per_behavior
                self.behavior_usage_counts[behavior_id] = \
                    self.behavior_usage_counts.get(behavior_id, 0) + 1
                
                # Calculate success rate (average damage per use)
                avg_damage = self.behavior_damage_totals[behavior_id] / \
                            self.behavior_usage_counts[behavior_id]
                
                # Convert to weight (normalize around 1.0, with bonus for high damage)
                weight = 1.0 + (avg_damage / 10.0)
                updated_weights[behavior_id] = weight
        
        return updated_weights

class BehaviorSystem:
    """Core AI behavior manager with learning, mutation, and graduation."""
    def __init__(self, data_dir: str = "data/behaviors"):
        self.data_dir = data_dir
        self.behaviors: Dict[str, List[BehaviorEntry]] = {
            "grunt": [],
            "ambush": [],
            "sniper": [],
            "boss": []
        }
        self.enemy_memories: Dict[str, BehaviorMemory] = {}
        self.correlator = DamageCorrelator()
        self.mutator = BehaviorMutator()
        
        # Memory sizes per class
        self.memory_sizes = {
            "grunt": 10,
            "ambush": 15,
            "sniper": 15,
            "boss": 50
        }
        
        # Graduation thresholds - when mutations become permanent
        self.graduation_thresholds = {
            "min_uses": 5,          # Must be used at least 5 times
            "min_weight": 1.5,      # Must have 1.5x success rate
            "min_damage": 30.0      # Must have dealt 30+ total damage
        }
        
        # Track base vs graduated behaviors
        self.base_behavior_ids: Dict[str, set] = {
            "grunt": set(),
            "ambush": set(),
            "sniper": set(),
            "boss": set()
        }
        
        self.load_behaviors()
        
        # Initialize constellation matrix with all loaded behavior IDs
        all_behavior_ids = [b.id for behaviors in self.behaviors.values() for b in behaviors]
        self.constellation_matrix = BehaviorConstellationMatrix(all_behavior_ids)
    
    def load_behaviors(self):
        """Load behavior definitions from JSON."""
        behavior_files = {
            "grunt": f"{self.data_dir}/grunt_behaviors.json",
            "ambush": f"{self.data_dir}/ambush_behaviors.json",
            "sniper": f"{self.data_dir}/sniper_behaviors.json",
            "boss": f"{self.data_dir}/boss_base_behaviors.json"
        }
        
        for enemy_class, filepath in behavior_files.items():
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        for behavior_data in data.get("behaviors", []):
                            behavior = BehaviorEntry.from_dict(behavior_data)
                            self.behaviors[enemy_class].append(behavior)
                            # Track base behaviors from JSON
                            self.base_behavior_ids[enemy_class].add(behavior.id)
                    logger.info(f"Loaded {len(self.behaviors[enemy_class])} base behaviors for {enemy_class}")
                except Exception as e:
                    logger.error(f"Failed to load behaviors from {filepath}: {e}")
            else:
                logger.warning(f"Behavior file not found: {filepath}")
    
    def get_or_create_memory(self, enemy_id: str, enemy_class: str) -> BehaviorMemory:
        """Get or create memory for an enemy."""
        if enemy_id not in self.enemy_memories:
            memory_size = self.memory_sizes.get(enemy_class, 10)
            self.enemy_memories[enemy_id] = BehaviorMemory(memory_size)
        return self.enemy_memories[enemy_id]
    
    def record_behavior(self, enemy_id: str, enemy_class: str, behavior_id: str):
        """Record that an enemy executed a behavior."""
        memory = self.get_or_create_memory(enemy_id, enemy_class)
        memory.record_behavior(behavior_id)
    
    def track_player_damage(self, damage_amount: float, player_health_before: float,
                           player_health_after: float, enemy_id: str, enemy_class: str):
        """Track damage dealt to player and correlate with behaviors."""
        memory = self.get_or_create_memory(enemy_id, enemy_class)
        damage_event = memory.record_damage(
            damage_amount, player_health_before, player_health_after, enemy_id
        )
        
        # Record sequence in constellation matrix
        behavior_sequence = memory.get_recent_behaviors()
        if len(behavior_sequence) >= 2:
            self.constellation_matrix.record_sequence(behavior_sequence, damage_amount)
        
        # Analyze and update weights
        updated_weights = self.correlator.analyze_damage_events([damage_event])
        
        # Update behavior weights
        for behavior_list in self.behaviors.values():
            for behavior in behavior_list:
                if behavior.id in updated_weights:
                    behavior.success_weight = updated_weights[behavior.id]
        
        logger.debug(f"Updated weights after damage: {updated_weights}")
        
        # Check for graduation candidates
        self.evaluate_for_graduation(enemy_class)
        
        # Boss mutation chance
        if enemy_class == "boss" and random.random() < 0.1:  # 10% chance
            self.trigger_boss_mutation(enemy_id, memory)
    
    def get_weighted_behavior(self, enemy_class: str) -> Optional[BehaviorEntry]:
        """Get a behavior weighted by success probability."""
        available_behaviors = self.behaviors.get(enemy_class, [])
        if not available_behaviors:
            return None
        
        # Weight selection
        weights = [b.success_weight for b in available_behaviors]
        total_weight = sum(weights)
        
        if total_weight == 0:
            return random.choice(available_behaviors)
        
        # Weighted random choice
        rand = random.uniform(0, total_weight)
        cumulative = 0
        for behavior, weight in zip(available_behaviors, weights):
            cumulative += weight
            if rand <= cumulative:
                return behavior
        
        return available_behaviors[-1]
    
    def trigger_boss_mutation(self, boss_id: str, memory: BehaviorMemory):
        """Boss tries to mutate/combine successful behaviors."""
        boss_behaviors = self.behaviors.get("boss", [])
        if len(boss_behaviors) < 2:
            return
        
        # Find two highly weighted behaviors
        sorted_behaviors = sorted(boss_behaviors, key=lambda b: b.success_weight, reverse=True)
        parent1 = sorted_behaviors[0]
        parent2 = sorted_behaviors[1]
        
        # Mutate
        mutation = self.mutator.mutate_behavior(parent1, parent2)
        self.behaviors["boss"].append(mutation)
        
        # Add to constellation matrix
        self.constellation_matrix.add_behavior_id(mutation.id)
        
        logger.info(f"Boss {boss_id} created mutation: {mutation.id}")
        
        # If mutation becomes highly successful, spread to other enemy classes
        if mutation.success_weight > 2.0:
            target_class = parent1.enemy_class if parent1.enemy_class != "boss" else "grunt"
            self.spread_behavior_to_class(mutation, target_class)
    
    def evaluate_for_graduation(self, enemy_class: str):
        """Check if any mutations should graduate to permanent behaviors."""
        behaviors = self.behaviors.get(enemy_class, [])
        base_ids = self.base_behavior_ids.get(enemy_class, set())
        
        for behavior in behaviors:
            # Skip behaviors already in base set
            if behavior.id in base_ids:
                continue
            
            # Check if mutation meets graduation criteria
            usage_count = self.correlator.behavior_usage_counts.get(behavior.id, 0)
            total_damage = self.correlator.behavior_damage_totals.get(behavior.id, 0.0)
            success_weight = behavior.success_weight
            
            if (usage_count >= self.graduation_thresholds["min_uses"] and
                success_weight >= self.graduation_thresholds["min_weight"] and
                total_damage >= self.graduation_thresholds["min_damage"]):
                
                # Graduate this behavior!
                self.graduate_behavior(behavior, enemy_class)
    
    def graduate_behavior(self, behavior: BehaviorEntry, enemy_class: str):
        """Promote a successful mutation to the permanent repertoire."""
        # Add to base behavior set
        self.base_behavior_ids[enemy_class].add(behavior.id)
        
        # Add to constellation matrix
        self.constellation_matrix.add_behavior_id(behavior.id)
        
        logger.info(
            f"🎓 GRADUATED: {behavior.id} for {enemy_class}! "
            f"(weight: {behavior.success_weight:.2f}, "
            f"uses: {self.correlator.behavior_usage_counts.get(behavior.id, 0)}, "
            f"damage: {self.correlator.behavior_damage_totals.get(behavior.id, 0):.1f})"
        )
        
        # Save to JSON for persistence
        self.save_graduated_behavior(behavior, enemy_class)
    
    def save_graduated_behavior(self, behavior: BehaviorEntry, enemy_class: str):
        """Save graduated behavior to JSON file for persistence."""
        graduated_dir = f"{self.data_dir}/graduated"
        os.makedirs(graduated_dir, exist_ok=True)
        
        filepath = f"{graduated_dir}/{enemy_class}_graduated.json"
        
        # Load existing graduated behaviors
        graduated_behaviors = []
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    graduated_behaviors = data.get("behaviors", [])
            except Exception as e:
                logger.error(f"Failed to load graduated behaviors: {e}")
        
        # Add new behavior
        graduated_behaviors.append(behavior.to_dict())
        
        # Save back
        try:
            with open(filepath, 'w') as f:
                json.dump({"behaviors": graduated_behaviors}, f, indent=2)
            logger.info(f"Saved graduated behavior to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save graduated behavior: {e}")
    
    def spread_behavior_to_class(self, behavior: BehaviorEntry, target_class: str):
        """Spread a successful behavior to another enemy class."""
        if target_class not in self.behaviors:
            return
        
        # Check if already exists
        existing_ids = {b.id for b in self.behaviors[target_class]}
        if behavior.id in existing_ids:
            return
        
        # Create adapted version for target class
        adapted_behavior = BehaviorEntry(
            id=f"{target_class}_{behavior.id}",
            enemy_class=target_class,
            action_type=behavior.action_type,
            parameters=behavior.parameters.copy(),
            success_weight=behavior.success_weight * 0.8  # Slightly reduced for new class
        )
        
        self.behaviors[target_class].append(adapted_behavior)
        self.constellation_matrix.add_behavior_id(adapted_behavior.id)
        
        logger.info(f"📡 SPREAD: {behavior.id} → {target_class} as {adapted_behavior.id}")
    
    def get_stats(self) -> Dict:
        """Get current system stats for debugging."""
        return {
            "total_behaviors": sum(len(b) for b in self.behaviors.values()),
            "behavior_counts": {k: len(v) for k, v in self.behaviors.items()},
            "graduated_counts": {k: len(self.behaviors[k]) - len(self.base_behavior_ids[k]) 
                                for k in self.behaviors.keys()},
            "active_memories": len(self.enemy_memories),
            "mutations_created": self.mutator.mutation_counter,
            "top_behaviors": sorted(
                [(b.id, b.success_weight) for behaviors in self.behaviors.values() for b in behaviors],
                key=lambda x: x[1], reverse=True
            )[:5],
            "constellation_stats": self.constellation_matrix.get_matrix_stats()
        }
