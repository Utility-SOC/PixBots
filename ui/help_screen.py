import pygame
import constants
import os

class HelpScreen:
    def __init__(self, screen, asset_manager):
        self.screen = screen
        self.asset_manager = asset_manager
        self.font_title = pygame.font.SysFont("arial", 48, bold=True)
        self.font_header = pygame.font.SysFont("arial", 36, bold=True)
        self.font_text = pygame.font.SysFont("arial", 24)
        self.font_code = pygame.font.SysFont("consolas", 20)
        
        self.scroll_y = 0
        self.content_height = 1000 
        self.readme_lines = self.load_readme()
        
    def load_readme(self):
        try:
            with open("README.md", "r") as f:
                return f.readlines()
        except FileNotFoundError:
            return ["README.md not found."]

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "close"
            elif event.key == pygame.K_UP:
                self.scroll_y = min(0, self.scroll_y + 40)
            elif event.key == pygame.K_DOWN:
                max_scroll = -(self.content_height - self.screen.get_height() + 50)
                if max_scroll > 0: max_scroll = 0
                self.scroll_y = max(max_scroll, self.scroll_y - 40)
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_y += event.y * 40
            # Clamp
            max_scroll = -(self.content_height - self.screen.get_height() + 50)
            if max_scroll > 0: max_scroll = 0
            self.scroll_y = max(max_scroll, min(0, self.scroll_y))
            
        return None

    def draw(self):
        self.screen.fill((20, 20, 30))
        
        y = 50 + self.scroll_y
        x = 50
        max_width = self.screen.get_width() - 100
        
        for line in self.readme_lines:
            line = line.strip()
            if not line:
                y += 10
                continue
                
            if line.startswith("# "):
                # H1
                surf = self.font_title.render(line[2:], True, (255, 255, 255))
                self.screen.blit(surf, (x, y))
                y += 60
            elif line.startswith("## "):
                # H2
                surf = self.font_header.render(line[3:], True, (100, 200, 255))
                self.screen.blit(surf, (x, y))
                y += 45
            elif line.startswith("### "):
                # H3
                surf = self.font_header.render(line[4:], True, (150, 220, 255))
                # Scale down slightly?
                surf = pygame.transform.scale(surf, (int(surf.get_width()*0.8), int(surf.get_height()*0.8)))
                self.screen.blit(surf, (x, y))
                y += 35
            elif line.startswith("- "):
                # Bullet
                surf = self.font_text.render(line, True, (220, 220, 220))
                self.screen.blit(surf, (x + 20, y))
                y += 30
            elif line.startswith("    ") or line.startswith("\t"):
                # Code block / Indent
                surf = self.font_code.render(line.strip(), True, (200, 255, 200))
                self.screen.blit(surf, (x + 40, y))
                y += 25
            else:
                # Normal text
                surf = self.font_text.render(line, True, (200, 200, 200))
                self.screen.blit(surf, (x, y))
                y += 30
                
        self.content_height = y - self.scroll_y
