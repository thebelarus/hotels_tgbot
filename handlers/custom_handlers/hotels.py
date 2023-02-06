import datetime

from dateutil.relativedelta import relativedelta
from loguru import logger
from telebot.types import CallbackQuery, Message
from telegram_bot_calendar import DetailedTelegramCalendar

from api import hotels_service
from config_data import config
from database.tools import CRUD
from keyboards.inline.cities_keyboard import cities_keyboard
from keyboards.reply.bool_keyboard import bool_keyboard
from loader import bot
from states.hotels_query import HotelQueryState


@logger.catch
@bot.message_handler(commands=['high', 'low', 'bestdeals'])
def initial_point(message: Message) -> None:
    '''
    Обработка комманд 'high', 'low', 'bestdeals' бота.
    Запрос названия города. Запись комманды в хранилище состояния.
    '''
    command_received = message.json['text']
    bot.set_state(
        message.from_user.id,
        HotelQueryState.city,
        message.chat.id)
    bot.send_message(
        message.from_user.id,
        f'Введите название города'
    )
    logger.debug(
        f'{message.from_user.username} ввел команду {command_received}')
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['command'] = command_received


@logger.catch
@bot.message_handler(state=HotelQueryState.city, regexp=r'[а-яА-Я -]{3,}')
def ask_city(message: Message) -> None:
    '''
    Запрос к API на получение ID локация на основание названия города.
    Запись названия города в хранилище состояния
    '''
    recived_cityname = message.json['text']
    request_completed,  cities_array = hotels_service.request_cities(
        recived_cityname)
    if request_completed and len(cities_array) > 0:
        logger.debug(
            (f'Пользователь {message.from_user.username}, '
             f'сделал запрос для города {recived_cityname}. '
             f'Были получены локации {cities_array}')
        )
        bot.send_message(
            message.chat.id,
            'Уточните выбор города из результатов поиска',
            reply_markup=cities_keyboard(cities_array)
        )
        bot.set_state(
            message.from_user.id,
            HotelQueryState.city_id,
            message.chat.id
        )
    elif request_completed:
        logger.error(
            (f'Пользователь {message.from_user.username}, '
             f'сделал запрос для города {recived_cityname}. '
             f'По данному городу {recived_cityname} ничего не найдено!'
             f'Были получены локации {cities_array}')
        )
        bot.send_message(
            message.chat.id,
            (f'По данному городу {recived_cityname} ничего не найдено! '
             'Повторите попытку с другим городом.')
        )
    else:
        logger.error(
            (f'Пользователь {message.from_user.username} '
             'Не получилось выполнить запрос на получения id локации!'
             )
        )
        bot.send_message(
            message.chat.id,
            'Не получилось выполнить запрос! Повторите попытку позже!'
        )


@logger.catch
@ bot.callback_query_handler(
    lambda callback_query: 'city:' in callback_query.data)
def city_callback(callback_query: CallbackQuery) -> None:
    '''Запрос количества отелей для поиска.
    Обработка ввода id c клавиатуры локаций.
    Запись id города в хранилище состояния.
    '''
    city_id_selected = callback_query.data.split(':')[1]
    city_name_selected = callback_query.data.split(':')[2]
    logger.debug(
        (f'Пользователь {callback_query.from_user.username}, '
         f'выбрал id города: {city_id_selected}')
    )
    bot.send_message(
        callback_query.from_user.id,
        ('Введите нужное количество отелей? '
         f'Не больше {config.HOTEL_REQUESTS_LIMIT}')
    )
    bot.set_state(
        callback_query.from_user.id,
        HotelQueryState.hotels_count
    )
    with bot.retrieve_data(
            callback_query.from_user.id,
            callback_query.message.chat.id) as data:
        data['city'] = city_name_selected
        data['city_id'] = city_id_selected


