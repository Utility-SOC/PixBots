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
        self.title_font = pygame.font.SysFont(None, 36)
        
        self.input_buffer = ""
        self.selected_indices = []
        self.message = "Select items to process"
        
        self.tabs = ["Fuse", "Recycle", "Upgrade"]
        self.current_tab_index = 0

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "close"
            elif event.key == pygame.K_TAB:
                self.current_tab_index = (self.current_tab_index + 1) % len(self.tabs)
                self.selected_indices = []
                self.input_buffer = ""
                self.message = f"Switched to {self.tabs[self.current_tab_index]} Mode"
            elif event.key == pygame.K_f or event.key == pygame.K_r or event.key == pygame.K_u:
                self.process_action()
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
                                # Selection limits based on mode
                                mode = self.tabs[self.current_tab_index]
                                if mode == "Fuse":
                                    if len(self.selected_indices) < 2:
                                        self.selected_indices.append(idx)
                                elif mode == "Recycle":
                                    self.selected_indices.append(idx) # Can select multiple
                                elif mode == "Upgrade":
                                    if len(self.selected_indices) < 1:
                                        self.selected_indices.append(idx)
                                        
                        self.input_buffer = ""
                    except ValueError:
                        self.input_buffer = ""
            elif event.unicode.isdigit():
                self.input_buffer += event.unicode
        return None

    def process_action(self):
        mode = self.tabs[self.current_tab_index]
        
        if mode == "Fuse":
            self.try_fuse()
        elif mode == "Recycle":
            self.try_recycle()
        elif mode == "Upgrade":
            self.try_upgrade()

    def try_fuse(self):
        if len(self.selected_indices) != 2:
            self.message = "Must select exactly 2 items to Fuse"
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

    def try_recycle(self):
        if not self.selected_indices:
            self.message = "Select items to recycle"
            return
            
        total_shards = 0
        # Process in reverse order to keep indices valid
        for idx in sorted(self.selected_indices, reverse=True):
            item = self.player.inventory.pop(idx)
            shards = item.get_recycle_value()
            total_shards += shards
            
        self.player.currencies["shards"] += total_shards
        self.selected_indices = []
        self.message = f"Recycled items for {total_shards} Shards!"

    def try_upgrade(self):
        if len(self.selected_indices) != 1:
            self.message = "Select exactly 1 item to Upgrade"
            return
            
        idx = self.selected_indices[0]
        item = self.player.inventory[idx]
        
        cost = item.get_upgrade_cost()
        if self.player.currencies["shards"] >= cost:
            self.player.currencies["shards"] -= cost
            item.upgrade()
            self.message = f"Upgraded {item.name} to Level {item.level}!"
            self.selected_indices = [] # Deselect after upgrade? Or keep selected for chain upgrade?
            # Let's keep it selected for convenience, but we need to re-verify cost next time
        else:
            self.message = f"Not enough Shards! Need {cost}"

    def draw(self):
        self.screen.fill((30, 30, 40))
        
        # Header
        mode = self.tabs[self.current_tab_index]
        title_text = f"Crafting Station - {mode} Mode (TAB to switch)"
        title = self.title_font.render(title_text, True, (255, 255, 255))
        self.screen.blit(title, (20, 20))
        
        # Currency Display
        shards = self.player.currencies.get("shards", 0)
        currency_text = f"Shards: {shards}"
        curr_surf = self.font.render(currency_text, True, (100, 255, 255))
        self.screen.blit(curr_surf, (self.screen.get_width() - 150, 20))
        
        # Message
        msg = self.font.render(self.message, True, (255, 255, 0))
        self.screen.blit(msg, (20, 60))
        
        # Instructions
        action_key = "F" if mode == "Fuse" else ("R" if mode == "Recycle" else "U")
        instr_text = f"Input Number + Enter to Select. Press '{action_key}' to {mode}. Esc to Exit."
        instr_surf = self.font.render(instr_text, True, (200, 200, 200))
        self.screen.blit(instr_surf, (20, 90))
        
        # Input Buffer
        input_text = f"Input: {self.input_buffer}"
        input_surf = self.font.render(input_text, True, (0, 255, 255))
        self.screen.blit(input_surf, (20, 120))
        
        # Inventory List
        y = 160
        for i, item in enumerate(self.player.inventory):
            color = (200, 200, 200)
            if i in self.selected_indices:
                color = (0, 255, 0)
            
            # Show extra info based on mode
            extra_info = ""
            if mode == "Recycle":
                extra_info = f" [+{item.get_recycle_value()} Shards]"
            elif mode == "Upgrade":
                cost = item.get_upgrade_cost()
                color_cost = (100, 255, 100) if self.player.currencies["shards"] >= cost else (255, 100, 100)
                # We can't easily change color mid-string with simple render, so just append text
                extra_info = f" [Cost: {cost} Shards] (Lvl {item.level})"
            
            text = f"{i+1}. {item.name} [{item.slot}] ({item.quality}){extra_info}"
            surf = self.font.render(text, True, color)
            self.screen.blit(surf, (50, y))
            y += 30
