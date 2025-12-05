# pixbots_enhanced/ui/main_menu.py
# UPDATED to use the AssetManager

import pygame
import logging
import constants
from core.asset_manager import ProceduralAssetManager

logger = logging.getLogger(__name__)

class MainMenu:
    """A basic main menu for the game."""
    def __init__(self, screen: pygame.Surface, asset_manager: ProceduralAssetManager):
        self.screen = screen
        self.asset_manager = asset_manager
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Use the asset manager to get fonts
        self.font_title = self.asset_manager.get_font(None, 72)
        self.font_button = self.asset_manager.get_font(None, 48)
        
        self.buttons = {
            "new_game": pygame.Rect(self.width/2 - 150, self.height/2 - 50, 300, 60),
            "quit": pygame.Rect(self.width/2 - 150, self.height/2 + 50, 300, 60)
        }

    def handle_input(self, event) -> str | None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                for action, rect in self.buttons.items():
                    if rect.collidepoint(event.pos):
                        logger.info(f"Main menu button '{action}' clicked.")
                        return action
        return None

    def draw(self):
        # Title
        title_surf = self.font_title.render("Pixbots Enhanced", True, (255, 255, 100))
        title_rect = title_surf.get_rect(center=(self.width/2, self.height/4))
        self.screen.blit(title_surf, title_rect)

        # Buttons
        for action, rect in self.buttons.items():
            pygame.draw.rect(self.screen, (80, 80, 150), rect)
            pygame.draw.rect(self.screen, (200, 200, 255), rect, 3)
            
            btn_text = action.replace("_", " ").title()
            btn_surf = self.font_button.render(btn_text, True, (255, 255, 255))
            btn_rect = btn_surf.get_rect(center=rect.center)
            self.screen.blit(btn_surf, btn_rect)

class PauseMenu:
    """A basic pause menu."""
    # This can be expanded with similar logic to MainMenu
    pass

