import pygame
import os
import json
import constants

class MissionSelectMenu:
    def __init__(self, screen, asset_manager):
        self.screen = screen
        self.asset_manager = asset_manager
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 24)
        
        self.missions = self._load_missions()
        self.selected_index = 0

    def _load_missions(self):
        missions = []
        maps_dir = os.path.join(constants.DATA_DIR, "maps")
        if not os.path.exists(maps_dir):
            return missions
            
        for filename in os.listdir(maps_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(maps_dir, filename), "r") as f:
                        data = json.load(f)
                        missions.append(data)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Failed to load mission {filename}: {e}")
        
        # Sort by name
        missions.sort(key=lambda x: x.get("name", ""))
        return missions

    def handle_input(self, event):
        if not self.missions:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "back"
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "back"
            elif event.key == pygame.K_UP:
                self.selected_index = max(0, self.selected_index - 1)
            elif event.key == pygame.K_DOWN:
                self.selected_index = min(len(self.missions) - 1, self.selected_index + 1)
            elif event.key == pygame.K_RETURN:
                return {"action": "launch", "mission": self.missions[self.selected_index].get("id")}
                
        return None

    def draw(self):
        self.screen.fill((20, 20, 30))
        
        title = self.font.render("--- MISSION SELECT ---", True, (255, 200, 50))
        self.screen.blit(title, (constants.SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        if not self.missions:
            msg = self.small_font.render("No missions found in /data/maps/.", True, (255, 100, 100))
            self.screen.blit(msg, (50, 150))
            return

        # List Menu
        y = 150
        for i, mission in enumerate(self.missions):
            color = (255, 255, 100) if i == self.selected_index else (200, 200, 200)
            prefix = ">> " if i == self.selected_index else "   "
            text = f"{prefix}{mission.get('name', 'Unknown')} [{mission.get('type', 'Unknown').upper()}]"
            surf = self.small_font.render(text, True, color)
            self.screen.blit(surf, (50, y))
            y += 40
            
        # Detail Panel (Right Side)
        mission = self.missions[self.selected_index]
        panel_x = constants.SCREEN_WIDTH // 2
        
        desc_title = self.small_font.render("Objectives:", True, (150, 200, 255))
        self.screen.blit(desc_title, (panel_x, 150))
        
        desc = self.small_font.render(mission.get('description', ''), True, (255, 255, 255))
        self.screen.blit(desc, (panel_x + 20, 180))
        
        lore_title = self.small_font.render("Transmission Log:", True, (150, 200, 255))
        self.screen.blit(lore_title, (panel_x, 240))
        
        lore_words = mission.get('lore', '').split(' ')
        lore_lines = []
        current_line = []
        for word in lore_words:
            current_line.append(word)
            if len(" ".join(current_line)) > 50:
                lore_lines.append(" ".join(current_line))
                current_line = []
        if current_line:
            lore_lines.append(" ".join(current_line))
            
        ly = 270
        for line in lore_lines:
            lsurf = self.small_font.render(line, True, (200, 255, 200))
            self.screen.blit(lsurf, (panel_x + 20, ly))
            ly += 25
            
        # Instructions
        inst = self.small_font.render("Up/Down: Select | Enter: Launch | Esc: Back", True, (100, 100, 100))
        self.screen.blit(inst, (constants.SCREEN_WIDTH//2 - inst.get_width()//2, constants.SCREEN_HEIGHT - 50))
