from loguru import logger
from telebot import custom_filters

import handlers
from loader import bot
from utils.set_bot_commands import set_default_commands

if __name__ == '__main__':
    logger.debug('Настройка бота')
    bot.add_custom_filter(custom_filters.StateFilter(bot))
    bot.add_custom_filter(custom_filters.IsDigitFilter())
    set_default_commands(bot)
    logger.debug('Запуск бота')
    bot.infinity_polling(skip_pending=True)
