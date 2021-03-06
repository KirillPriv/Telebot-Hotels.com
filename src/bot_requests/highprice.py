import os
import json
import requests
import time
import datetime
import telebot
import re

from dotenv import load_dotenv
from typing import Dict
from telebot import types
from datetime import date
from telebot.types import InputMediaPhoto

from src.settings import logger

load_dotenv()

KEY_GET_HOTELS = os.getenv('KEY_GET_HOTELS')
KEY_GET_HOTELS_INFO = os.getenv('KEY_GET_HOTELS_INFO')
KEY_GET_HOTELS_FOTO = os.getenv('KEY_GET_HOTELS_FOTO')


def start_search(bot: telebot, message: telebot.types.Message, user_dict: Dict) -> None:
    """Функция старта команды. Запрашивает у пользователя город, в котором расположен отель"""

    bot.send_message(message.from_user.id, 'В каком городе будем осуществлять поиск по команде /highprice\n'
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

            req_hotels_2 = requests.request('GET', url, headers=headers, params=querystring, timeout=30)
            dict_hotels_id = json.loads(req_hotels_2.text)

            result_city = [re.findall(r'\w+', i_town['caption']) if '<span' in i_town['caption']
                           else i_town['caption']
                           for i_town in dict_hotels_id['suggestions'][0]['entities']]
            for word_list in result_city:
                if 'span' in word_list and 'class' in word_list and 'highlighted' in word_list:
                    word_list.remove('span')
                    word_list.remove('class')
                    word_list.remove('span')
                    word_list.remove('highlighted')

            if dict_hotels_id['moresuggestions'] != 0:
                user_dict[message.chat.id]['dict_town'] = dict_hotels_id
                with open('User_dict {chat_id}.json'.format(chat_id=message.chat.id), 'w') as file:
                    json.dump(user_dict, file, indent=4)

                keyboard = types.InlineKeyboardMarkup()
                if len(dict_hotels_id['suggestions'][0]['entities']) > 0:
                    for i_index in range(0, len(dict_hotels_id['suggestions'][0]['entities'])):
                        keyboard.add(types.InlineKeyboardButton(text='{city_name}'.
                                                                format(city_name=result_city[i_index]),
                                                                callback_data=str(i_index)))
                else:
                    raise Exception('len(dict_hotels_id[suggestions][0][entities]) == 0')

                question = 'Уточните пожалуйста город из списка, в котором осуществляем поиск?'
                bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)
            else:
                raise Exception('moresuggestions == 0')
        else:
            raise Exception
    except Exception as ex:
        logger.debug('Command: {command} Name func: {func} error name: {ex}'.
                     format(command =user_dict[message.chat.id]['command'], func=get_city.__name__, ex=ex))

        bot.send_message(message.from_user.id, 'Город введен неверно, введите город согласно интрукции')
        bot.register_next_step_handler(message, get_city, bot, user_dict)


def chek_in_hotel(message: telebot.types.Message, bot: telebot, user_dict: Dict) -> None:
    """Функция, которая запрашивает у пользователя дату заезда в отель"""

    bot.send_message(message.chat.id, 'Введите дату заезда в отель через (-)\n'
                                           'Пример ввода даты: 20-11-2021\n'
                                           'Примечание: дата въезда не может быть меньше текущей даты')
    bot.register_next_step_handler(message, chek_out_hotel, bot, user_dict)


def chek_out_hotel(message: telebot.types.Message, bot: telebot, user_dict: Dict) -> None:
    """Функция, которая запрашивает у пользователя дату выезда из отеля"""

    try:
        if len(message.text.split('-')) == 3 and 0 < int(message.text.split('-')[0]) <= 31 \
                and 0 < int(message.text.split('-')[1]) <= 12 and 0 < int(message.text.split('-')[2]) >= 2021 \
                and int(message.text.split('-')[0] >= time.strftime('%d-%m-%Y').split('-')[0]) \
                and int(message.text.split('-')[1] >= time.strftime('%d-%m-%Y').split('-')[1]) \
                and int(message.text.split('-')[2] >= time.strftime('%d-%m-%Y').split('-')[2]):

            user_dict[message.chat.id]['chekIn'] = message.text
            bot.send_message(message.from_user.id, 'Введите дату выезда из отеля через (-)\n'
                                                   'Пример ввода даты: 28-11-2021\n'
                                                   'Примечание: дата выезда должна быть выше даты въезда')
            bot.register_next_step_handler(message, period_of_stay_hotel, bot, user_dict)
        else:
            raise Exception('date chek_in_hotel Error')
    except Exception as ex:
        logger.debug('Command: {command} Name func: {func} error name: {ex}'.
                     format(command=user_dict[message.chat.id]['command'], func=chek_out_hotel.__name__, ex=ex))

        bot.send_message(message.from_user.id, 'Дата введена некоректно, введите дату согласно интрукции')
        bot.register_next_step_handler(message, chek_out_hotel, bot, user_dict)


