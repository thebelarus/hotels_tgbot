from telebot.handler_backends import State, StatesGroup


class HotelQueryState(StatesGroup):
    '''Класс состояния диалога с пользователем.'''
    command = State()
    city = State()
    city_id = State()
    enter_date = State()
    end_date = State()
    total_days = State()
    hotels_count = State()
    is_images_needed = State()
    images_count = State()
    distance = State()
    low_price = State()
    high_price = State()
