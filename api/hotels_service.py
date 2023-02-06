import datetime
from typing import Dict, List, Tuple

import requests
from loguru import logger

from config_data import config


class API_SETTINGS:
    ENDPOINTS = {
        'search': 'locations/v3/search',
        'list': 'properties/v2/list',
        'detail': 'properties/v2/detail',
    }

    HEADERS = {
        "X-RapidAPI-Key": config.RAPID_API_KEY,
        "X-RapidAPI-Host": config.RAPID_API_HOST
    }

    TIMEOUT = config.REQUESTS_TIMEOUT


@logger.catch
def request_cities(location_name: str) -> Tuple[bool, List[Tuple[str, str]]]:
    '''
    Получение городо по заданному имени локации
    :param location_name:
    :return:
    '''
    params = {
        'q': location_name,
        'locale': 'ru_RU'
    }
    is_ok_request_status, request_data = make_api_request(
        API_SETTINGS.ENDPOINTS['search'],
        'GET',
        params=params,
        headers=API_SETTINGS.HEADERS,
        json=[]
    )
    results = []
    if not is_ok_request_status:
        return is_ok_request_status, []
    try:
        for item in request_data['sr']:
            if item["type"] == 'CITY':
                results.append(
                    (item["regionNames"]['shortName'], item["gaiaId"]))
    except Exception as error:
        logger.exception(
            ('Ошибка при разборе ответа от сервера '
             f'при запросе id локаций города {error}'))
        return False, results
    finally:
        return is_ok_request_status, results


@logger.catch
def _sort_hotels_from_high_to_low(
    hotels: List[Tuple[str, float]],
        limit: int = 10) -> List[Tuple[str, float]]:
    '''Сортировка отелей по убыванию цены'''
    return sorted(
        hotels, key=lambda hotel: hotel[2], reverse=True
    )[:limit]


@logger.catch
def _sort_hotels_by_distance_limit(
    hotels: List[Tuple[str, float]],
        distance: int,
        limit: int = 10, ) -> List[Tuple[str, float]]:
    '''Сортировка отелей по убыванию дистанции от центра города'''
    hotels = list(filter(lambda hotel: hotel[3] < distance, hotels))
    hotels = sorted(hotels, key=lambda x: (x[2], x[3]))
    return hotels[:limit]


@logger.catch
def search_hotels_for_location(
        region_id: str,
        limit: int,
        checkInDate: datetime.datetime,
        checkOutDate: datetime.datetime,
        distance: int = None,
        low_price: int = None,
        high_price: int = None,
        command: str = '/low') -> List:
    '''
    Поиск отелей в заданной локации.
    Ответ список отелей с базовой информацией: id отеля, название, цена
    '''
    payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "ru_RU",
        "siteId": 300000001,
        "destination": {"regionId": str(region_id)},
        "checkInDate": {
            "day": checkInDate.day,
            "month": checkInDate.month,
            "year": checkInDate.year
        },
        "checkOutDate": {
            "day": checkOutDate.day,
            "month": checkOutDate.month,
            "year": checkOutDate.year
        },
        "rooms": [{"adults": 1}],
        "resultsStartingIndex": 0,
        "resultsSize": limit,
        "filters": {"availableFilter": "SHOW_AVAILABLE_ONLY"}
    }
    if command == '/low':
        payload['sort'] = 'PRICE_LOW_TO_HIGH'
    elif command == '/high':
        payload['resultsSize'] = 200
    elif command == '/bestdeals':
        payload['sort'] = 'DISTANCE'
        payload['resultsSize'] = 200
        payload['filters']['price'] = {"max": high_price, "min": low_price}
    else:
        return False, []
    is_ok_request_status, request_data = make_api_request(
        method_endswith=API_SETTINGS.ENDPOINTS['list'],
        method_type='POST',
        json=payload,
        headers=API_SETTINGS.HEADERS | {"content-type": "application/json"},
        params=[]
    )
    try:
        if is_ok_request_status:
            parser_responce_hotels = []
            hotels = request_data['data']['propertySearch']['properties']
            for hotel_item in hotels:
                parser_responce_hotels.append(
                    (
                        hotel_item['id'],
                        hotel_item['name'],
                        round(hotel_item['price']['lead']['amount'], 2),
                        (hotel_item['destinationInfo']
                         ['distanceFromDestination']
                         ['value'])
                    )
                )
            if command == '/high':
                parser_responce_hotels = _sort_hotels_from_high_to_low(
                    hotels=parser_responce_hotels,
                    limit=limit)
            elif command == '/bestdeals':
                parser_responce_hotels = _sort_hotels_by_distance_limit(
                    hotels=parser_responce_hotels,
                    distance=distance,
                    limit=limit)
            return True, parser_responce_hotels
        else:
            return False, []
    except (KeyError, TypeError):
        logger.exception(
            ('Ошибка при разборе JSON ответа от '
             f'{API_SETTINGS.ENDPOINTS["list"]}, ключ не найден.'))
        return False, []


