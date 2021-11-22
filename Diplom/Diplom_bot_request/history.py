import telebot


def get_history(bot: telebot, message: telebot.types.Message) -> None:

    """Основная функция которая выолняет вывод истории запросов пользователя
    из файла history {chat_id}.txt в чат бота"""

    try:
        with open('history {chat_id}.txt'.format(chat_id=message.chat.id), 'r', encoding='utf-8') as history:
            bot.send_message(message.chat.id, 'История запросов пользователя:\n{history}'.
                             format(history=history.read()))
    except FileNotFoundError:
        bot.send_message(message.chat.id, 'История запросов пока пуста. Попробуйте позже')
