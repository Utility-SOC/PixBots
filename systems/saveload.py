# pixbots_enhanced/systems/saveload.py
# Source: Extracted from Version 2's complete_main_py.py
# Description: Handles saving and loading game state and AI data.

import os
import json
import logging
import constants

logger = logging.getLogger(__name__)

class SaveLoadSystem:
    def __init__(self, saves_dir: str, data_dir: str):
        self.saves_dir = saves_dir
        self.data_dir = data_dir
        os.makedirs(self.saves_dir, exist_ok=True)

    def get_profile_path(self, profile_name: str) -> str:
        return os.path.join(self.saves_dir, profile_name)

    def load_ai_workbook(self, profile_name: str) -> dict | None:
        profile_path = self.get_profile_path(profile_name)
        workbook_file = os.path.join(profile_path, "ai_workbook.json")
        if not os.path.exists(workbook_file):
            return None
        try:
            with open(workbook_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load AI workbook for '{profile_name}': {e}")
            return None

    def save_ai_workbook(self, profile_name: str, workbook_data: dict) -> bool:
        profile_path = self.get_profile_path(profile_name)
        os.makedirs(profile_path, exist_ok=True)
        workbook_file = os.path.join(profile_path, "ai_workbook.json")
        try:
            with open(workbook_file, 'w') as f:
                json.dump(workbook_data, f, indent=4)
            return True
        except IOError as e:
            logger.error(f"Failed to save AI workbook for '{profile_name}': {e}")
            return False

    def save_game(self, profile_name: str, player, map_seed: int = None) -> bool:
        profile_path = self.get_profile_path(profile_name)
        os.makedirs(profile_path, exist_ok=True)
        save_file = os.path.join(profile_path, "savegame.json")
        
        data = {
            "player": player.to_dict(),
            "map_seed": map_seed,
            "version": "0.2.0"
        }
        
        try:
            with open(save_file, 'w') as f:
                json.dump(data, f, indent=4)
            logger.info(f"Game saved to {save_file}")
            return True
        except IOError as e:
            logger.error(f"Failed to save game for '{profile_name}': {e}")
            return False

    def load_game(self, profile_name: str, asset_manager=None):
        """Returns a tuple (Player, map_seed) or None."""
        profile_path = self.get_profile_path(profile_name)
        save_file = os.path.join(profile_path, "savegame.json")
        
        if not os.path.exists(save_file):
            return None
            
        try:
            with open(save_file, 'r') as f:
                data = json.load(f)
                
            from entities.player import Player
            player = Player.from_dict(data["player"], asset_manager)
            map_seed = data.get("map_seed")
            
            logger.info(f"Game loaded from {save_file}")
            return player, map_seed
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load game for '{profile_name}': {e}")
            return None