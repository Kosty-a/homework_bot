import os
from dotenv import load_dotenv
import logging
import exceptions
import requests
from telegram import Bot
import time


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
logger.addHandler(handler)
formater = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formater)

RETRY_PERIOD = 600
# RETRY_PERIOD = 10
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
        raise exceptions.EnvVarException('Environment variables: FAIL')


def send_message(bot, message):
    bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message
    )

def get_api_answer(timestamp):
    """Получение ответа от API."""
    payload = {'from_date': timestamp}
    try:
        api_answer = requests.get(ENDPOINT, headers=HEADERS, params=payload).json()
        logger.debug('API answer: OK')
        print(api_answer)
    except Exception:
        logger.error('API answer: FAIL')
        api_answer = None

    return api_answer


def check_response(response):
    """Проверка ответа API."""
    if response.get('code') == 'UnknownError':
        logger.error('from_date format: FAIL')
    elif response.get('code') == 'not_authenticated':
        logger.error('PRACTICUM_TOKEN: FAIL')
    else:
        logger.debug('Check API answer: OK')


def parse_status(homework):
    """Парсинг ответа API."""
    if not homework.get('homeworks'):
        return None
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    verdict = HOMEWORK_VERDICTS.get(status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""

    check_tokens()

    # Создаем объект класса бота
    bot = Bot(token=TELEGRAM_TOKEN)
    # timestamp = int(time.time())
    timestamp = int(time.time()) - 34 * 24 * 60 * 60

    while True:
        try:
            api_answer = get_api_answer(timestamp)
            if api_answer:
                check_response(api_answer)
                message = parse_status(api_answer)
                if message:
                    send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
