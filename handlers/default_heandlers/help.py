from loguru import logger
from telebot.types import Message

from config_data.config import DEFAULT_COMMANDS
from loader import bot


@logger.catch
@bot.message_handler(commands=['help'])
def bot_help(message: Message):
    '''Вывод сообщения с списком существующих комманд'''
    text = [f'/{command} - {desk}' for command, desk in DEFAULT_COMMANDS]
    bot.reply_to(message, '\n'.join(text))
