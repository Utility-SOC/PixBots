import pygame
import constants

class PauseMenu:
    def __init__(self, screen, asset_manager):
        self.screen = screen
        self.asset_manager = asset_manager
        self.font = self.asset_manager.get_font(None, 48)
        self.small_font = self.asset_manager.get_font(None, 32)
        
        self.options = [
            {"text": "Resume", "action": "resume"},
            {"text": "Quick Save", "action": "save_load_menu"},
            {"text": "Main Menu", "action": "main_menu"},
            {"text": "Quit to Desktop", "action": "quit"}
        ]
        self.selected_index = 0
        
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.options)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return self.options[self.selected_index]["action"]
            elif event.key == pygame.K_ESCAPE:
                return "resume"
                
        elif event.type == pygame.MOUSEMOTION:
            mx, my = pygame.mouse.get_pos()
            # Simple mouse hover check
            center_x = self.screen.get_width() // 2
            start_y = 200
            for i, opt in enumerate(self.options):
                y = start_y + i * 60
                rect = pygame.Rect(center_x - 100, y - 15, 200, 30)
                if rect.collidepoint(mx, my):
                    self.selected_index = i
                    
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mx, my = pygame.mouse.get_pos()
                center_x = self.screen.get_width() // 2
                start_y = 200
                for i, opt in enumerate(self.options):
                    y = start_y + i * 60
                    rect = pygame.Rect(center_x - 100, y - 15, 200, 30)
                    if rect.collidepoint(mx, my):
                        return opt["action"]
                        
        return None

    def draw(self):
        # Draw semi-transparent background
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Draw Title
        title = self.font.render("PAUSED", True, (255, 255, 255))
        self.screen.blit(title, (self.screen.get_width()//2 - title.get_width()//2, 100))
        
        # Draw Options
        center_x = self.screen.get_width() // 2
        start_y = 200
        
        for i, opt in enumerate(self.options):
            color = (255, 255, 255)
            if i == self.selected_index:
                color = (255, 215, 0) # Gold
                
            text = self.small_font.render(opt["text"], True, color)
            self.screen.blit(text, (center_x - text.get_width()//2, start_y + i * 60))
