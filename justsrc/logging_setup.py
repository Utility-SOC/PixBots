# G:\work\pixelbots\logging_setup.py
import logging
import logging.handlers
import os
import sys

def configure_logging():
    """Sets up advanced, file-rotating logging for the application."""
    logs_dir = 'logs'
    os.makedirs(logs_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)8s] %(name)25s: %(message)s',
        handlers=[
            logging.handlers.RotatingFileHandler(
                os.path.join(logs_dir, 'pixbots.log'),
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            ),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logging.getLogger('pygame').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info("Logging configured.")

