import pygame
import constants
from ui.diegetic_ui import DiegeticUI

class SaveSlotMenu:
    def __init__(self, screen, asset_manager, save_load_system, mode="load"):
        self.screen = screen
        self.asset_manager = asset_manager
        self.save_load_system = save_load_system
        self.mode = mode # "load" or "new"
        
        self.font_title = self.asset_manager.get_font(None, 64)
        self.font_slot = self.asset_manager.get_font(None, 48)
        self.font_detail = self.asset_manager.get_font(None, 32)
        
        self.slots = ["Slot 1", "Slot 2", "Slot 3"]
        self.selected_index = 0
        
        # Load metadata for slots
        self.slot_data = {}
        self._refresh_slot_data()

    def _refresh_slot_data(self):
        for slot in self.slots:
            profile = slot.lower().replace(" ", "_")
            # We need a way to peek at save data without full load
            # For now, let's just check existence
            path = self.save_load_system.get_profile_path(profile)
            import os
            import json
            save_file = os.path.join(path, "savegame.json")
            if os.path.exists(save_file):
                try:
                    with open(save_file, 'r') as f:
                        data = json.load(f)
                        player_data = data.get("player", {})
                        self.slot_data[slot] = {
                            "exists": True,
                            "level": player_data.get("level", "?"),
                            "hp": f"{int(player_data.get('hp', 0))}/{int(player_data.get('max_hp', 0))}"
                        }
                except:
                    self.slot_data[slot] = {"exists": True, "error": "Corrupt"}
            else:
                self.slot_data[slot] = {"exists": False}

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.slots)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.slots)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return self.slots[self.selected_index].lower().replace(" ", "_")
            elif event.key == pygame.K_ESCAPE:
                return "back"
                
        elif event.type == pygame.MOUSEMOTION:
            mx, my = pygame.mouse.get_pos()
            center_x = self.screen.get_width() // 2
            start_y = 200
            for i, slot in enumerate(self.slots):
                rect = pygame.Rect(center_x - 200, start_y + i * 100, 400, 80)
                if rect.collidepoint(mx, my):
                    self.selected_index = i
                    
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mx, my = pygame.mouse.get_pos()
                center_x = self.screen.get_width() // 2
                start_y = 200
                for i, slot in enumerate(self.slots):
                    rect = pygame.Rect(center_x - 200, start_y + i * 100, 400, 80)
                    if rect.collidepoint(mx, my):
                        return slot.lower().replace(" ", "_")
                        
        return None

    def draw(self):
        self.screen.fill((5, 10, 5))
        DiegeticUI.draw_scanlines(self.screen)
        
        # Title
        title_text = "SELECT SAVE SLOT" if self.mode == "load" else "SELECT SLOT TO SAVE"
        title = self.font_title.render(title_text, True, DiegeticUI.HOLO_GREEN)
        self.screen.blit(title, (self.screen.get_width()//2 - title.get_width()//2, 50))
        
        center_x = self.screen.get_width() // 2
        start_y = 200
        
        for i, slot in enumerate(self.slots):
            rect = pygame.Rect(center_x - 200, start_y + i * 100, 400, 80)
            is_selected = (i == self.selected_index)
            
            # Draw Box
            color = DiegeticUI.HOLO_GREEN if is_selected else DiegeticUI.HOLO_GREEN_DIM
            pygame.draw.rect(self.screen, color, rect, 2)
            
            # Slot Name
            name_surf = self.font_slot.render(slot, True, color)
            self.screen.blit(name_surf, (rect.x + 20, rect.y + 10))
            
            # Metadata
            data = self.slot_data.get(slot, {})
            if data.get("exists"):
                details = f"Lvl {data.get('level')} | HP {data.get('hp')}"
                if self.mode == "new": details += " (Will Overwrite)"
                detail_surf = self.font_detail.render(details, True, DiegeticUI.HOLO_GREEN_DIM)
                self.screen.blit(detail_surf, (rect.x + 20, rect.y + 50))
            else:
                detail_surf = self.font_detail.render("Empty", True, (100, 100, 100))
                self.screen.blit(detail_surf, (rect.x + 20, rect.y + 50))
