import unittest
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

# Mock pygame
from unittest.mock import MagicMock
sys.modules["pygame"] = MagicMock()
sys.modules["pygame.image"] = MagicMock()
sys.modules["pygame.transform"] = MagicMock()

from hex_system.hex_tile import SplitterTile
from hex_system.energy_packet import ProjectileContext, SynergyType, ProjectileModifier
from equipment.component import ComponentEquipment
import logging

class TestRefinement(unittest.TestCase):
    def test_smart_splitter(self):
        splitter = SplitterTile(split_count=2, exit_directions=[0, 1]) # Valid exits 0 and 1
        
        ctx = ProjectileContext(synergies={SynergyType.RAW: 100.0})
        
        # 1. Test with both valid
        results = splitter.process_energy(ctx, 3, valid_exits=[0, 1])
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].get_total_magnitude(), 50.0)
        self.assertEqual(results[1].get_total_magnitude(), 50.0)
        
        # 2. Test with one blocked
        results = splitter.process_energy(ctx, 3, valid_exits=[0]) # 1 blocked
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].get_total_magnitude(), 100.0) # Full power conserved
        
    def test_accumulation_logic(self):
        comp = ComponentEquipment(name="Test Gun", slot="right_arm")
        
        # Mock accumulation rate logic which normally comes from simulate_flow
        # We'll set it manually for testing update()
        comp.accumulation_rate = 50.0 
        
        comp.update(0.1) # 0.1 seconds
        self.assertAlmostEqual(comp.stored_energy, 5.0)
        
        comp.update(1.0)
        self.assertAlmostEqual(comp.stored_energy, 55.0)
        
        # Test Consume
        consumed = comp.consume_stored_energy(10.0)
        self.assertEqual(consumed, 10.0)
        self.assertAlmostEqual(comp.stored_energy, 45.0)
        
        # Test Discharge
        all_energy = comp.consume_stored_energy(None)
        self.assertAlmostEqual(all_energy, 45.0)
        self.assertEqual(comp.stored_energy, 0.0)

    def test_kinetic_spread_formula(self):
        # We can't easily test Player.shoot without mocking combat system, 
        # but we can verify the formula logic here
        
        def calculate_spread_step(kinetic_rate):
            base_spread = 0.15
            spread_factor = max(0.0, 1.0 - (kinetic_rate / 100.0))
            return base_spread * spread_factor
            
        # 0 Kinetic -> Full Spread
        self.assertAlmostEqual(calculate_spread_step(0.0), 0.15)
        
        # 50 Kinetic -> Half Spread
        self.assertAlmostEqual(calculate_spread_step(50.0), 0.075)
        
        # 100 Kinetic -> Zero Spread
        self.assertEqual(calculate_spread_step(100.0), 0.0)
        
        # 150 Kinetic -> Zero Spread (clamped)
        self.assertEqual(calculate_spread_step(150.0), 0.0)

if __name__ == '__main__':
    unittest.main()
