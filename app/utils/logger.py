import logging
import os
import colorlog
from logging.handlers import RotatingFileHandler

def get_custom_logger(name="pos_backend"):
    """
    Creates and returns a custom logger that logs to both the console (with colors)
    and a file with rotating file handler.
    """
    # Create logs directory if it doesn't exist at the root of the project
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
    
    # Simpler approach: Create 'logs' folder relative to the current working directory
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid duplicate logs if handlers are already configured
    if not logger.handlers:
        # Custom formatter for the file logs (no colors)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Custom formatter for the console logs (with colors)
        console_formatter = colorlog.ColoredFormatter(
            '%(cyan)s%(asctime)s%(reset)s - %(name)s - %(log_color)s%(levelname)s%(reset)s - [%(purple)s%(filename)s:%(lineno)d%(reset)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            }
        )

        # File handler (10 MB per file, keep 5 backups)
        file_handler = RotatingFileHandler(
            'logs/app.log', maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.INFO)

        # Standard console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

# Expose a default logger instance to be imported anywhere in the app
logger = get_custom_logger()
