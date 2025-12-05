# pixbots_enhanced/ui/main_menu.py
# UPDATED to use DiegeticUI

import pygame
import logging
import constants
from core.asset_manager import ProceduralAssetManager
from ui.diegetic_ui import DiegeticUI

logger = logging.getLogger(__name__)

class MainMenu:
    """A diegetic main menu for the game."""
    def __init__(self, screen: pygame.Surface, asset_manager: ProceduralAssetManager):
        self.screen = screen
        self.asset_manager = asset_manager
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Use the asset manager to get fonts
        self.font_title = self.asset_manager.get_font(None, 72)
        self.font_button = self.asset_manager.get_font(None, 48)
        
        self.buttons = {
            "new_game": pygame.Rect(self.width/2 - 150, self.height/2 - 80, 300, 60),
            "load_game": pygame.Rect(self.width/2 - 150, self.height/2, 300, 60),
            "quit": pygame.Rect(self.width/2 - 150, self.height/2 + 80, 300, 60)
        }
        
        self.hovered_button = None

    def handle_input(self, event) -> str | None:
        if event.type == pygame.MOUSEMOTION:
            self.hovered_button = None
            for action, rect in self.buttons.items():
                if rect.collidepoint(event.pos):
                    self.hovered_button = action
                    break
                    
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                for action, rect in self.buttons.items():
                    if rect.collidepoint(event.pos):
                        logger.info(f"Main menu button '{action}' clicked.")
                        return action
        return None

    def draw(self):
        # Draw dark background
        self.screen.fill((5, 10, 5))
        
        # Draw Scanlines
        DiegeticUI.draw_scanlines(self.screen)
        
        # Title
        title_surf = self.font_title.render("Pixbots Enhanced", True, DiegeticUI.HOLO_GREEN)
        title_rect = title_surf.get_rect(center=(self.width/2, self.height/4))
        
        # Title Glow
        glow_surf = self.font_title.render("Pixbots Enhanced", True, DiegeticUI.HOLO_GREEN_DIM)
        self.screen.blit(glow_surf, (title_rect.x + 2, title_rect.y + 2))
        self.screen.blit(title_surf, title_rect)

        # Buttons
        for action, rect in self.buttons.items():
            is_hovered = (action == self.hovered_button)
            btn_text = action.replace("_", " ").title()
            
            DiegeticUI.draw_holographic_button(
                self.screen, rect, btn_text, self.font_button, is_hovered
            )

class PauseMenu:
    """A basic pause menu."""
    # This can be expanded with similar logic to MainMenu
    pass

