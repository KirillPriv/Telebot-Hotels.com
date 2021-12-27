import telebot
import os

from src.settings import logger


def get_history(bot: telebot, message: telebot.types.Message) -> None:

    """Основная функция которая выолняет вывод истории запросов пользователя
    из файла history {chat_id}.txt в чат бота"""

    try:
        if os.stat('history {chat_id}.txt'.format(chat_id=message.chat.id)).st_size == 0:
            bot.send_message(message.chat.id, 'История запросов пока пуста. Попробуйте позже')
        else:
            with open('history {chat_id}.txt'.format(chat_id=message.chat.id), 'r', encoding='utf-8') as history:
                bot.send_message(message.chat.id, 'История запросов пользователя:\n{history}'.
                                 format(history=history.read()))
    except FileNotFoundError as ex:
        logger.debug('Command: {command} Name func: {func} error name: {ex}'.
                     format(command='history', func=get_history.__name__, ex=ex))
        bot.send_message(message.chat.id, 'История запросов пока пуста. Попробуйте позже')
    except Exception as ex:
        logger.debug('Command: {command} Name func: {func} error name: {ex}'.
                     format(command='history', func=get_history.__name__, ex=ex))
        bot.send_message(message.chat.id, 'История запросов слишком велика. Необходимо отчистить историю')
        bot.send_message(message.chat.id, 'Очистить историю? да/нет?')
        bot.register_next_step_handler(message, clean_history, bot)


def clean_history(message: telebot.types.Message, bot: telebot) -> None:
    if message.text.lower() == 'да':
        with open('history {chat_id}.txt'.format(chat_id=message.chat.id), 'w', encoding='utf-8') as history:
            history.write('')
        bot.send_message(message.chat.id, 'История запросов очищена!')
    else:
        bot.send_message(message.chat.id, 'История запросов будет недоступна, очистите историю и повторитет запрос!')