def period_of_stay_hotel(message: telebot.types.Message, bot: telebot, user_dict: Dict) -> None:
    """Функция, которая подсчитывает количесвто дней, которые пользователь проведет в отеле"""

    user_dict[message.chat.id]['chekOut'] = message.text

    date_chek_in = user_dict[message.chat.id]['chekIn'].split('-')
    date_chek_out = user_dict[message.chat.id]['chekOut'].split('-')

    try:
        if len(message.text.split('-')) == 3 and 0 < int(message.text.split('-')[0]) <= 31 \
                and 0 < int(message.text.split('-')[1]) <= 12 and 0 < int(message.text.split('-')[2]) >= 2021 \
                and datetime.datetime(int(date_chek_out[2]), int(date_chek_out[1]), int(date_chek_out[0])) > \
                datetime.datetime(int(date_chek_in[2]), int(date_chek_in[1]), int(date_chek_in[0])):

            period_of_stay = date(int(date_chek_out[2]), int(date_chek_out[1]), int(date_chek_out[0])) - \
                             date(int(date_chek_in[2]), int(date_chek_in[1]), int(date_chek_in[0]))

            user_dict[message.chat.id]['period_of_stay'] = period_of_stay.days
            get_hotel_info(message, bot, user_dict)
        else:
            raise Exception('date chek_out_hotel Error')
    except Exception as ex:
        logger.debug('Command: {command} Name func: {func} error name: {ex}'.
                     format(command=user_dict[message.chat.id]['command'], func=period_of_stay_hotel.__name__, ex=ex))

        bot.send_message(message.from_user.id, 'Дата введена некоректно, введите дату согласно интрукции')
        bot.register_next_step_handler(message, period_of_stay_hotel, bot, user_dict)


def get_hotel_info(message: telebot.types.Message, bot: telebot, user_dict: Dict) -> None:
    """Функция, которая по destinationId запрашивает на API инфомрацию по отелям
    и передает полученный результат в виде словаря hotels_dict в функцию get_number_city()"""

    date_chek_in = user_dict[message.chat.id]['chekIn']
    date_chek_out = user_dict[message.chat.id]['chekOut']

    url = 'https://hotels4.p.rapidapi.com/properties/list'
    querystring = {'destinationId': user_dict[message.chat.id]['hotel_destinationId'],
                   'pageNumber': '1',
                   'pageSize': '25',
                   'checkIn:': '-'.join(reversed(date_chek_in.split('-'))),
                   'checkOut': '-'.join(reversed(date_chek_out.split('-'))),
                   'adults1': '1',
                   'sortOrder:': 'Price',
                   'locale:': 'en_US',
                   'currency:': 'USD'
                   }

    headers = {
        'x-rapidapi-host': 'hotels4.p.rapidapi.com',
        'x-rapidapi-key': KEY_GET_HOTELS_INFO
    }

    req_hotels = requests.request('GET', url, headers=headers, params=querystring, timeout=30)
    try:
        hotels = json.loads(req_hotels.text)
        hotels_dict = hotels['data']['body']['searchResults']['results']

        get_number_city(message, hotels_dict, bot, user_dict)
    except Exception as ex:
        logger.debug('Command: {command} Name func: {func} error name: {ex}'.
                     format(command=user_dict[message.chat.id]['command'], func=get_hotel_info.__name__, ex=ex))

        bot.send_message(message.from_user.id, 'Ответ сервера некорректен, начните запрос по команде заново!')
        start_search(bot, message, user_dict)


def get_number_city(message: telebot.types.Message, hotels_dict: Dict, bot: telebot, user_dict: Dict) -> None:
    """Функция, которая запрашивает у пользователя количество отелей,
    которое необходимо вывести в чат"""

    user_dict[message.chat.id]['hotels'] = hotels_dict
    bot.send_message(message.from_user.id, 'Сколько вывести отелей с максимальми ценами в городе {city}\n'
                                           'Примечание: Количество отелей не должно быть больше 25'.
                     format(city=user_dict[message.chat.id]['city']))
    bot.register_next_step_handler(message, get_photo, bot, user_dict)


