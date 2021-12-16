import os
import json
import requests
import time
import telebot

from datetime import date
from dotenv import load_dotenv
from typing import Dict
from telebot import types
from telebot.types import InputMediaPhoto

from src.settings import logger

load_dotenv()

KEY_GET_HOTELS = os.getenv('KEY_GET_HOTELS')
KEY_GET_HOTELS_INFO = os.getenv('KEY_GET_HOTELS_INFO')
KEY_GET_HOTELS_FOTO = os.getenv('KEY_GET_HOTELS_FOTO')


def start_search(bot: telebot, message: telebot.types.Message, user_dict: Dict) -> None:
    """Функция старта команды. Запрашивает у пользователя город, в котором расположен отель"""

    bot.send_message(message.from_user.id, 'В каком городе будем осуществлять поиск по команде /bestdeal\n'
                                           'Пример ввода русских городов: Moscow Russia или moscow Russia\n'
                                           'Пример ввода иностранных городов: London или london')
    bot.register_next_step_handler(message, get_city, bot, user_dict)


def get_city(message: telebot.types.Message, bot: telebot, user_dict: Dict) -> None:
    """Функция, которая по названию города делает запрос на API и записывает
    полученный результат destinationId в User_dict"""

    try:
        if message.text.isalpha() or len(message.text.split()) == 2 and message.text.split()[0].isalpha() \
                and message.text.split()[1].isalpha():
            user_dict[message.chat.id]['city'] = message.text
            url = 'https://hotels4.p.rapidapi.com/locations/v2/search'
            querystring = {'query': message.text,
                           'locale': 'en_US',
                           'currency': 'USD'
                           }

            headers = {
                'x-rapidapi-host': 'hotels4.p.rapidapi.com',
                'x-rapidapi-key': KEY_GET_HOTELS
            }

            req_hotels_2 = requests.request('GET', url, headers=headers, params=querystring, timeout=10)
            dict_hotels_id = json.loads(req_hotels_2.text)

            if dict_hotels_id['moresuggestions'] != 0:
                hotel_destinationId = dict_hotels_id['suggestions'][0]['entities'][0]['destinationId']
                user_dict[message.chat.id]['hotel_destinationId'] = hotel_destinationId

                chekIn_hotel(message, bot, user_dict)
            else:
                raise Exception
        else:
            raise Exception
    except Exception as ex:
        logger.debug('Command: {command} Name func: {func} error name: {ex}'.
                     format(command=user_dict[message.chat.id]['command'], func=get_city.__name__, ex=ex))

        bot.send_message(message.from_user.id, 'Город введен неверно, введите город согласно интрукции')
        bot.register_next_step_handler(message, get_city, bot, user_dict)


def chekIn_hotel(message: telebot.types.Message, bot: telebot, user_dict: Dict) -> None:
    """Функция, которая запрашивает у пользователя дату заезда в отель"""

    bot.send_message(message.from_user.id, 'Введите дату заезда в отель через (-)\n'
                                           'Пример ввода даты: 20-11-2021')
    bot.register_next_step_handler(message, chekOut_hotel, bot, user_dict)


def chekOut_hotel(message: telebot.types.Message, bot: telebot, user_dict: Dict) -> None:
    """Функция, которая запрашивает у пользователя дату выезда из отеля"""

    try:
        if len(message.text.split('-')) == 3 and 0 < int(message.text.split('-')[0]) <= 31 \
                and 0 < int(message.text.split('-')[1]) <= 12 and 0 < int(message.text.split('-')[2]) >= 2021:

            user_dict[message.chat.id]['chekIn'] = message.text
            bot.send_message(message.from_user.id, 'Введите дату выезда из отеля через (-)\n'
                                                   'Пример ввода даты: 28-11-2021')
            bot.register_next_step_handler(message, period_of_stay_hotel, bot, user_dict)
        else:
            raise Exception('date chekIn_hotel Error')
    except Exception as ex:
        logger.debug('Command: {command} Name func: {func} error name: {ex}'.
                     format(command=user_dict[message.chat.id]['command'], func=chekOut_hotel.__name__, ex=ex))

        bot.send_message(message.from_user.id, 'Дата введена некоректно, введите дату согласно интрукции')
        bot.register_next_step_handler(message, chekOut_hotel, bot, user_dict)


