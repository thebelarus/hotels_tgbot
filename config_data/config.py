import os

from dotenv import find_dotenv, load_dotenv

if not find_dotenv():
    exit('Переменные окружения не загружены т.к отсутствует файл .env')
else:
    load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
RAPID_API_KEY = os.getenv('RAPID_API_KEY')
RAPID_API_HOST = os.getenv('RAPID_API_HOST')

BOT_DATABASE_NAME = 'bot.db'
REQUESTS_TIMEOUT = 30
HOTEL_PHOTOS_LIMIT = 10
HOTEL_REQUESTS_LIMIT = 15

DEFAULT_COMMANDS = (
    ('start', "Запустить бота"),
    ('help', "Вывести справку"),
    ('low', "Получить самые дешевые отели"),
    ('high', "Получить самые дорогие отели"),
    ('bestdeals', "Получить отели с заданной стоимостью"),
    ('history', "Получить историю запросов"),
)