def get_photo(message: telebot.types.Message, bot: telebot, user_dict: Dict) -> None:
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
                     format(command=user_dict[message.chat.id]['command'], func=get_photo.__name__, ex=ex))

        bot.send_message(message.from_user.id, 'Введенно некорректное значение, '
                                               'либо введенное значение привышает 25\n'
                                               'Введите значение согласно интрукции (кол-во <= 25)')
        bot.register_next_step_handler(message, get_photo, bot, user_dict)


def get_quantity_photo(message: telebot.types.Message, bot: telebot, user_dict: Dict) -> None:
    """Функция, которая запрашивает у пользователя количество фотографий отелей,
    которое необходимо вывести в чат"""

    bot.send_message(message.chat.id, 'Сколько фото отелей вывести\n'
                                      'Примечание: Количество фото не должно быть больше 10')
    bot.register_next_step_handler(message, get_city_price_and_photo, bot, user_dict)


def get_city_price_and_photo(message: telebot.types.Message, bot: telebot, user_dict: Dict) -> None:
    """Основная Функция для вывода информации по выбранным отелям и фотографий к ним,
    в данной функции производится сортировка словаря по ценам, а
    также осуществляется вывод информации по отелям в чат"""

    user_dict[message.chat.id]['get_photo'] = ['yes']
    hotels_dict = user_dict[message.chat.id]['hotels']

    try:
        if message.text.isalnum() and int(message.text) <= 10:
            def filter_key(hotel_dict: Dict) -> True or False:
                """Функция фильтрации словаря по указанному ключу
                :return True or False
                """
                if 'ratePlan' in hotel_dict:
                    return True
                else:
                    return False

            hotel_dict_filter = list(filter(filter_key, hotels_dict))
            hotel_dict_sorted = sorted(hotel_dict_filter,
                                       key=lambda elem: elem['ratePlan']['price']['exactCurrent'], reverse=True)

            for i_hotel in hotel_dict_sorted[:int(user_dict[message.chat.id]['hotels_number'])]:
                url_4 = 'https://hotels4.p.rapidapi.com/properties/get-hotel-photos'
                querystring_4 = {'id': i_hotel['id'],  # конкретный id отеля
                                 }

                headers_4 = {
                    'x-rapidapi-host': 'hotels4.p.rapidapi.com',
                    'x-rapidapi-key': KEY_GET_HOTELS_FOTO
                }

                req_hotels_photo = requests.request('GET', url_4, headers=headers_4, params=querystring_4, timeout=30)
                hotels_photo_dict = json.loads(req_hotels_photo.text)

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

                media_group = [InputMediaPhoto(i_photo_get['baseUrl'].format(size='z'))
                               for i_photo_get in hotels_photo_dict['hotelImages'][:int(message.text)]]
                bot.send_media_group(message.chat.id, media_group)

                write_history(i_hotel, message, total_price)
        else:
            raise Exception('get_quantity_photo Error')
    except Exception as ex:
        logger.debug('Command: {command} Name func: {func} error name: {ex}'.
                     format(command=user_dict[message.chat.id]['command'], func=get_city_price_and_photo.__name__, ex=ex))

        bot.send_message(message.from_user.id, 'Введенно некорректное значение, '
                                               'либо введенное значение привышает 10\n'
                                               'Введите значение согласно интрукции (кол-во фото <= 10)')
        bot.register_next_step_handler(message, get_city_price_and_photo, bot, user_dict)


def get_city_price_none_photo(message: telebot.types.Message, bot: telebot, user_dict: Dict) -> None:
    """Основная Функция для вывода информации по выбранным отелям без фотографий,
       в данной функции производится сортировка словаря по ценам, а
       также осуществляется вывод информации по отелям в чат"""

    user_dict[message.chat.id]['get_photo'] = ['no']
    hotels_dict = user_dict[message.chat.id]['hotels']

    def filter_key(hotel_dict):
        if 'ratePlan' in hotel_dict:
            return True
        else:
            return False

    hotel_dict_filter = list(filter(filter_key, hotels_dict))
    hotel_dict_sorted = sorted(hotel_dict_filter,
                               key=lambda elem: elem['ratePlan']['price']['exactCurrent'], reverse=True)

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