def period_of_stay_hotel(message: telebot.types.Message, bot: telebot, user_dict: Dict) -> None:
    """Функция, которая подсчитывает количесвто дней, которые пользователь проведет в отеле"""

    try:
        user_dict[message.chat.id]['chekOut'] = message.text

        if len(message.text.split('-')) == 3 and 0 < int(message.text.split('-')[0]) <= 31 \
                and 0 < int(message.text.split('-')[1]) <= 12 and 0 < int(message.text.split('-')[2]) >= 2021 \
                and user_dict[message.chat.id]['chekIn'] < user_dict[message.chat.id]['chekOut']:

            date_chek_in = user_dict[message.chat.id]['chekIn'].split('-')
            date_chek_out = user_dict[message.chat.id]['chekOut'].split('-')
            period_of_stay = date(int(date_chek_out[2]), int(date_chek_out[1]), int(date_chek_out[0])) - \
                             date(int(date_chek_in[2]), int(date_chek_in[1]), int(date_chek_in[0]))

            user_dict[message.chat.id]['period_of_stay'] = period_of_stay.days
            get_hotel_info(message, bot, user_dict)
        else:
            raise Exception('date chekOut_hotel Error')
    except Exception as ex:
        logger.debug('Command: {command} Name func: {func} error name: {ex}'.
                     format(command=user_dict[message.chat.id]['command'], func=period_of_stay_hotel.__name__, ex=ex))

        bot.send_message(message.from_user.id, 'Дата введена некоректно, введите дату согласно интрукции')
        bot.register_next_step_handler(message, period_of_stay_hotel, bot, user_dict)


def get_hotel_info(message: telebot.types.Message, bot: telebot, user_dict: Dict) -> None:
    """Функция, которая по destinationId запрашивает на API инфомрацию по отелям
    и передает полученный результат в виде словаря hotels_dict в функцию get_number_city()"""

    url = 'https://hotels4.p.rapidapi.com/properties/list'
    querystring = {'destinationId': user_dict[message.chat.id]['hotel_destinationId'],
                   'pageNumber': '1',
                   'pageSize': '25',
                   'checkIn:': time.strftime('%Y-%m-%d'),
                   'checkOut': time.strftime('%Y-%m-%d'),
                   'adults1': '1',
                   'sortOrder:': 'Price',
                   'locale:': 'en_US',
                   'currency:': 'USD'
                   }

    headers = {
        'x-rapidapi-host': 'hotels4.p.rapidapi.com',
        'x-rapidapi-key': KEY_GET_HOTELS_INFO
    }

    req_hotels = requests.request('GET', url, headers=headers, params=querystring, timeout=10)
    hotels = json.loads(req_hotels.text)
    hotels_dict = hotels['data']['body']['searchResults']['results']

    get_range_price(message, hotels_dict, bot, user_dict)


def get_range_price(message: telebot.types.Message, hotels_dict: Dict, bot: telebot, user_dict: Dict) -> None:
    """Функция, которая запрашивает у пользователя диапазон стоимости проживания,
            по которому необходимо осуществлять поиск отелей"""

    user_dict[message.chat.id]['hotels'] = hotels_dict
    bot.send_message(message.from_user.id, 'Введите диапазон стоимости проживания через (-)\n'
                                           'Пример ввода диапазона стоимости: 3-40')
    bot.register_next_step_handler(message, get_range_distance, bot, user_dict)


def get_range_distance(message: telebot.types.Message, bot: telebot, user_dict: Dict) -> None:
    """Функция, которая запрашивает у пользователя диапазон расстояния от центра города,
        по которому необходимо осуществлять поиск отелей"""

    try:
        if len(message.text.split('-')) == 2 and int(message.text.split('-')[0]) <= int(message.text.split('-')[1]):
            user_dict[message.chat.id]['range_price'] = message.text
            bot.send_message(message.from_user.id, 'Введите диапазон расстояния от центра города через (-)\n'
                                                   'Пример ввода расстояния от центра: 0-3')
            bot.register_next_step_handler(message, get_number_city, bot, user_dict)
        else:
            raise Exception('get_range_price Error')
    except Exception as ex:
        logger.debug('Command: {command} Name func: {func} error name: {ex}'.
                     format(command=user_dict[message.chat.id]['command'], func=get_range_distance.__name__, ex=ex))

        bot.send_message(message.from_user.id, 'Введенно некорректное значение, '
                                               'либо первое значение привышает второе веденное значение\n'
                                               'Введите значение согласно интрукции')
        bot.register_next_step_handler(message, get_range_distance, bot, user_dict)


def get_number_city(message: telebot.types.Message, bot: telebot, user_dict: Dict) -> None:
    """Функция, которая запрашивает у пользователя количество отелей,
    которое необходимо вывести в чат"""

    try:
        if len(message.text.split('-')) == 2 and int(message.text.split('-')[0]) <= int(message.text.split('-')[1]):
            user_dict[message.chat.id]['range_distance'] = message.text
            bot.send_message(message.from_user.id, 'Сколько вывести отелей с заданными параметрами в городе {city}\n'
                                                   'Примечание: Количество отелей не должно быть больше 25'.
                             format(city=user_dict[message.chat.id]['city']))
            bot.register_next_step_handler(message, get_foto, bot, user_dict)
        else:
            raise Exception('get_range_distance Error')
    except Exception as ex:
        logger.debug('Command: {command} Name func: {func} error name: {ex}'.
                     format(command=user_dict[message.chat.id]['command'], func=get_number_city.__name__, ex=ex))

        bot.send_message(message.from_user.id, 'Введенно некорректное значение, '
                                               'либо первое значение привышает второе веденное значение\n'
                                               'Введите значение согласно интрукции')
        bot.register_next_step_handler(message, get_number_city, bot, user_dict)


