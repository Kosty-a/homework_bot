import logging
import os
import time

import requests
from dotenv import load_dotenv
from telegram import Bot

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
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправка сообщения в telegram."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logger.debug('Send message: OK')
    except Exception as error:
        logger.error(f'Send message: FAIL\n{error}')


def get_api_answer(timestamp):
    """Получение ответа от API."""
    payload = {'from_date': timestamp}
    try:
        api_answer = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        if api_answer.status_code == 200:
            api_answer = api_answer.json()
        else:
            raise exceptions.APIAnswerStatusCodeError()
    except exceptions.APIAnswerStatusCodeError:
        raise exceptions.APIAnswerStatusCodeError(
            'API answer status code: FAIL\n'
            f'params: {payload}\n'
            f'status_code: {api_answer.status_code}\n'
            f'content: {api_answer.json()}'
        )
    except Exception:
        raise exceptions.APIAnswerError('API answer: FAIL')

    return api_answer


def check_response(response):
    """Проверка ответа API."""
    if not isinstance(response, dict):
        raise TypeError('Check response is dict: FAIL')
    if 'homeworks' not in response:
        raise exceptions.CheckResponseHomeworkError(
            'Check response homework: FAIL'
        )
    if not isinstance(response['homeworks'], list):
        raise TypeError('Check response homework is list: FAIL')


def parse_status(homework):
    """Парсинг ответа API."""
    if homework_name := homework.get('homework_name'):
        status = homework.get('status')
        verdict = HOMEWORK_VERDICTS.get(status)
    else:
        raise exceptions.ParseStatusHomeworkNameError(
            'Homework name: FAIL'
        )
    if verdict:
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        raise exceptions.ParseStatusHomeworkStatusError(
            'Homework status: FAIL'
        )


def main():
    """Основная логика работы бота."""
    if check_tokens():
        logger.debug('Environment variables: OK')
    else:
        logger.critical('Environment variables: FAIL')
        exit()

    # Создаем объект класса бота
    bot = Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            api_answer = get_api_answer(timestamp)
            logger.debug('API answer: OK')
            check_response(api_answer)
            logger.debug('Check response: OK')
            if homework := api_answer.get('homeworks'):
                logger.debug('New homework status: YES')
                message = parse_status(homework[0])
                logger.debug('Parse status: OK')
                send_message(bot, message)
            else:
                logger.debug('New homework status: NO')
            timestamp = api_answer.get('current_date')
        except Exception as error:
            logger.error(error)
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
