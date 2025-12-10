import pygame
from systems.energy_system import EnergySystem

class HUD:
    def __init__(self, asset_manager):
        self.asset_manager = asset_manager
        self.font = asset_manager.get_font(None, 24)
        
    def draw_top_left_hud(self, surface, player):
        input_rate, output_rate = EnergySystem.calculate_total_output(player)
        
        # Colors: Green if Output <= Input, Red if Output > Input (Wasted/Deficit)
        # Wait, Input > Output means wasted energy? No, Input > Output means we have surplus.
        # "Input > Output means wasted energy" ... yes, if we generate more than we use, it's "wasted" in some sense, but typically good.
        # If Input < Output, we are draining batteries (bad).
        # Let's use:
        # Green if Input >= Output (Surplus/Balanced)
        # Yellow if Input < Output (Deficit - relying on buffer)
        # But for "wasted energy" warning...
        # Let's allow Green for Surplus.
        
        color = (50, 255, 50) 
        if output_rate > input_rate:
            color = (255, 50, 50) # Red warning
        
        text = f"Input: {input_rate:.0f}/s | Output: {output_rate:.0f}/s"
        surf = self.font.render(text, True, color)
        
        # Background box for legibility
        bg_rect = surf.get_rect(topleft=(10, 10))
        bg_rect.inflate_ip(10, 10)
        s = pygame.Surface(bg_rect.size)
        s.set_alpha(128)
        s.fill((0, 0, 0))
        surface.blit(s, bg_rect)
        
        surface.blit(surf, (15, 15))

        # Show HP and Shield
        hp_color = (255, 50, 50)
        shield_color = (50, 150, 255)
        
        hp_text = f"HP: {int(player.hp)}/{int(player.max_hp)}"
        shield_text = f"Shield: {int(getattr(player, 'shield', 0))}/{int(getattr(player, 'max_shield', 100))}"
        
        hp_surf = self.font.render(hp_text, True, hp_color)
        shield_surf = self.font.render(shield_text, True, shield_color)
        
        surface.blit(hp_surf, (15, 45))
        surface.blit(shield_surf, (15, 75))
