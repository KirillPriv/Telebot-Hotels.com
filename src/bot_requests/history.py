import telebot
import datetime
from loguru import logger

def get_history(bot: telebot, message: telebot.types.Message) -> None:

    """Основная функция которая выолняет вывод истории запросов пользователя
    из файла history {chat_id}.txt в чат бота"""

    try:
        with open('history {chat_id}.txt'.format(chat_id=message.chat.id), 'r', encoding='utf-8') as history:
            bot.send_message(message.chat.id, 'История запросов пользователя:\n{history}'.
                             format(history=history.read()))
    except FileNotFoundError as ex:
        logger.add('errors id{chat_id}.log'.format(chat_id=message.chat.id), level='DEBUG',
                   format='{time} {level} {message}', rotation='9:00', compression='zip')
        logger.debug('Command: {command} Name func: {func} error name: {ex}'.
                     format(command='history', func=get_history.__name__, ex=ex))
        bot.send_message(message.chat.id, 'История запросов пока пуста. Попробуйте позже')
