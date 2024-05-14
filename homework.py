import logging
import os
import time

import requests
import telebot
from dotenv import load_dotenv

import exceptions
from custom_formatter import CustomFormatter

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
logger.addHandler(handler)
handler.setFormatter(CustomFormatter())

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка наличия необходимых переменных оружения."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        logger.debug('Environment variables: OK')
    else:
        logger.critical('Environment variables: FAIL')
        raise exceptions.EnvVarError('Environment variables: FAIL')


def send_message(bot, message):
    """Отправка сообщения в telegram."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logger.debug('Send message: OK')
    except Exception:
        logger.error('Send message: FAIL')


def get_api_answer(timestamp):
    """Получение ответа от API."""
    payload = {'from_date': timestamp}
    try:
        api_answer = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        if api_answer.status_code == 200:
            api_answer = api_answer.json()
            logger.debug('API answer: OK')
        else:
            logger.error('API answer status code: FAIL')
            raise exceptions.APIAnswerStatusCodeError()
    except exceptions.APIAnswerStatusCodeError:
        raise exceptions.APIAnswerStatusCodeError(
            'API answer status code: FAIL'
        )
    except Exception:
        logger.error('API answer: FAIL')
        raise Exception('API answer: FAIL')

    return api_answer


def check_response(response):
    """Проверка ответа API."""
    if type(response) is not dict:
        logger.error('Check response is dict: FAIL')
        raise TypeError('Check response is dict: FAIL')
    try:
        homeworks = response['homeworks']
    except KeyError:
        logger.error('Check response homework: FAIL')
        raise exceptions.CheckResponseHomeworkError(
            'Check response homework: FAIL'
        )
    if type(homeworks) is not list:
        logger.error('Check response homework is list: FAIL')
        raise TypeError('Check response homework is list: FAIL')
    logger.debug('Check response: OK')


def parse_status(homework):
    """Парсинг ответа API."""
    if homework_name := homework.get('homework_name'):
        status = homework.get('status')
        verdict = HOMEWORK_VERDICTS.get(status)
    else:
        logger.error('Homework name: FAIL')
        raise exceptions.ParseStatusHomeworkNameError(
            'Homework name: FAIL'
        )
    if verdict:
        logger.debug('Parse status: OK')
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        logger.error('Homework status: FAIL')
        raise exceptions.ParseStatusHomeworkStatusError(
            'Homework status: FAIL'
        )


def main():
    """Основная логика работы бота."""
    check_tokens()

    # Создаем объект класса бота
    bot = telebot.TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            api_answer = get_api_answer(timestamp)
            check_response(api_answer)
            if homework := api_answer.get('homeworks'):
                message = parse_status(homework[0])
                send_message(bot, message)
            else:
                logger.debug('New homework status: NO')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
