# pixbots/systems/behavior_constellation.py
# Matrix-based behavior pattern recognition for AI learning

import numpy as np
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict
import json
import logging

logger = logging.getLogger(__name__)

class BehaviorConstellationMatrix:
    """
    Tracks behavior patterns using matrices for efficient pattern recognition.
    
    Features:
    - Co-occurrence matrix: Which behaviors appear together in successful sequences
    - Transition matrix: Which behavior typically follows another
    - Success correlation: Which combinations lead to player damage
    """
    
    def __init__(self, behavior_ids: List[str]):
        """Initialize matrices for given behavior IDs."""
        self.behavior_ids = behavior_ids
        self.behavior_to_idx = {bid: idx for idx, bid in enumerate(behavior_ids)}
        self.idx_to_behavior = {idx: bid for bid, idx in self.behavior_to_idx.items()}
        self.n = len(behavior_ids)
        
        # Co-occurrence matrix: counts how often behaviors appear together in successful sequences
        # Shape: (n_behaviors, n_behaviors)
        # cooccurrence[i][j] = count of times behavior_i and behavior_j appeared in same damage sequence
        self.cooccurrence = np.zeros((self.n, self.n), dtype=np.float32)
        
        # Transition matrix: probability of behavior_j following behavior_i
        # Shape: (n_behaviors, n_behaviors)
        # transition[i][j] = P(behavior_j | behavior_i)
        self.transition = np.zeros((self.n, self.n), dtype=np.float32)
        self.transition_counts = np.zeros((self.n, self.n), dtype=np.int32)
        
        # Success weight matrix: average damage when behavior_i precedes behavior_j
        # Shape: (n_behaviors, n_behaviors)
        self.success_weights = np.zeros((self.n, self.n), dtype=np.float32)
        self.success_counts = np.zeros((self.n, self.n), dtype=np.int32)
        
        # Constellation clusters: identified patterns (sets of behaviors)
        self.constellations: Dict[str, Set[str]] = {}
        self.constellation_success_rates: Dict[str, float] = {}
    
    def add_behavior_id(self, behavior_id: str):
        """Dynamically add a new behavior (e.g., boss mutation) to the matrix."""
        if behavior_id in self.behavior_to_idx:
            return
        
        idx = self.n
        self.behavior_ids.append(behavior_id)
        self.behavior_to_idx[behavior_id] = idx
        self.idx_to_behavior[idx] = behavior_id
        self.n += 1
        
        # Expand matrices
        self.cooccurrence = np.pad(self.cooccurrence, ((0, 1), (0, 1)), constant_values=0)
        self.transition = np.pad(self.transition, ((0, 1), (0, 1)), constant_values=0)
        self.transition_counts = np.pad(self.transition_counts, ((0, 1), (0, 1)), constant_values=0)
        self.success_weights = np.pad(self.success_weights, ((0, 1), (0, 1)), constant_values=0)
        self.success_counts = np.pad(self.success_counts, ((0, 1), (0, 1)), constant_values=0)
    
    def record_sequence(self, behavior_sequence: List[str], damage_dealt: float):
        """
        Record a sequence of behaviors that led to damage.
        Updates all matrices based on the sequence.
        """
        if len(behavior_sequence) < 2:
            return
        
        indices = [self.behavior_to_idx.get(bid) for bid in behavior_sequence if bid in self.behavior_to_idx]
        if len(indices) < 2:
            return
        
        # Update co-occurrence matrix (all pairs in sequence)
        for i in range(len(indices)):
            for j in range(i + 1, len(indices)):
                idx_i, idx_j = indices[i], indices[j]
                self.cooccurrence[idx_i][idx_j] += 1
                self.cooccurrence[idx_j][idx_i] += 1  # Symmetric
        
        # Update transition matrix (sequential pairs)
        for i in range(len(indices) - 1):
            idx_current = indices[i]
            idx_next = indices[i + 1]
            self.transition_counts[idx_current][idx_next] += 1
            
            # Update success weights (damage credit for this transition)
            self.success_weights[idx_current][idx_next] += damage_dealt
            self.success_counts[idx_current][idx_next] += 1
        
        # Recompute transition probabilities
        self._update_transition_probabilities()
    
    def _update_transition_probabilities(self):
        """Convert transition counts to probabilities."""
        for i in range(self.n):
            row_sum = self.transition_counts[i].sum()
            if row_sum > 0:
                self.transition[i] = self.transition_counts[i] / row_sum
    
    def get_best_next_behavior(self, current_behavior: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Given current behavior, return top K most successful next behaviors.
        Returns list of (behavior_id, expected_damage) tuples.
        """
        if current_behavior not in self.behavior_to_idx:
            return []
        
        idx = self.behavior_to_idx[current_behavior]
        
        # Calculate expected damage for each next behavior
        expected_damages = []
        for j in range(self.n):
            if self.success_counts[idx][j] > 0:
                avg_damage = self.success_weights[idx][j] / self.success_counts[idx][j]
                transition_prob = self.transition[idx][j]
                expected_damage = avg_damage * transition_prob
                expected_damages.append((self.idx_to_behavior[j], expected_damage))
        
        # Sort by expected damage and return top K
        expected_damages.sort(key=lambda x: x[1], reverse=True)
        return expected_damages[:top_k]
    
    def identify_constellations(self, min_cooccurrence: int = 3, min_success_weight: float = 20.0):
        """
        Identify behavior constellations (clusters of behaviors that work well together).
        Uses clustering based on co-occurrence and success weights.
        """
        self.constellations.clear()
        self.constellation_success_rates.clear()
        
        # Find strongly connected behavior pairs
        strong_pairs = []
        for i in range(self.n):
            for j in range(i + 1, self.n):
                if self.cooccurrence[i][j] >= min_cooccurrence:
                    # Calculate average success when these behaviors co-occur
                    total_success = (self.success_weights[i][j] + self.success_weights[j][i])
                    total_count = max(1, self.success_counts[i][j] + self.success_counts[j][i])
                    avg_success = total_success / total_count
                    
                    if avg_success >= min_success_weight:
                        strong_pairs.append((i, j, avg_success))
        
        # Group pairs into constellations using simple clustering
        used_behaviors = set()
        constellation_id = 0
        
        for i, j, success in sorted(strong_pairs, key=lambda x: x[2], reverse=True):
            if i in used_behaviors or j in used_behaviors:
                continue
            
            # Start new constellation
            constellation_name = f"constellation_{constellation_id}"
            constellation_behaviors = {self.idx_to_behavior[i], self.idx_to_behavior[j]}
            
            # Try to expand constellation with nearby behaviors
            for k in range(self.n):
                if k in [i, j] or k in used_behaviors:
                    continue
                
                # Check if k co-occurs strongly with both i and j
                co_i = self.cooccurrence[i][k]
                co_j = self.cooccurrence[j][k]
                if co_i >= min_cooccurrence / 2 and co_j >= min_cooccurrence / 2:
                    constellation_behaviors.add(self.idx_to_behavior[k])
            
            self.constellations[constellation_name] = constellation_behaviors
            self.constellation_success_rates[constellation_name] = success
            
            used_behaviors.update([i, j])
            constellation_id += 1
        
        logger.info(f"Identified {len(self.constellations)} behavior constellations")
        return self.constellations
    
    def get_constellation_recommendation(self, current_behaviors: List[str]) -> Optional[Tuple[str, Set[str], float]]:
        """
        Given current behavior sequence, recommend which constellation to activate.
        Returns (constellation_name, missing_behaviors, success_rate) or None.
        """
        current_set = set(current_behaviors)
        
        best_match = None
        best_score = 0
        
        for const_name, const_behaviors in self.constellations.items():
            # Calculate overlap
            overlap = len(current_set & const_behaviors)
            missing = const_behaviors - current_set
            
            if overlap > 0 and len(missing) > 0:
                # Score based on overlap and success rate
                success_rate = self.constellation_success_rates[const_name]
                score = overlap * success_rate / len(const_behaviors)
                
                if score > best_score:
                    best_score = score
                    best_match = (const_name, missing, success_rate)
        
        return best_match
    
    def get_matrix_stats(self) -> Dict:
        """Get statistics about the matrices for debugging."""
        return {
            "n_behaviors": self.n,
            "total_cooccurrences": int(self.cooccurrence.sum() / 2),  # Divide by 2 since symmetric
            "total_transitions": int(self.transition_counts.sum()),
            "n_constellations": len(self.constellations),
            "avg_constellation_size": np.mean([len(c) for c in self.constellations.values()]) if self.constellations else 0,
            "most_common_transitions": self._get_top_transitions(5),
            "strongest_cooccurrences": self._get_top_cooccurrences(5)
        }
    
    def _get_top_transitions(self, n: int) -> List[Tuple[str, str, float]]:
        """Get top N most common behavior transitions."""
        transitions = []
        for i in range(self.n):
            for j in range(self.n):
                if self.transition_counts[i][j] > 0:
                    transitions.append((
                        self.idx_to_behavior[i],
                        self.idx_to_behavior[j],
                        float(self.transition[i][j])
                    ))
        transitions.sort(key=lambda x: x[2], reverse=True)
        return transitions[:n]
    
    def _get_top_cooccurrences(self, n: int) -> List[Tuple[str, str, float]]:
        """Get top N most common behavior co-occurrences."""
        cooccurrences = []
        for i in range(self.n):
            for j in range(i + 1, self.n):
                if self.cooccurrence[i][j] > 0:
                    cooccurrences.append((
                        self.idx_to_behavior[i],
                        self.idx_to_behavior[j],
                        float(self.cooccurrence[i][j])
                    ))
        cooccurrences.sort(key=lambda x: x[2], reverse=True)
        return cooccurrences[:n]
    
    def save_to_file(self, filepath: str):
        """Save matrices to file for persistence."""
        data = {
            "behavior_ids": self.behavior_ids,
            "cooccurrence": self.cooccurrence.tolist(),
            "transition_counts": self.transition_counts.tolist(),
            "success_weights": self.success_weights.tolist(),
            "success_counts": self.success_counts.tolist(),
            "constellations": {k: list(v) for k, v in self.constellations.items()},
            "constellation_success_rates": self.constellation_success_rates
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved constellation matrix to {filepath}")
    
    def load_from_file(self, filepath: str):
        """Load matrices from file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.behavior_ids = data["behavior_ids"]
        self.behavior_to_idx = {bid: idx for idx, bid in enumerate(self.behavior_ids)}
        self.idx_to_behavior = {idx: bid for bid, idx in self.behavior_to_idx.items()}
        self.n = len(self.behavior_ids)
        
        self.cooccurrence = np.array(data["cooccurrence"], dtype=np.float32)
        self.transition_counts = np.array(data["transition_counts"], dtype=np.int32)
        self.success_weights = np.array(data["success_weights"], dtype=np.float32)
        self.success_counts = np.array(data["success_counts"], dtype=np.int32)
        
        self._update_transition_probabilities()
        
        self.constellations = {k: set(v) for k, v in data["constellations"].items()}
        self.constellation_success_rates = data["constellation_success_rates"]
        
        logger.info(f"Loaded constellation matrix from {filepath}")
