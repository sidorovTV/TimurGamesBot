import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logger(name, log_file, level=logging.INFO):
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Ensure the log directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


# Setup loggers
main_logger = setup_logger('main', 'logs/main.log')
db_logger = setup_logger('database', 'logs/main.log')
admin_logger = setup_logger('admin', 'logs/main.log')
session_logger = setup_logger('session', 'logs/main.log')
help_logger = setup_logger('help', 'logs/main.log')
registration_logger = setup_logger('registration', 'logs/main.log')
start_logger = setup_logger('start', 'logs/main.log')
menu_logger = setup_logger('menu', 'logs/main.log')
notification_logger = setup_logger('notification', 'logs/main.log')