def get_foto(message: telebot.types.Message, bot: telebot, user_dict: Dict) -> None:
    """Функция, которая запрашивает у пользователя нужно ли выводить фотографии отелей"""

    try:
        if message.text.isalnum() and int(message.text) <= 25:
            user_dict[message.chat.id]['hotels_number'] = message.text
            with open('User_dict {chat_id}.json'.format(chat_id=message.chat.id), 'w') as file:
                json.dump(user_dict, file, indent=4)
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text='Да', callback_data='yes'))
            keyboard.add(types.InlineKeyboardButton(text='Нет', callback_data='no'))
            question = 'Отели выводить с фото?'
            bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)
        else:
            raise Exception('get_number_city Error')
    except Exception as ex:
        logger.debug('Command: {command} Name func: {func} error name: {ex}'.
                     format(command=user_dict[message.chat.id]['command'], func=get_foto.__name__, ex=ex))

        bot.send_message(message.from_user.id, 'Введенно некорректное значение, '
                                               'либо введенное значение привышает 25\n'
                                               'Введите значение согласно интрукции (кол-во <= 25)')
        bot.register_next_step_handler(message, get_foto, bot, user_dict)


def get_quantity_foto(message: telebot.types.Message, bot: telebot, user_dict: Dict) -> None:
    """Функция, которая запрашивает у пользователя количество фотографий отелей,
    которое необходимо вывести в чат"""

    bot.send_message(message.chat.id, 'Сколько фото отелей вывести\n'
                                      'Примечание: Количество фото не должно быть больше 10')
    bot.register_next_step_handler(message, get_city_price_and_foto, bot, user_dict)


def get_city_price_and_foto(message: telebot.types.Message, bot: telebot, user_dict: Dict) -> None:
    """Основная Функция для вывода информации по выбранным отелям и фотографий к ним,
    в данной функции производится сортировка словаря по выбранным параметрам, а
    также осуществляется вывод информации по отелям в чат"""

    user_dict[message.chat.id]['get_foto'] = ['yes']
    hotels_dict = user_dict[message.chat.id]['hotels']
    range_price = user_dict[message.chat.id]['range_price'].split('-')
    range_distance = user_dict[message.chat.id]['range_distance'].split('-')

    try:
        if message.text.isalnum() and int(message.text) <= 10:
            def filter_hotel(hotels_dict):
                if 'ratePlan' in hotels_dict:
                    i_distance = (hotels_dict['landmarks'][0]['distance']).split()
                    if int(range_price[0]) <= hotels_dict['ratePlan']['price']['exactCurrent'] <= int(range_price[1]) \
                            and int(range_distance[0]) <= float(i_distance[0]) <= int(range_distance[1]):
                        return True
                else:
                    return False

            hotel_dict_filter = list(filter(filter_hotel, hotels_dict))
            if len(hotel_dict_filter) < int(user_dict[message.chat.id]['hotels_number']):
                bot.send_message(message.chat.id, 'К сожалению по вашим параметрам, отелей нашлось '
                                                  'всего: {range}\n'.format(range=len(hotel_dict_filter)))

            hotel_dict_sorted = sorted(hotel_dict_filter, key=lambda elem: elem['ratePlan']['price']['exactCurrent'],
                                       reverse=False)

            for i_hotel in hotel_dict_sorted[:int(user_dict[message.chat.id]['hotels_number'])]:
                url = 'https://hotels4.p.rapidapi.com/properties/get-hotel-photos'
                querystring = {'id': i_hotel['id'],  # конкретный id отеля
                               }
                headers = {
                    'x-rapidapi-host': 'hotels4.p.rapidapi.com',
                    'x-rapidapi-key': KEY_GET_HOTELS_FOTO
                }

                req_hotels_foto = requests.request('GET', url, headers=headers, params=querystring, timeout=10)
                hotels_foto_dict = json.loads(req_hotels_foto.text)

                total_price = float(user_dict[message.chat.id]['period_of_stay']) * \
                              round(i_hotel['ratePlan']['price']['exactCurrent'], 0)

                bot.send_message(message.chat.id, 'Наименование отеля: \n{name}\n'
                                                  'адресс: {adress}\n'
                                                  'расстояние до центра: {distance_center}\n'
                                                  'общая стоимость путёвки: ${total_price}\n'
                                                  'цена за одну ночь: {price}\n'
                                                  'ссылка на отель: https://ru.hotels.com/ho{hotel_id}'.
                                 format(name=i_hotel['name'],
                                        adress=i_hotel['address']['streetAddress'],
                                        distance_center=i_hotel['landmarks'][0]['distance'],
                                        total_price=int(total_price),
                                        price=i_hotel['ratePlan']['price']['current'],
                                        hotel_id=i_hotel['id']), disable_web_page_preview=True)

                media_group = [InputMediaPhoto(i_foto_get['baseUrl'].format(size='z'))
                               for i_foto_get in hotels_foto_dict['hotelImages'][:int(message.text)]]
                bot.send_media_group(message.chat.id, media_group)

                write_history(i_hotel, message, total_price)
        else:
            raise Exception('get_quantity_foto Error')

    except Exception as ex:
        logger.debug('Command: {command} Name func: {func} error name: {ex}'.
                     format(command=user_dict[message.chat.id]['command'],
                            func=get_city_price_and_foto.__name__, ex=ex))

        bot.send_message(message.from_user.id, 'Введенно некорректное значение, '
                                               'либо введенное значение привышает 10\n'
                                               'Введите значение согласно интрукции (кол-во фото <= 10)')
        bot.register_next_step_handler(message, get_city_price_and_foto, bot, user_dict)


