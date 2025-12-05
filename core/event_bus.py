# G:\work\pixelbots\core\asset_manager.py
import pygame
import os
import json
import logging
import constants

logger = logging.getLogger(__name__)

class ProceduralAssetManager:
    def __init__(self):
        self.fonts = {}
        self.images = {}
        self.data_cache = {}
        logger.info("ProceduralAssetManager initialized.")

    def get_image(self, name: str, alpha: bool = True) -> pygame.Surface:
        if name in self.images:
            logger.debug(f"Retrieved cached image '{name}'")
            return self.images[name]

        logger.info(f"Loading image '{name}' from disk...")
        image_path = os.path.join(constants.SPRITES_DIR, name)
        try:
            image = pygame.image.load(image_path)
            if alpha:
                image = image.convert_alpha()
            else:
                image = image.convert()
            self.images[name] = image
            return image
        except (pygame.error, FileNotFoundError):
            logger.warning(f"Sprite '{name}' not found. Generating placeholder.")
            placeholder = self._create_placeholder(name)
            self.images[name] = placeholder
            return placeholder

    def get_font(self, name, size):
        key = (name, size)
        if key not in self.fonts:
            try:
                self.fonts[key] = pygame.font.Font(name, size)
            except (IOError, pygame.error):
                self.fonts[key] = pygame.font.Font(None, size)
        return self.fonts[key]

    def get_data(self, filename: str) -> dict:
        if filename in self.data_cache:
            return self.data_cache[filename]

        file_path = os.path.join(constants.DATA_DIR, filename)
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                self.data_cache[filename] = data
                return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Data file '{filename}' not found or invalid.", exc_info=True)
            return {}

    def _create_placeholder(self, name: str) -> pygame.Surface:
        surface = pygame.Surface((constants.TILE_SIZE, constants.TILE_SIZE), pygame.SRCALPHA)
        color = (abs(hash(name)) % 200 + 55, abs(hash(name) * 2) % 200 + 55, abs(hash(name) * 3) % 200 + 55)
        surface.fill(color)
        pygame.draw.rect(surface, (255, 0, 255), surface.get_rect(), 2)
        return surface

