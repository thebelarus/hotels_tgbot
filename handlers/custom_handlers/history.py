from loguru import logger
from telebot.types import CallbackQuery, InlineKeyboardButton, Message
from telegram_bot_pagination import InlineKeyboardPaginator

from database.tools import CRUD
from loader import bot


@logger.catch
@bot.message_handler(commands=['history'])
def get_character(message: Message) -> None:
    '''Обработка команды пользователя на получение истории поиска'''
    send_history_page(message, message.from_user.id)


@logger.catch
@bot.callback_query_handler(
    func=lambda call: call.data.split('#')[0] == 'character')
def history_page_callback(callback_query: CallbackQuery) -> None:
    '''Обработка нажатия кнопок выбора соответсующей истории запроса'''
    page = int(callback_query.data.split('#')[1])
    bot.delete_message(
        callback_query.message.chat.id,
        callback_query.message.message_id
    )
    send_history_page(callback_query.message,
                      callback_query.from_user.id, page)


@logger.catch
@bot.callback_query_handler(
    func=lambda call: call.data.split('#')[0] == 'delete')
def history_item_delete_callback(callback_query: CallbackQuery) -> None:
    '''Удаление запроса пользователя из его истории поиска'''
    page = int(callback_query.data.split('#')[1])
    logger.debug(f'Удаление запроса с id {page}')
    is_request_completed = CRUD.delete_user_request(page)
    bot.delete_message(
        callback_query.message.chat.id,
        callback_query.message.message_id
    )
    if is_request_completed:
        logger.debug(f'Запрос с id {page} был удален с базы')
    send_history_page(callback_query.message, callback_query.from_user.id, 0)


@logger.catch
def send_history_page(message: Message, user_id: int, page: int = 1) -> None:
    '''Вывод пользователю результат запроса из его истории поиска'''
    logger.debug(
        f'{message.from_user.username} запросил историю запросов.')
    is_request_completed, requests_history = CRUD.get_user_requests(
        user_id)
    if is_request_completed and len(requests_history) > 0:
        request_id = requests_history[page-1].id
        paginator = InlineKeyboardPaginator(
            len(requests_history),
            current_page=page,
            data_pattern='character#{page}'
        )
        paginator.add_before(
            InlineKeyboardButton('Удалить из истории',
                                 callback_data='delete#{}'.format(request_id))
        )
        request = requests_history[page-1]
        result_message = (f'Дата запроса: {request.created_at}\n'
                          f'Команда: {request.command}\n'
                          f'Город: {request.city}\n'
                          f'Дата заезда: {request.start_date}\n'
                          f'Дата выезда: {request.end_date}\n'
                          f'Количество отелей: {request.hotels_count}\n'
                          )
        if None not in (
            request.distance,
            request.low_price,
            request.high_price
        ):
            result_message += (
                f'Запрашиваемая дистанция: {request.distance}км.\n'
                f'Минимальная цена: {request.low_price}$\n'
                f'Максимальна цена: {request.high_price}$\n'
            )
        result_message += '\nНайденные отели:'
        for item in request.history_request:
            result_message += (f'\nНазвание отеля <b>{item.hotel.name}</b> '
                               f'адресс  <b>{item.hotel.address}</b> '
                               f'дистанция  <b>{item.hotel.distance}км</b> '
                               f'цена  <b>{item.hotel_price}$</b>'
                               )
        bot.send_message(
            message.chat.id,
            result_message,
            reply_markup=paginator.markup,
            parse_mode='html'
        )
    else:
        bot.send_message(
            message.chat.id,
            'История пуста.'
        )
