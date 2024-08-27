FROM python:3.9

# Установка tzdata и настройка часового пояса
RUN apt-get update && apt-get install -y tzdata
ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN mkdir /data
RUN mkdir /logs

# Определяем volume
VOLUME /data

# Установите зависимости
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Скопируйте код вашего бота в контейнер
COPY . .

# Установите переменные окружения
ENV PYTHONPATH=.

CMD ["python", "app/main.py"]