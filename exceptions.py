class EnvVarError(Exception):
    """ОШИБКА: отсутствует переменная(-ые) окружения."""

    pass


class APIAnswerStatusCodeError(Exception):
    """ОШИБКА: статус-код не 200."""

    pass


class ParseStatusHomeworkStatusError(Exception):
    """ОШИБКА: неправильный статус домашней работы."""

    pass


class ParseStatusHomeworkNameError(Exception):
    """ОШИБКА: нет ключа homework_name."""

    pass


class CheckResponseHomeworkError(Exception):
    """ОШИБКА: в ответе нет ключа homeworks."""

    pass