def get_city_price_none_foto(message: telebot.types.Message, bot: telebot, user_dict: Dict) -> None:
    """Основная Функция для вывода информации по выбранным отелям без фотографий,
       в данной функции производится сортировка словаря по выбранным параметрам, а
       также осуществляется вывод информации по отелям в чат"""

    user_dict[message.chat.id]['get_foto'] = ['yes']
    hotels_dict = user_dict[message.chat.id]['hotels']
    range_price = user_dict[message.chat.id]['range_price'].split('-')
    range_distance = user_dict[message.chat.id]['range_distance'].split('-')

    def filter_hotel(hotel_dict):
        if 'ratePlan' in hotel_dict:
            i_distance = (hotel_dict['landmarks'][0]['distance']).split()
            if int(range_price[0]) <= hotel_dict['ratePlan']['price']['exactCurrent'] <= int(range_price[1]) \
                    and int(range_distance[0]) <= float(i_distance[0]) <= int(range_distance[1]):
                return True
        else:
            return False

    hotel_dict_filter = list(filter(filter_hotel, hotels_dict))
    if len(hotel_dict_filter) < int(user_dict[message.chat.id]['hotels_number']):
        bot.send_message(message.chat.id, 'К сожалению по вашим параметрам, отелей нашлось '
                                          'всего: {range}\n'.format(range=len(hotel_dict_filter)))

    hotel_dict_sorted = sorted(hotel_dict_filter, key=lambda elem: elem['ratePlan']['price']['exactCurrent'],
                               reverse=False)

    for i_hotel in hotel_dict_sorted[:int(user_dict[message.chat.id]['hotels_number'])]:
        total_price = float(user_dict[message.chat.id]['period_of_stay']) * \
                      round(i_hotel['ratePlan']['price']['exactCurrent'], 0)

        bot.send_message(message.chat.id, 'Наименование отеля: \n{name}\n'
                                          'адресс: {adress}\n'
                                          'расстояние до центра: {distance_center}\n'
                                          'общая стоимость путёвки: ${total_price}\n'
                                          'цена за одну ночь: {price}\n'
                                          'ссылка на отель: https://ru.hotels.com/ho{hotel_id}'.
                         format(name=i_hotel['name'],
                                adress=i_hotel['address']['streetAddress'],
                                distance_center=i_hotel['landmarks'][0]['distance'],
                                total_price=int(total_price),
                                price=i_hotel['ratePlan']['price']['current'],
                                hotel_id=i_hotel['id']), disable_web_page_preview=True)

        write_history(i_hotel, message, total_price)


def write_history(i_hotel: Dict, message: telebot.types.Message, total_price: float) -> None:
    """Функция выполняет запись истории запросов  отелей пользователя в файл history {chat_id}.txt"""

    with open('history {chat_id}.txt'.format(chat_id=message.chat.id), 'a', encoding='utf-8') as history_file:
        history_file.write('\nНаименование отеля: \n{name}\n'.format(name=i_hotel['name']))
        history_file.write('адрес: {adress}\n'.format(adress=i_hotel['address']['streetAddress']))
        history_file.write('растояние от центра: {distance}\n'.format(distance=i_hotel['landmarks'][0]['distance']))
        history_file.write('общая стоимость путёвки: ${total_price}\n'.format(total_price=int(total_price)))
        history_file.write('цена за одну ночь: {price}\n'.format(price=i_hotel['ratePlan']['price']['current']))
        history_file.write('ссылка на отель: https://ru.hotels.com/ho{hotel_id}\n'.format(hotel_id=i_hotel['id']))