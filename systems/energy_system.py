from typing import Tuple, TYPE_CHECKING
if TYPE_CHECKING:
    from entities.player import Player

class EnergySystem:
    # Baseline for normalization (1000.0 corresponds to a Legendary Core's potential flow)
    MAX_GAME_FLOW = 1000.0 

    @staticmethod
    def calculate_total_output(player: 'Player') -> Tuple[float, float]:
        """
        Calculates the total energy generation (Input) and potential consumption (Output).
        Returns: (InputRate, OutputRate)
        """
        input_rate = 0.0
        output_rate = 0.0
        
        # 1. Torso Input (Generation)
        torso = player.components.get("torso")
        if torso and torso.core:
             input_rate = torso.core.generation_rate
        
        # 2. Component Consumption
        # We simulate the flow through components assuming full connectivity to measure potential output.
        if torso:
             _, _, torso_exits = torso.simulate_flow()
             
             for slot, comp in player.components.items():
                 if not comp or slot == "torso": continue
                 
                 input_context = None
                 input_dir = 0
                 
                 # Map Torso Exits to Components (Simplified Model)
                 if slot == "right_arm":
                     input_context = torso_exits.get(0)
                     input_dir = 3
                 elif slot == "left_arm":
                     input_context = torso_exits.get(3)
                     input_dir = 0
                 elif slot == "head":
                     input_context = torso_exits.get(1)
                     input_dir = 4 # Enters from Bottom? Or Top? If Head is above torso, energy comes from Bottom (4/5)
                     # Standard: 0=E, 1=NE, 2=NW, 3=W, 4=SW, 5=SE
                     # Torso(1/NE) -> Head. Head Entry?
                     # If Head is NE of Torso, Entry on Head is SW (4).
                     input_dir = 4 
                 elif slot == "back":
                     input_context = torso_exits.get(2) # NW
                     input_dir = 5 # Entry from SE (5)
                 elif "leg" in slot:
                     if "right" in slot:
                          input_context = torso_exits.get(5)
                          input_dir = 2
                     else:
                          input_context = torso_exits.get(4)
                          input_dir = 1
                
                 # Fallback: If no explicit connection, allow trickle charge from Core (Wireless/Internal Routing)
                 if not input_context and torso.core:
                     # Create a default context from the Core's dominant type
                     # Penalty: 50% efficiency for wireless transfer
                     from hex_system.energy_packet import ProjectileContext, SynergyType
                     base_mag = torso.core.generation_rate * 0.5
                     input_context = ProjectileContext(synergies={torso.core.core_type: base_mag})
                 
                 if input_context:
                     _, stats, _ = comp.simulate_flow(input_context, input_dir)
                     output_rate += stats.get("weapon_damage", 0.0)
        
        # 3. SUCM Consumption
        if hasattr(player, "sucm"):
            output_rate += player.sucm.calculate_consumption(input_rate)
            
        return input_rate, output_rate

    @staticmethod
    def calculate_flow(magnitude: float) -> float:
        """
        Calculates the normalized flow magnitude (0-1000) for visualization.
        """
        # H5: Flow Rate / Max Flow Capacity * 1000
        # We clamp at 1000 to keep UI consistent
        return min(1000.0, (magnitude / EnergySystem.MAX_GAME_FLOW) * 1000.0)
