import unittest
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from hex_system.hex_tile import OrbitalModulatorTile, DetonationTriggerTile, SecondaryOutputTile, TargetSystem, TriggerMode
from equipment.sucm import SUCM, SUCMState
from systems.energy_system import EnergySystem

class TestHexPhase1(unittest.TestCase):
    def test_orbital_modulator(self):
        tile = OrbitalModulatorTile()
        self.assertEqual(tile.tile_type, "Orbital Modulator")
        self.assertEqual(tile.orbit_radius, 0.5)
        
        tile.orbit_radius = 0.8
        d = tile.to_dict()
        self.assertEqual(d["orbit_radius"], 0.8)
        
        tile2 = OrbitalModulatorTile()
        tile2.restore_from_dict(d)
        self.assertEqual(tile2.orbit_radius, 0.8)

    def test_detonation_trigger(self):
        tile = DetonationTriggerTile()
        self.assertEqual(tile.tile_type, "Detonation Trigger")
        self.assertEqual(tile.trigger_time, 1.0)
        
        tile.trigger_time = 0.5
        d = tile.to_dict()
        self.assertEqual(d["trigger_time"], 0.5)
        
        tile2 = DetonationTriggerTile()
        tile2.restore_from_dict(d)
        self.assertEqual(tile2.trigger_time, 0.5)

    def test_secondary_output(self):
        tile = SecondaryOutputTile()
        self.assertEqual(tile.target_system, TargetSystem.SHIELD)
        
        tile.target_system = TargetSystem.SUCM
        tile.trigger_mode = TriggerMode.TOGGLE
        d = tile.to_dict()
        self.assertEqual(d["target_system"], "SUCM")
        self.assertEqual(d["trigger_mode"], "TOGGLE")
        
        tile2 = SecondaryOutputTile()
        tile2.restore_from_dict(d)
        self.assertEqual(tile2.target_system, TargetSystem.SUCM)
        self.assertEqual(tile2.trigger_mode, TriggerMode.TOGGLE)

    def test_sucm(self):
        sucm = SUCM(recharge_threshold=100.0)
        self.assertEqual(sucm.state, SUCMState.DISCHARGED)
        
        sucm.add_energy(50)
        self.assertEqual(sucm.current_recharge, 50)
        self.assertEqual(sucm.state, SUCMState.DISCHARGED)
        
        sucm.add_energy(60) # Overcharge
        self.assertEqual(sucm.current_recharge, 100.0)
        self.assertEqual(sucm.state, SUCMState.CHARGED)
        
        sucm.discharge()
        self.assertEqual(sucm.state, SUCMState.DISCHARGED)
        self.assertEqual(sucm.current_recharge, 0.0)

    def test_energy_system_flow(self):
        # Magnitude 1000 -> 1000 normalized
        norm = EnergySystem.calculate_flow(1000.0)
        self.assertEqual(norm, 1000.0)
        
        # Magnitude 10 -> 10 normalized
        norm = EnergySystem.calculate_flow(10.0)
        self.assertEqual(norm, 10.0)
        
        # Magnitude 2000 -> 1000 (clamped)
        norm = EnergySystem.calculate_flow(2000.0)
        self.assertEqual(norm, 1000.0)

if __name__ == '__main__':
    unittest.main()
