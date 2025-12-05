# G:\work\pixelbots\core\game_state.py
import logging
import constants

logger = logging.getLogger(__name__)

class GameStateManager:
    def __init__(self, initial_state=constants.STATE_MENU):
        self.state = initial_state
        self.previous_state = None
        logger.info(f"GameStateManager initialized to: {self.state}")

    def set_state(self, new_state):
        if self.state != new_state:
            self.previous_state = self.state
            logger.info(f"State change: '{self.state}' -> '{new_state}'")
            self.state = new_state

    def get_state(self):
        return self.state

    def get_previous_state(self):
        return self.previous_state