@logger.catch
def get_hotel_details(hotel_id: str,
                      is_images_needed: bool = False,
                      image_limit=None) -> Tuple[bool, str, List]:
    '''
    Получение дополнительных сведений об отеле.
    Адресс отеля и список фотографий
    '''
    payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "en_US",
        "siteId": 300000001,
        "propertyId": hotel_id
    }

    is_request_complted, request_data = make_api_request(
        method_endswith=API_SETTINGS.ENDPOINTS['detail'],
        method_type='POST',
        json=payload,
        headers=API_SETTINGS.HEADERS | {"content-type": "application/json"},
        params=[]
    )
    if not is_request_complted:
        return False, '', []
    try:
        address = (request_data['data']
                   ['propertyInfo']
                   ['summary']
                   ['location']
                   ['address']
                   ['addressLine'])
    except (KeyError, TypeError):
        logger.exception(
            (f'Ошибка при разборе адресса JSON ответа '
             '{API_SETTINGS.ENDPOINTS["list"]}, ключ не найден.'))
        address = 'не найден'
    images_links = []
    if is_images_needed:
        try:
            images = (request_data['data']['propertyInfo']
                      ['propertyGallery']['images'][:image_limit])
            for item in images:
                images_links.append(item['image']['url'])
        except (KeyError, TypeError):
            logger.exception(
                ('Ошибка при разборе фотографий JSON ответа '
                 f'{API_SETTINGS.ENDPOINTS["list"]}, ключ не найден.'))
    return True, address, images_links


@logger.catch
def make_api_request(method_endswith: Dict,
                     method_type: str,
                     headers: Dict,
                     params: Dict,
                     json: Dict
                     ) -> Tuple[bool, Dict]:
    '''Выполнение запроса к API сервису сайта'''
    url = f"https://{config.RAPID_API_HOST}/{method_endswith}"
    if method_type == 'GET':
        return make_get_request(
            url=url,
            params=params,
            headers=headers
        )
    elif method_type == 'POST':
        return make_post_request(
            url=url,
            json=json,
            headers=headers
        )
    else:
        return False, {}


@logger.catch
def make_get_request(
        url: str,
        params: Dict,
        headers: Dict) -> Tuple[bool, Dict]:
    '''Выполнение GET запроса'''
    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=API_SETTINGS.TIMEOUT
        )
        if response.status_code == requests.codes.ok:
            logger.debug(
                (f'GET запрос {url} успешно выполнен. '
                 f'Получен код {response.status_code}'))
            return True, response.json()
        else:
            logger.error(
                ('Ошибка, не получен код успешного запроса. '
                 f'Получен {response.status_code} при GET запросe {url}'))
            return False, response.status_code
    except Exception as error:
        logger.exception(
            f'Ошибка при GET запросe {url} {error}')
        return False, {}


def make_post_request(
        url: str,
        json: Dict,
        headers: Dict
) -> Tuple[bool, Dict]:
    '''Выполнение POST запроса'''
    try:
        response = requests.post(
            url,
            headers=headers,
            json=json,
            timeout=API_SETTINGS.TIMEOUT
        )
        if response.status_code == requests.codes.ok:
            logger.debug(
                (f'POST запрос {url} успешно выполнен. '
                 f'Получен код {response.status_code}'))
            return True, response.json()
        else:
            logger.debug(
                ('Ошибка, не получен код успешного запроса.'
                 f'Получен {response.status_code} при POST запросe {url}'))
            return False, {}
    except Exception as error:
        logger.exception(
            f'Ошибка при POST запросe {url}\n{error}')
        return False, {}
