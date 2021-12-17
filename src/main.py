import os
import datetime
import json
import telebot

from dotenv import load_dotenv

from bot_requests import lowprice
from bot_requests import highprice
from bot_requests import bestdeal
from bot_requests import history

load_dotenv()

BOT_TOKEN = os.getenv('BOT_Token')
bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(content_types=['text'])
def get_start_message(message: telebot.types.Message) -> None:
    """Стартовая функция. Выыодит список комананд, и делает запрос у пользователя какую команду вывести"""
    if message.text == '/start' or message.text == 'Привет' or message.text == 'привет' or message.text == 'Hello word':
        bot.send_message(message.from_user.id, "Привет, я твой помощник в поиске подходящего отеля\n"
                                               "Для начала работы напиши одну из команд:\n"
                                               "/help - вывод меню помощи\n"
                                               "/lowprice  - вывод отелей с самой низкой ценой\n"
                                               "/highprice - вывод отелей с максимальной ценой\n"
                                               "/bestdeal - вывод отелей по заданным параметрам цена и удаленность от центра\n"
                                               "/history - вывод истории запросов\n")
        bot.register_next_step_handler(message, get_comannd_message)
    else:
        bot.send_message(message.from_user.id, 'Я тебя не понимаю. Напиши /help.')
        bot.register_next_step_handler(message, get_comannd_message)


def get_comannd_message(message: telebot.types.Message) -> None:
    """Функция осуществляет работу команд в зависмости от выбора пользователя.
    Записывает в файл history {chat_id}.txt дату и время ввода выбранной команды, а также
    передает в функцию start_search() bot и message"""

    user_dict = dict()

    if message.text == '/help':
        user_dict[message.chat.id] = {'command': message.text}
        bot.send_message(message.from_user.id, 'Чтобы начать работу бота напишите /start\n'
                                               'Команды, которые умеет выполнять этот бот:\n'
                                               '\n/lowprice - команда для запуска поиска отелей с минимальными ценами, '
                                               'начинает работу после ввода команды /start\n'
                                               '\n/highprice - команда для запуска поиска отелей с максимальными ценами, '
                                               'начинает работу после ввода команды /start\n'
                                               '\n/bestdeal - команда для запуска поиска отелей '
                                               'c лучшим предложением по заданным параметрам '
                                               '(цена, удаленность от центра города), '
                                               'начинает работу после ввода команды /start\n'
                                               '\n/history - команда для вывода истории запросов пользователя, '
                                               'начинает работу после ввода команды /start\n')
        bot.register_next_step_handler(message, get_start_message)

    elif message.text == '/lowprice':
        user_dict[message.chat.id] = {'command': message.text}
        with open('history {chat_id}.txt'.format(chat_id=message.chat.id), 'a', encoding='utf-8') as history_file:
            history_file.write('\nКоманда, которую вводил пользователь:/lowprice\n')
            history_file.write('Дата и время ввода команды: {time}\n'.
                               format(time=datetime.datetime.now().replace(microsecond=0)))
        lowprice.start_search(bot, message, user_dict)

    elif message.text == '/highprice':
        user_dict[message.chat.id] = {'command': message.text}
        with open('history {chat_id}.txt'.format(chat_id=message.chat.id), 'a', encoding='utf-8') as history_file:
            history_file.write('\nКоманда, которую вводил пользователь:/highprice\n')
            history_file.write('Дата и время ввода команды: {time}\n'.
                               format(time=datetime.datetime.now().replace(microsecond=0)))
        highprice.start_search(bot, message, user_dict)

    elif message.text == '/bestdeal':
        user_dict[message.chat.id] = {'command': message.text}
        with open('history {chat_id}.txt'.format(chat_id=message.chat.id), 'a', encoding='utf-8') as history_file:
            history_file.write('\nКоманда, которую вводил пользователь:/bestdeal\n')
            history_file.write('Дата и время ввода команды: {time}\n'.
                               format(time=datetime.datetime.now().replace(microsecond=0)))
        bestdeal.start_search(bot, message, user_dict)

    elif message.text == '/history':
        user_dict[message.chat.id] = {'command': message.text}
        history.get_history(bot, message)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call) -> None:
    """ Обработка запроса необходимости вывода фото отелей с помощью кнопок"""

    with open('User_dict {chat_id}.json'.format(chat_id=call.message.chat.id), 'r') as file:
        user_dict = json.loads(file.read())

    user_dict = {int(key): dict for key, dict in user_dict.items()}

    if call.data == "yes":
        if user_dict[call.message.chat.id]['command'] == '/lowprice':
            lowprice.get_quantity_photo(call.message, bot, user_dict)
        elif user_dict[call.message.chat.id]['command'] == '/highprice':
            highprice.get_quantity_photo(call.message, bot, user_dict)
        elif user_dict[call.message.chat.id]['command'] == '/bestdeal':
            bestdeal.get_quantity_photo(call.message, bot, user_dict)
    else:
        if user_dict[call.message.chat.id]['command'] == '/lowprice':
            lowprice.get_city_price_none_photo(call.message, bot, user_dict)
        elif user_dict[call.message.chat.id]['command'] == '/highprice':
            highprice.get_city_price_none_photo(call.message, bot, user_dict)
        elif user_dict[call.message.chat.id]['command'] == '/bestdeal':
            bestdeal.get_city_price_none_photo(call.message, bot, user_dict)

bot.polling(none_stop=True, interval=0)
