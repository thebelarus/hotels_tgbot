from loguru import logger
from telebot.types import Message

from loader import bot


@logger.catch
@bot.message_handler(state=None)
def bot_echo(message: Message):
    '''Вывод сообщения для несуществующих комманд'''
    bot.reply_to(message, ("Данной команды не существует! "
                           "Список доступные команд /help"))