@logger.catch
@ bot.message_handler(state=HotelQueryState.hotels_count)
def ask_enter_date(message: Message) -> None:
    '''
    Запрос даты заезда в отель.
    Запись количества отелей в хранилище состояния
    '''
    if (message.text.isdigit() and
            0 < int(message.text) <= config.HOTEL_REQUESTS_LIMIT):
        current_date = datetime.date.today()
        calendar, step = DetailedTelegramCalendar(
            current_date=current_date,
            locale='ru',
            min_date=current_date,
            max_date=current_date + relativedelta(years=1)
        ).build()
        bot.send_message(
            message.chat.id,
            f'Выберите дату заезда',
            reply_markup=calendar
        )
        bot.set_state(
            message.from_user.id,
            HotelQueryState.enter_date,
            message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['hotels_count'] = int(message.text)
    else:
        bot.send_message(
            message.chat.id,
            ('Ошибка! Введите количество отелей целым положительным '
             f'чилом больше 0 но меньше {config.HOTEL_REQUESTS_LIMIT}')
        )


@logger.catch
@ bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def start_end_date_call(callback_query) -> None:
    '''Обработка ввода даты заезда/выезда полученной с клавиатуры'''
    result, key = None, None
    with bot.retrieve_data(
            callback_query.message.chat.id,
            callback_query.message.chat.id) as data:
        if not data.get('enter_date'):
            result, key, _ = DetailedTelegramCalendar(
                locale='ru',
                min_date=datetime.date.today()).process(callback_query.data)
        elif not data.get('end_date'):
            new_start_date = data.get('enter_date') + relativedelta(days=1)
            result, key, _ = DetailedTelegramCalendar(
                locale='ru',
                min_date=new_start_date).process(callback_query.data)
    if not result and key:
        bot.edit_message_text(
            "Введите дату",
            callback_query.message.chat.id,
            callback_query.message.message_id,
            reply_markup=key
        )
    elif result:
        with bot.retrieve_data(
                callback_query.message.chat.id,
                callback_query.message.chat.id) as data:
            if not data.get('enter_date'):
                data['enter_date'] = result
                calendar, _ = DetailedTelegramCalendar(
                    locale='ru',
                    min_date=result + relativedelta(days=1)).build()
                bot.edit_message_text("Выберите дату выезда",
                                      callback_query.message.chat.id,
                                      callback_query.message.message_id,
                                      reply_markup=calendar)
            elif not data.get('end_date'):
                data['end_date'] = result
                data['total_days'] = (
                    data['end_date'] - data['enter_date']).days
                bot.edit_message_reply_markup(
                    callback_query.message.chat.id,
                    callback_query.message.message_id,
                    reply_markup=None
                )
                bot.send_message(
                    callback_query.from_user.id,
                    'Нужны ли изображения отелей?',
                    reply_markup=bool_keyboard()
                )
                bot.set_state(
                    callback_query.from_user.id,
                    HotelQueryState.is_images_needed
                )


@logger.catch
@ bot.message_handler(state=HotelQueryState.is_images_needed)
def ask_is_images_needed(message: Message) -> None:
    '''Обработка условия требуются ли фотографии в запросе'''
    if message.text == 'Да':
        bot.send_message(
            message.chat.id,
            ('Cколько изображений каждого отеля требуется? '
             f'(Не больше {config.HOTEL_PHOTOS_LIMIT})')
        )
        bot.set_state(
            message.from_user.id,
            HotelQueryState.images_count,
            message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['is_images_needed'] = True
            data['images_count'] = 0
    else:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            command = data['command']
            data['is_images_needed'] = False
            data['images_count'] = 0
        if command == '/bestdeals':
            bot.send_message(
                message.chat.id,
                'Укажите динстанцию для поиска.')
            bot.set_state(
                message.from_user.id,
                HotelQueryState.distance,
                message.chat.id)
        else:
            final_step(message)


@logger.catch
def final_step(message: Message) -> None:
    '''Запрос и получение результата поиска. Вывод результата пользователю.'''
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        (response_status,
         response_data) = hotels_service.search_hotels_for_location(
            region_id=data.get('city_id'),
            limit=data.get('hotels_count'),
            checkInDate=data.get('enter_date'),
            checkOutDate=data.get('end_date'),
            distance=data.get('distance', None),
            low_price=data.get('low_price', None),
            high_price=data.get('high_price', None),
            command=data.get('command')
        )
        logger.debug(
            f"Пользователь {message.from_user.username} данные для запроса "
            f"Команда: {data['command']}\n"
            f"Имя города: {data['city']}\n"
            f"ID города City ID: {data['city_id']}\n"
            f"Дата заезда: {data['enter_date']}\n"
            f"Дата отъезда: {data['end_date']}\n"
            f"Количетсво отелей: {data['hotels_count']}\n"
            f"Нужны ли фото: {data['is_images_needed']}\n"
            f"Количество фото для запроса: {data['images_count']}\n")
        if response_status:
            hotels = []
            for (hotel_id,
                 hotel_name,
                 hotel_price,
                 destination) in response_data:
                (is_ok_status,
                 address,
                 images_links) = hotels_service.get_hotel_details(
                    hotel_id=hotel_id,
                    is_images_needed=data['is_images_needed'],
                    image_limit=int(data['images_count'])
                )
                if is_ok_status:
                    total_price = round(data['total_days']*hotel_price, 2)
                    msg = (f"Название отеля <b>{hotel_name}</b> цена за ночь: "
                           f"<b>{hotel_price}$</b> цена за указанный период "
                           f"<b>{total_price}$</b>, расстояние <b>"
                           f"{destination}</b>км, адресс: {address}")
                    bot.send_message(message.chat.id, msg,
                                     parse_mode='html')
                    for image_link in images_links:
                        bot.send_photo(message.chat.id, image_link)
                    hotel_info = {
                        'id': hotel_id,
                        'name': hotel_name,
                        'address': address,
                        'destination': destination,
                        'hotel_price': hotel_price
                    }
                    hotels.append(hotel_info)
                else:
                    bot.send_message(
                        message.chat.id,
                        ('Не удалось дополнительную '
                         f'получить информацию об отеле {hotel_name}'),
                        parse_mode='html')
            bot.send_message(message.chat.id, f'Поиск завершен.')
            write_request_completed = CRUD.write_request_to_history(
                created_at=datetime.datetime.now().isoformat(' ', 'seconds'),
                user=message.from_user.id,
                command=data['command'],
                city=data['city'],
                start_date=data['enter_date'],
                end_date=data['end_date'],
                hotels_count=data['hotels_count'],
                hotels=hotels,
                is_images_needed=data['is_images_needed'],
                images_count=data['images_count'],
                distance=data.get('distance', None),
                low_price=data.get('low_price', None),
                high_price=data.get('high_price', None)
            )
            if write_request_completed:
                logger.debug(
                    ('Данные поискового запроса и полученные результ '
                     'были записаны в базу данных')
                )
            else:
                logger.error(
                    ('Данные поискового запроса и полученные результ '
                     f'не были записаны в базу данных')
                )
        else:
            msg = ('Нет данных по данному запросу. '
                   f'Повторите попытку позже или измените параметры запроса')
            logger.error(msg)
            bot.send_message(message.chat.id, msg, parse_mode='html')
    bot.delete_state(message.from_user.id, message.chat.id)


@logger.catch
@ bot.message_handler(state=HotelQueryState.images_count, is_digit=True)
def ask_images_count(message: Message) -> None:
    '''
    Обработка условия запроса фотографий.
    Обработка ввода даты заезда/выезда полученной с клавиатуры
    '''
    if (message.text.isdigit() and
            0 < int(message.text) <= config.HOTEL_PHOTOS_LIMIT):
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            command = data['command']
            data['images_count'] = int(message.text)
        if command in ('/low', '/high'):
            final_step(message)
        elif command == '/bestdeals':
            bot.send_message(
                message.chat.id,
                'Укажите динстанцию для поиска.')
            bot.set_state(
                message.from_user.id,
                HotelQueryState.distance,
                message.chat.id)
    else:
        bot.send_message(
            message.chat.id,
            ('Ошибка! Введите количество фотографий целым положительным'
             f'чилом больше 0 но меньше {config.HOTEL_PHOTOS_LIMIT}')
        )


@ bot.message_handler(state=HotelQueryState.distance, is_digit=True)
def ask_distance(message: Message) -> None:
    '''
    Обработка условия запроса фотографий.
    Обработка ввода даты заезда/выезда полученной с клавиатуры
    '''
    bot.send_message(
        message.chat.id,
        'Укажите минимальную цену за номер')
    bot.set_state(
        message.from_user.id,
        HotelQueryState.low_price,
        message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['distance'] = int(message.text)


@logger.catch
@ bot.message_handler(state=HotelQueryState.low_price, is_digit=True)
def ask_low_price(message: Message) -> None:
    price = int(message.text)
    if price < 0:
        bot.send_message(
            message.chat.id,
            'Вы ввели некоректную цену, меньше 0! Повторите попытку!'
        )
    else:
        bot.send_message(
            message.chat.id,
            'Укажите маскимальную цену за номер')
        bot.set_state(
            message.from_user.id,
            HotelQueryState.high_price,
            message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['low_price'] = int(message.text)


@logger.catch
@ bot.message_handler(state=HotelQueryState.high_price, is_digit=True)
def get_high_price(message: Message) -> None:
    '''
    Проверка ввода максимальной цены,
    что она больше уже введенной минимальной.'''
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        low_price = data['low_price']
    price = int(message.text)
    if price < 0:
        bot.send_message(
            message.chat.id,
            'Вы ввели некоректную цену, меньше 0! Повторите попытку!'
        )
    elif price < low_price:
        bot.send_message(
            message.chat.id,
            'Вы ввели максимальную цену меньше минимальной! Повторите попытку!'
        )
    else:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['high_price'] = price
            username = message.from_user.username
            logger.debug((
                f"Пользователь {username}. Данные для запроса:"
                f"Команда: {data['command']}\n"
                f"Имя города: {data['city']}\n"
                f"ID города: {data['city_id']}\n"
                f"Дата заезда: {data['enter_date']}\n"
                f"Дата отъезда: {data['end_date']}\n"
                f"Количетсво отелей: {data['hotels_count']}\n"
                f"Нужны ли фото: {data['is_images_needed']}\n"
                f"Количество фото: {data['images_count']}\n"
                f"Дистанция: {data['distance']}\n"
                f"Минимальная цена: {data['low_price']}\n"
                f"Максимальная цена: {data['high_price']}"
            ))
        final_step(message)
        bot.delete_state(message.from_user.id, message.chat.id)


@ bot.message_handler(state=HotelQueryState.city)
def hotels_city_name_incorrect(message: Message) -> None:
    bot.send_message(
        message.chat.id,
        ('Вы ввели не некоректое название города. '
         'Требуются символы кирилицы! Повторите попытку.'))


@ bot.message_handler(state=HotelQueryState.low_price, is_digit=False)
@ bot.message_handler(state=HotelQueryState.high_price, is_digit=False)
@ bot.message_handler(state=HotelQueryState.distance, is_digit=False)
@ bot.message_handler(state=HotelQueryState.images_count, is_digit=False)
@ bot.message_handler(state=HotelQueryState.hotels_count, is_digit=False)
def hotels_digit_incorrect(message: Message) -> None:
    bot.send_message(
        message.chat.id, 'Вы ввели не число. Повторите попытку.')
