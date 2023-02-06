from typing import Any

import peewee as pw
from loguru import logger

from database.models import History, Hotel, Request, db


@logger.catch
def create_and_return_hotel(id,
                            name,
                            address,
                            distance):
    '''Создание отеля в базе данных'''
    try:
        with db:
            Hotel.create(
                id=id,
                name=name,
                address=address,
                distance=distance).save()
            logger.debug(f'Отель с {id} и именем {name} записан в базу')
            return True, Hotel.get(Hotel.id == id)
    except pw.IntegrityError:
        logger.debug(f'Отель с {id} и именем {name} уже находится в базе')
        return True, Hotel.get(Hotel.id == id)
    except Exception as error:
        logger.debug(f'Ошибка при работе с базой: {error}')
        return False, None


@logger.catch
def create_and_return_request(created_at,
                              user,
                              command,
                              city,
                              start_date,
                              end_date,
                              hotels_count,
                              is_images_needed=False,
                              images_count=0,
                              distance=None,
                              low_price=None,
                              high_price=None
                              ):
    '''Создание и возврат запроса пользователя в базе данных'''
    try:
        request = Request.create(
            created_at=created_at,
            user=user,
            command=command,
            city=city,
            start_date=start_date,
            end_date=end_date,
            hotels_count=hotels_count,
            is_images_needed=is_images_needed,
            images_count=images_count
        )
        if distance is not None:
            request.distance = distance
        if low_price is not None:
            request.low_price = low_price
        if high_price is not None:
            request.high_price = high_price
        request.save()
        return True, Request.select().where(
            Request.created_at == created_at,
            Request.user == user
        )
    except pw.IntegrityError:
        logger.debug(
            (f'Запрос с датой {created_at} и пользователем '
             f'{user} уже находится в базе!'))
        return True, Request.select().where(
            Request.created_at == created_at,
            Request.user == user
        )
    except Exception as error:
        logger.exception(f'Ошибка при работе с базой: {error}')
        return False, None


@logger.catch
def write_request_to_history(created_at,
                             user,
                             command,
                             city,
                             start_date,
                             end_date,
                             hotels_count,
                             hotels,
                             is_images_needed=False,
                             images_count=0,
                             distance=None,
                             low_price=None,
                             high_price=None
                             ) -> bool:
    '''Запись всех данных(запрос и отели) в базу данных'''
    with db:
        if len(hotels) < 1:
            return False
        is_completed, request_creaded = create_and_return_request(
            created_at=created_at,
            user=user,
            command=command,
            city=city,
            start_date=start_date,
            end_date=end_date,
            hotels_count=hotels_count,
            is_images_needed=is_images_needed,
            images_count=images_count,
            distance=distance,
            low_price=low_price,
            high_price=high_price
        )
        if not is_completed:
            logger.error(
                'Не удалось записать и получить данные запроса в базу.')
            return False
        for hotel in hotels:
            is_completed, hotel_creaded = create_and_return_hotel(
                id=hotel['id'],
                name=hotel['name'],
                address=hotel['address'],
                distance=hotel['destination']
            )
            if not is_completed:
                logger.error('Не удалось записать данные отелей в базу.')
                return False
            is_completed = create_and_return_history(
                request=request_creaded,
                hotel=hotel_creaded,
                hotel_price=hotel['hotel_price']
            )
            if not is_completed:
                logger.error('Не удалось записать данные истории в базу.')
                return False
        return True


@logger.catch
def create_and_return_history(request,
                              hotel,
                              hotel_price):
    '''Запись связи отель-запрос в базу данных'''
    try:
        with db:
            History.create(
                request=request,
                hotel=hotel,
                hotel_price=hotel_price
            ).save()
            logger.debug(f'Данные истории поиска записаны в базу!')
            return True
    except pw.IntegrityError:
        logger.debug(
            (f'Запись с запросом {request} и отелем '
             f'{hotel} уже находится в базе!'))
        return True
    except Exception as error:
        logger.exception(f'Ошибка при работе с базой: {error}')
        return False


@logger.catch
def get_user_requests(user: int) -> tuple[bool, Any]:
    '''Получение всех запросов для пользотвателя'''
    try:
        with db:
            return True, Request.filter(Request.user == user)
    except Request.DoesNotExist:
        logger.error(f'Отеля с id {id} не сущетсвует в базе!')
        return False, None
    except Exception as error:
        logger.exception(f'Ошибка при работе с базой: {error}')
        return False, None


@logger.catch
def delete_user_request(request_id: int) -> bool:
    '''Удаление запроса пользователя по id'''
    with db.atomic() as transaction:
        try:
            history_for_request = History.delete().where(
                History.request == request_id)
            history_for_request.execute()
            request = Request.get(id=request_id)
            request.delete_instance()
            return True
        except pw.ErrorSavingData:
            logger.error(
                ('Ошибка выполнения транзакции на '
                 f'удаление данных запроса с id {id}'))
            transaction.rollback()
            return False
