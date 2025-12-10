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
                self.base_synergy_effects = self.synergies_data.get("base_synergy_effects", {})
        except FileNotFoundError:
            print(f"Error: Synergies data file not found at {data_path}")
            # Fallback defaults
            self.base_synergies = ["raw", "fire", "ice", "lightning", "kinetic"]
            self.combinations = []
            self.base_synergy_effects = {}

    def calculate_synergy(self, packet: ProjectileContext) -> SynergyResult:
        """
        Determines the active synergies based on the packet's composition.
        Returns a SynergyResult containing ALL active synergies and their magnitudes.
        """
        if not packet.synergies:
            return SynergyResult(name="raw", effects={})

        # Get all synergies present with significant magnitude (> 5% of total)
        total_mag = packet.get_total_magnitude()
        if total_mag <= 0:
            return SynergyResult(name="raw", effects={})

        active_effects = {}
        active_synergies_list = []
        
        for syn_type, mag in packet.synergies.items():
            # Allow if significant ratio OR significant absolute value
            # User wants 100 vampirism to count even if 1000 vortex is present.
            if mag > 1.0: # Absolute threshold (1.0 is very low, ensuring almost anything registers)
                # Convert Enum to string if necessary, or use value
                syn_name = syn_type.value if isinstance(syn_type, SynergyType) else str(syn_type)
                active_synergies_list.append(syn_name)
                
                # Get base effects for this synergy
                base_effects = self.base_synergy_effects.get(syn_name, {})
                
                # Merge effects (this is a simple merge, might need more complex logic later)
                for k, v in base_effects.items():
                    active_effects[k] = v
                
                # Dynamic Power Injection: Ensure combat system knows the magnitude
                active_effects[f"{syn_name}_power"] = mag
                    
        # If no specific synergy is dominant enough, default to raw
        if not active_synergies_list:
            return SynergyResult(name="raw", effects={})
            
        # The "name" is now a composite or just the primary one for display?
        # Let's use the dominant one for the "name" field but pass all in effects
        dominant_enum = packet.get_dominant_synergy()
        dominant_name = dominant_enum.value if isinstance(dominant_enum, SynergyType) else str(dominant_enum)
        
        # Store all active synergies in the effects dict for the Projectile to use
        active_effects["active_synergies"] = active_synergies_list
        
        return SynergyResult(name=dominant_name, effects=active_effects)

    def get_synergy_effects(self, synergy_name: str) -> Dict[str, Any]:
        """Returns the effects for a named synergy."""
        return self.base_synergy_effects.get(synergy_name, {})
