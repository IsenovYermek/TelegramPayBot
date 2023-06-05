import logging
import os
if not os.path.exists('logs'):
    os.makedirs('logs')

# Создаем форматтеры для логирования в файл и в консоль
file_formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
console_formatter = logging.Formatter(fmt='%(levelname)s - %(module)s - %(message)s')

# Создаем директорию для логов, если ее еще нет
if not os.path.exists('logs'):
    os.makedirs('logs')

# Логгер для записи ошибок и предупреждений
error_logger = logging.getLogger('error_logger')
error_logger.setLevel(logging.WARNING)  # Уровень логирования WARNING
error_handler = logging.FileHandler('logs/error.log', encoding='utf-8')
error_handler.setLevel(logging.WARNING)
error_handler.setFormatter(file_formatter)
error_logger.addHandler(error_handler)

# Логгер для записи остальных сообщений
info_logger = logging.getLogger('info_logger')
info_logger.setLevel(logging.DEBUG)  # Уровень логирования DEBUG
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(console_formatter)
info_logger.addHandler(console_handler)
