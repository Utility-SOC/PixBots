import pygame
import constants

class GarageMenu:
    def __init__(self, screen, asset_manager, player):
        self.screen = screen
        self.asset_manager = asset_manager
        self.player = player
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 32)
        
        # Simple buttons
        self.buttons = {
            "components": pygame.Rect(constants.SCREEN_WIDTH//2 - 150, 200, 300, 60),
            "equipment": pygame.Rect(constants.SCREEN_WIDTH//2 - 150, 280, 300, 60),
            "crafting": pygame.Rect(constants.SCREEN_WIDTH//2 - 150, 360, 300, 60),
            "missions": pygame.Rect(constants.SCREEN_WIDTH//2 - 150, 440, 300, 60),
            "main_menu": pygame.Rect(constants.SCREEN_WIDTH//2 - 150, 520, 300, 60)
        }

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            if self.buttons["components"].collidepoint(pos):
                return "components"
            elif self.buttons["equipment"].collidepoint(pos):
                return "equipment"
            elif self.buttons["crafting"].collidepoint(pos):
                return "crafting"
            elif self.buttons["missions"].collidepoint(pos):
                return "missions"
            elif self.buttons["main_menu"].collidepoint(pos):
                return "main_menu"
                
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "main_menu"
            
        return None

    def draw(self):
        self.screen.fill((20, 20, 30))
        
        # Title
        title = self.font.render("--- THE GARAGE ---", True, (255, 200, 50))
        self.screen.blit(title, (constants.SCREEN_WIDTH//2 - title.get_width()//2, 100))
        
        # Player Stats (Basic)
        if self.player:
            hp_text = self.small_font.render(f"Core HP: {self.player.hp} / {self.player.max_hp}", True, (200, 200, 200))
            self.screen.blit(hp_text, (50, 50))
        
        # Buttons
        for name, rect in self.buttons.items():
            color = (50, 150, 255) if rect.collidepoint(pygame.mouse.get_pos()) else (30, 80, 150)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (200, 200, 200), rect, 2)
            
            label = name.replace("_", " ").title()
            text = self.small_font.render(label, True, (255, 255, 255))
            self.screen.blit(text, (rect.centerx - text.get_width()//2, rect.centery - text.get_height()//2))
