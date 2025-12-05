import pygame
import logging
import constants
from ui.diegetic_ui import DiegeticUI

logger = logging.getLogger(__name__)

class PauseMenu:
    """A diegetic pause menu."""
    def __init__(self, screen: pygame.Surface, asset_manager):
        self.screen = screen
        self.asset_manager = asset_manager
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        self.font_title = self.asset_manager.get_font(None, 64)
        self.font_button = self.asset_manager.get_font(None, 36)
        
        # Menu Options
        self.options = [
            "Resume",
            "Save/Load",
            "Settings",
            "Help",
            "Exit to Main Menu",
            "Exit Desktop"
        ]
        
        # Calculate layout
        self.buttons = {}
        btn_width = 300
        btn_height = 50
        start_y = self.height / 2 - (len(self.options) * 60) / 2
        
        for i, option in enumerate(self.options):
            rect = pygame.Rect(
                self.width / 2 - btn_width / 2,
                start_y + i * 60,
                btn_width,
                btn_height
            )
            self.buttons[option] = rect
            
        self.hovered_button = None
        self.sub_state = "main" # main, save_load, settings, help

    def handle_input(self, event) -> str | None:
        if self.sub_state == "main":
            if event.type == pygame.MOUSEMOTION:
                self.hovered_button = None
                for action, rect in self.buttons.items():
                    if rect.collidepoint(event.pos):
                        self.hovered_button = action
                        break
                        
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for action, rect in self.buttons.items():
                        if rect.collidepoint(event.pos):
                            return self._handle_action(action)
                            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "resume"
                    
        return None

    def _handle_action(self, action):
        if action == "Resume":
            return "resume"
        elif action == "Save/Load":
            # For now, just print or maybe trigger a quick save/load?
            # User asked for a menu, so maybe we should show sub-options.
            # But for MVP, let's just return the action string and handle in main.py
            # or toggle a sub-state here.
            return "save_load_menu" 
        elif action == "Settings":
            return "settings"
        elif action == "Help":
            return "help"
        elif action == "Exit to Main Menu":
            return "main_menu"
        elif action == "Exit Desktop":
            return "quit"
        return None

    def draw(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        # Draw Scanlines
        DiegeticUI.draw_scanlines(self.screen)
        
        # Title
        title_surf = self.font_title.render("PAUSED", True, DiegeticUI.HOLO_GREEN)
        title_rect = title_surf.get_rect(center=(self.width/2, self.height/4))
        
        # Glow
        glow_surf = self.font_title.render("PAUSED", True, DiegeticUI.HOLO_GREEN_DIM)
        self.screen.blit(glow_surf, (title_rect.x + 2, title_rect.y + 2))
        self.screen.blit(title_surf, title_rect)
        
        # Buttons
        for action, rect in self.buttons.items():
            is_hovered = (action == self.hovered_button)
            
            DiegeticUI.draw_holographic_button(
                self.screen, rect, action, self.font_button, is_hovered
            )
