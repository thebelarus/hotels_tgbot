from loguru import logger
from telebot.types import Message

from loader import bot


@logger.catch
@bot.message_handler(commands=['start'])
def bot_start(message: Message):
    '''Вывод сообщения приветствия'''
    bot.reply_to(message, f"Привет, {message.from_user.full_name}!")
