import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from hex_system.energy_packet import ProjectileContext, SynergyType

@dataclass
class SynergyResult:
    name: str
    effects: Dict[str, Any]
    is_combination: bool = False

class SynergyManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SynergyManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.synergies_data = {}
        self.base_synergies = []
        self.combinations = []
        self.load_data()
        self._initialized = True

    def load_data(self):
        # Assuming the data file is in the standard location relative to the project root
        # Adjust path as necessary based on where this is run from
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_path = os.path.join(base_path, "data", "synergies.json")
        
        try:
            with open(data_path, 'r') as f:
                self.synergies_data = json.load(f)
                self.base_synergies = self.synergies_data.get("base_synergies", [])
                self.combinations = self.synergies_data.get("combinations", [])
        except FileNotFoundError:
            print(f"Error: Synergies data file not found at {data_path}")
            # Fallback defaults
            self.base_synergies = ["raw", "fire", "ice", "lightning", "kinetic"]
            self.combinations = []

    def calculate_synergy(self, packet: ProjectileContext) -> SynergyResult:
        """
        Determines the active synergy based on the packet's composition.
        Checks for combinations first, then falls back to the dominant base synergy.
        """
        if not packet.synergies:
            return SynergyResult(name="raw", effects={})

        # Get all synergies present with significant magnitude (> 10% of total)
        total_mag = packet.get_total_magnitude()
        if total_mag <= 0:
            return SynergyResult(name="raw", effects={})

        active_types = []
        for syn_type, mag in packet.synergies.items():
            if mag / total_mag > 0.1: # Threshold to consider a synergy active
                # Convert Enum to string if necessary, or use value
                syn_name = syn_type.value if isinstance(syn_type, SynergyType) else str(syn_type)
                active_types.append(syn_name)

        # Check for combinations
        # We look for a combination where all inputs are present in the active types
        for combo in self.combinations:
            inputs = combo.get("inputs", [])
            if all(inp in active_types for inp in inputs):
                # Found a match!
                return SynergyResult(
                    name=combo["result"],
                    effects=combo.get("effects", {}),
                    is_combination=True
                )

        # No combination found, return dominant base synergy
        dominant_enum = packet.get_dominant_synergy()
        dominant_name = dominant_enum.value if isinstance(dominant_enum, SynergyType) else str(dominant_enum)
        
        return SynergyResult(name=dominant_name, effects={})

    def get_synergy_effects(self, synergy_name: str) -> Dict[str, Any]:
        """Returns the effects for a named synergy (if it's a combination)."""
        for combo in self.combinations:
            if combo["result"] == synergy_name:
                return combo.get("effects", {})
        return {}
