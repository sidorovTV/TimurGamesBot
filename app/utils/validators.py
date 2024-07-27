import re
from datetime import datetime, time, date

def is_valid_age(age: str) -> bool:
    return age.isdigit() and 0 < int(age) < 120


def is_valid_russian_name(name: str) -> bool:
    # Проверяем, что имя состоит только из русских букв, дефиса и пробелов
    # Минимальная длина имени - 2 символа
    pattern = r'^[а-яА-ЯёЁ\s-]{2,}$'
    return bool(re.match(pattern, name))

def is_valid_date(date_string: str) -> bool:
    try:
        # Пытаемся преобразовать строку в объект date
        input_date = datetime.strptime(date_string, "%Y-%m-%d").date()

        # Проверяем, что дата не в прошлом
        return input_date >= date.today()
    except ValueError:
        # Если возникла ошибка при преобразовании, значит формат неверный
        return False


def is_valid_time(time_string: str) -> bool:
    # Проверяем формат ЧЧ:ММ с помощью регулярного выражения
    if not re.match(r'^\d{2}:\d{2}$', time_string):
        return False

    try:
        # Пытаемся преобразовать строку в объект time
        input_time = datetime.strptime(time_string, "%H:%M").time()
        return True
    except ValueError:
        # Если возникла ошибка при преобразовании, значит время некорректное
        return False