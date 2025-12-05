import unittest
import sys
import os
import math

# Suppress pygame prompt
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import constants
from entities.enemy import Enemy
from entities.bot import Bot
from systems.crafting_system import CraftingSystem
from equipment.component import ComponentEquipment, create_starter_torso
from hex_system.energy_packet import EnergyCore, SynergyType
from hex_system.hex_coord import HexCoord

class TestMechanics(unittest.TestCase):
    def setUp(self):
        print(f"Running test: {self._testMethodName}")

    def test_boss_invulnerability(self):
        print("Testing Boss Invulnerability...")
        boss = Enemy("Boss", 0, 0, ai_class="Boss")
        boss.hp = 1000
        
        # Default: Vulnerable
        constants.BOSS_INVULNERABLE = False
        boss.take_damage(100)
        self.assertLess(boss.hp, 1000, "Boss should take damage when vulnerable")
        
        # Invulnerable
        constants.BOSS_INVULNERABLE = True
        prev_hp = boss.hp
        boss.take_damage(100)
        self.assertEqual(boss.hp, prev_hp, "Boss should NOT take damage when invulnerable")
        
        # Reset
        constants.BOSS_INVULNERABLE = False
        print("Boss Invulnerability Passed")

    def test_crafting_synergy_merge(self):
        print("Testing Crafting Synergy Merge...")
        crafting = CraftingSystem()
        
        # Create Torso 1 (Fire)
        t1 = create_starter_torso()
        t1.core = EnergyCore(core_type=SynergyType.FIRE, generation_rate=10.0, position=HexCoord(0,0))
        t1.core.synergy_outputs = {SynergyType.FIRE: 10.0}
        
        # Create Torso 2 (Ice)
        t2 = create_starter_torso()
        t2.core = EnergyCore(core_type=SynergyType.ICE, generation_rate=20.0, position=HexCoord(0,0))
        t2.core.synergy_outputs = {SynergyType.ICE: 20.0}
        
        # Fuse
        fused = crafting.fuse_components(t1, t2)
        
        self.assertIsNotNone(fused)
        self.assertEqual(fused.slot, "torso")
        self.assertIsNotNone(fused.core)
        
        # Check Synergies
        outputs = fused.core.synergy_outputs
        self.assertIn(SynergyType.FIRE, outputs)
        self.assertIn(SynergyType.ICE, outputs)
        self.assertEqual(outputs[SynergyType.FIRE], 10.0)
        self.assertEqual(outputs[SynergyType.ICE], 20.0)
        print("Crafting Synergy Merge Passed")

    def test_collision_damage(self):
        print("Testing Collision Damage...")
        bot = Bot("TestBot", 0, 0)
        bot.velocity_x = 500 # High speed
        bot.max_hp = 100
        bot.hp = 100
        
        # Mock GameMap
        class MockMap:
            def __init__(self):
                self.width = 10
                self.height = 10
                self.terrain = [[constants.GRASS for _ in range(10)] for _ in range(10)]
                self.obstacles = set()
                
        game_map = MockMap()
        # Place obstacle at (1, 0)
        game_map.obstacles.add((1, 0))
        
        # Update movement with collision
        # dt=0.1 -> move 50 units. TILE_SIZE is usually 32. 50 > 32.
        # Should hit (1,0)
        
        bot.update_movement(1, 0, 0.1, game_map)
        
        print(f"DEBUG: Bot HP: {bot.hp}, Velocity X: {bot.velocity_x}")
        
        # Check if damage taken
        # Velocity was 500. Damage = 500 * 0.1 = 50.
        self.assertLess(bot.hp, 100, "Bot should take collision damage")
        self.assertEqual(bot.velocity_x, 0, "Bot should stop on collision")
        print("Collision Damage Passed")

if __name__ == '__main__':
    unittest.main()
