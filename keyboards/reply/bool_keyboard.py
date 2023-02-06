from telebot import types


def bool_keyboard() -> types.ReplyKeyboardMarkup:
    '''Возвращает клавиатуру для ввода значаний Да или Нет'''
    markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
    item_button_1 = types.KeyboardButton('Да')
    item_button_2 = types.KeyboardButton('Нет')
    markup.add(item_button_1, item_button_2)
    return markup
