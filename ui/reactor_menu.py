# pixbots_enhanced/ui/reactor_menu.py
# Debug menu for adjusting torso reactor synergy outputs

import pygame
from typing import Optional
from hex_system.energy_packet import SynergyType, EnergyCore

class ReactorDebugMenu:
    """Debug UI for adjusting reactor synergy outputs."""
    
    def __init__(self, screen: pygame.Surface, player):
        self.screen = screen
        self.player = player
        self.font = pygame.font.SysFont(None, 24)
        self.title_font = pygame.font.SysFont(None, 36)
        
        self.synergy_types = [
            SynergyType.RAW,
            SynergyType.FIRE,
            SynergyType.ICE,
            SynergyType.LIGHTNING,
            SynergyType.VORTEX,
            SynergyType.POISON,
            SynergyType.EXPLOSION,
            SynergyType.KINETIC,
            SynergyType.PIERCE,
            SynergyType.VAMPIRIC,
        ]
        
        self.selected_index = 0
        self.message = "Adjust reactor synergy outputs (0-100)"
        
        #Get torso reactor
        self.reactor = self._get_torso_reactor()
        
        # Color map for synergies
        self.synergy_colors = {
            SynergyType.RAW: (150, 150, 150),
            SynergyType.FIRE: (255, 80, 20),
            SynergyType.ICE: (100, 200, 255),
            SynergyType.LIGHTNING: (255, 255, 100),
            SynergyType.VORTEX: (200, 100, 255),
            SynergyType.POISON: (100, 255, 100),
            SynergyType.EXPLOSION: (255, 150, 0),
            SynergyType.KINETIC: (200, 200, 200),
            SynergyType.PIERCE: (255, 255, 255),
            SynergyType.VAMPIRIC: (200, 0, 100),
        }
    
    def _get_torso_reactor(self) -> Optional[EnergyCore]:
        """Get the reactor from the player's torso component."""
        torso = self.player.components.get("torso")
        if torso and hasattr(torso, 'core'):
            return torso.core
        return None
    
    def handle_input(self, event):
        """Handle keyboard input."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_r:
                return "close"
            elif event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)
            elif event.key == pygame.K_DOWN:
                self.selected_index = min(len(self.synergy_types) -  1, self.selected_index + 1)
            elif event.key == pygame.K_LEFT:
                self._adjust_selected(-5.0)
            elif event.key == pygame.K_RIGHT:
                self._adjust_selected(5.0)
            elif event.key == pygame.K_LEFTBRACKET:  # [
                self._adjust_selected(-1.0)
            elif event.key == pygame.K_RIGHTBRACKET:  # ]
                self._adjust_selected(1.0)
            elif event.key == pygame.K_0:
                self._set_selected(0.0)
            elif pygame.K_1 <= event.key <= pygame.K_9:
                value = (event.key - pygame.K_0) * 10
                self._set_selected(float(value))
        return None
    
    def _adjust_selected(self, amount):
        """Adjust the selected synergy output by amount."""
        if not self.reactor:
            self.message = "No reactor found!"
            return
        
        synergy = self.synergy_types[self.selected_index]
        current = self.reactor.synergy_outputs.get(synergy, 0.0)
        new_value = max(0.0, min(100.0, current + amount))
        self.reactor.set_synergy_output(synergy, new_value)
        self.message = f"{synergy.value.upper()}: {new_value:.1f}"
    
    def _set_selected(self, value):
        """Set the selected synergy output to a specific value."""
        if not self.reactor:
            self.message = "No reactor found!"
            return
        
        synergy = self.synergy_types[self.selected_index]
        new_value = max(0.0, min(100.0, value))
        self.reactor.set_synergy_output(synergy, new_value)
        self.message = f"{synergy.value.upper()}: {new_value:.1f}"
    
    def draw(self):
        """Render the reactor debug menu."""
        self.screen.fill((20, 20, 30))
        
        # Title
        title = self.title_font.render("Reactor Synergy Configuration", True, (255, 255, 255))
        self.screen.blit(title, (20, 20))
        
        # Message/status
        msg = self.font.render(self.message, True, (255, 255, 100))
        self.screen.blit(msg, (20, 60))
        
        if not self.reactor:
            error = self.title_font.render("ERROR: No torso reactor found!", True, (255, 50, 50))
            self.screen.blit(error, (100, 200))
            inst = self.font.render("ESC: Close", True, (150, 150, 150))
            self.screen.blit(inst, (20, self.screen.get_height() - 40))
            return
        
        # Synergy list
        y = 110
        for i, synergy in enumerate(self.synergy_types):
            value = self.reactor.synergy_outputs.get(synergy, 0.0)
            color = self.synergy_colors.get(synergy, (255, 255, 255))
            
            # Highlight selected
            if i == self.selected_index:
                pygame.draw.rect(self.screen, (60, 60, 80), (10, y - 5, 760, 30))
                prefix = ">> "
            else:
                prefix = "   "
            
            # Synergy name
            name_text = f"{prefix}{synergy.value.upper()}"
            name_surf = self.font.render(name_text, True, color)
            self.screen.blit(name_surf, (20, y))
            
            # Value bar
            bar_x = 250
            bar_width = 400
            bar_height = 20
            
            # Background bar
            pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, y, bar_width, bar_height))
            
            # Filled bar
            fill_width = int((value / 100.0) * bar_width)
            if fill_width > 0:
                pygame.draw.rect(self.screen, color, (bar_x, y, fill_width, bar_height))
            
            # Border
            pygame.draw.rect(self.screen, color, (bar_x, y, bar_width, bar_height), 2)
            
            # Value text
            value_text = f"{value:.1f}"
            value_surf = self.font.render(value_text, True, (255, 255, 255))
            self.screen.blit(value_surf, (bar_x + bar_width + 10, y))
            
            y += 35
        
        # Dominant synergy display
        y += 20
        dominant = self.reactor.get_dominant_synergy()
        dominant_text = f"Dominant Synergy: {dominant.value.upper()}"
        dominant_color = self.synergy_colors.get(dominant, (255, 255, 255))
        dominant_surf = self.title_font.render(dominant_text, True, dominant_color)
        self.screen.blit(dominant_surf, (20, y))
        
        # Total output
        total = sum(self.reactor.synergy_outputs.values())
        total_text = f"Total Output: {total:.1f}"
        total_surf = self.font.render(total_text, True, (200, 200, 200))
        self.screen.blit(total_surf, (20, y + 40))
        
        # Instructions
        instructions = [
            "↑/↓: Select Synergy",
            "←/→: Adjust ±5 | [/]: Adjust ±1",
            "0-9: Set to (N×10) | ESC/R: Close"
        ]
        y = self.screen.get_height() - 80
        for inst in instructions:
            inst_surf = self.font.render(inst, True, (150, 150, 150))
            self.screen.blit(inst_surf, (20, y))
            y += 25
