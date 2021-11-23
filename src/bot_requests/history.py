import telebot
import datetime


def get_history(bot: telebot, message: telebot.types.Message) -> None:

    """Основная функция которая выолняет вывод истории запросов пользователя
    из файла history {chat_id}.txt в чат бота"""

    try:
        with open('history {chat_id}.txt'.format(chat_id=message.chat.id), 'r', encoding='utf-8') as history:
            bot.send_message(message.chat.id, 'История запросов пользователя:\n{history}'.
                             format(history=history.read()))
    except FileNotFoundError as ex:
        with open('errors id{chat_id}.log'.format(chat_id=message.chat.id), 'a', encoding='utf-8') as erros_log:
            erros_log.write('\nИмя функции: {func}\n'.format(func=get_history.__name__))
            erros_log.write('Вызвана ошибка: {traceback}'.format(traceback=ex))
            erros_log.write('Время ошибки: {time}\n'.format(time=datetime.datetime.now().replace(microsecond=0)))
        bot.send_message(message.chat.id, 'История запросов пока пуста. Попробуйте позже')
