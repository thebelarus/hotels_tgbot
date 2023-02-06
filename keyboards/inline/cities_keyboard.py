from typing import Dict, List

from telebot.callback_data import CallbackData
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

cities_factory = CallbackData('city_id', 'city_name', prefix='city')


def cities_keyboard(cities: List) -> InlineKeyboardMarkup:
    print(cities)
    '''Возвращает клавиатуру для ввода найденных городов.'''
    return InlineKeyboardMarkup(
        keyboard=[
            [
                InlineKeyboardButton(
                    text=city_name,
                    callback_data=cities_factory.new(
                        city_id=city_id, city_name=city_name)
                )
            ]
            for city_name, city_id in cities
        ]
    )
