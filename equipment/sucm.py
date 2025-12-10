from enum import Enum

class SUCMState(Enum):
    CHARGED = "CHARGED"
    DISCHARGED = "DISCHARGED"

class SUCM:
    def __init__(self, recharge_threshold: float = 100.0):
        self.state = SUCMState.DISCHARGED
        self.recharge_threshold = recharge_threshold
        self.current_recharge = 0.0
        
    def add_energy(self, amount: float):
        if self.state == SUCMState.CHARGED:
            return False # Not used
            
        self.current_recharge += amount
        if self.current_recharge >= self.recharge_threshold:
            self.state = SUCMState.CHARGED
            self.current_recharge = self.recharge_threshold
        
        return True
    
    def discharge(self):
        self.state = SUCMState.DISCHARGED
        self.current_recharge = 0.0

    def calculate_consumption(self, total_available_energy: float) -> float:
        """
        Consumes 0.1% of total available energy as a localized energy sink when charging?
        Spec says: "In calculate_output, it provides 0 energy when DISCHARGED and consumes 0.1% of total available energy as a localized energy sink."
        Wait, if it's DISCHARGED it generates 0, but consumes?
        Yes, "The module is powerful but comes with a continuous, though small, background cost when disabled."
        So when DISCHARGED (disabled/charging), it consumes.
        When CHARGED (enabled/ready), does it consume? Spec doesn't say explicitly but implies trade-off when disabled (charging).
        Let's assume it consumes when DISCHARGED.
        """
        if self.state == SUCMState.DISCHARGED:
             return total_available_energy * 0.001
        return 0.0
