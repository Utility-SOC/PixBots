import pygame
import constants
from systems.crafting_system import CraftingSystem

class CraftingMenu:
    def __init__(self, screen, asset_manager, player):
        self.screen = screen
        self.asset_manager = asset_manager
        self.player = player
        self.crafting_system = CraftingSystem()
        self.font = pygame.font.SysFont(None, 24)
        
        self.input_buffer = ""
        self.selected_indices = []
        self.message = "Select 2 components to fuse"

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "close"
            elif event.key == pygame.K_f:
                self.try_fuse()
            elif event.key == pygame.K_BACKSPACE:
                self.input_buffer = self.input_buffer[:-1]
            elif event.key == pygame.K_RETURN:
                if self.input_buffer:
                    try:
                        idx = int(self.input_buffer) - 1
                        if 0 <= idx < len(self.player.inventory):
                            if idx in self.selected_indices:
                                self.selected_indices.remove(idx)
                            else:
                                if len(self.selected_indices) < 2:
                                    self.selected_indices.append(idx)
                        self.input_buffer = ""
                    except ValueError:
                        self.input_buffer = ""
            elif event.unicode.isdigit():
                self.input_buffer += event.unicode
        return None

    def try_fuse(self):
        if len(self.selected_indices) != 2:
            self.message = "Must select exactly 2 items"
            return
            
        idx1, idx2 = self.selected_indices
        comp1 = self.player.inventory[idx1]
        comp2 = self.player.inventory[idx2]
        
        new_comp = self.crafting_system.fuse_components(comp1, comp2)
        if new_comp:
            # Remove old items (reverse sort to avoid index shift)
            for idx in sorted(self.selected_indices, reverse=True):
                self.player.inventory.pop(idx)
            
            self.player.inventory.append(new_comp)
            self.selected_indices = []
            self.message = f"Fused: {new_comp.name}!"
        else:
            self.message = "Fusion failed (Must be same slot)"

    def draw(self):
        self.screen.fill((30, 30, 40))
        
        title = self.font.render("Crafting Station (Press F to Fuse, Esc to Exit)", True, (255, 255, 255))
        self.screen.blit(title, (20, 20))
        
        msg = self.font.render(self.message, True, (255, 255, 0))
        self.screen.blit(msg, (20, 50))
        
        input_text = f"Input: {self.input_buffer}"
        input_surf = self.font.render(input_text, True, (0, 255, 255))
        self.screen.blit(input_surf, (20, 80))
        
        y = 120
        for i, item in enumerate(self.player.inventory):
            color = (200, 200, 200)
            if i in self.selected_indices:
                color = (0, 255, 0)
            
            text = f"{i+1}. {item.name} [{item.slot}] ({item.quality})"
            surf = self.font.render(text, True, color)
            self.screen.blit(surf, (50, y))
            y += 30
