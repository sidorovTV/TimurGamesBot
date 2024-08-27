# Используйте базовый образ Python
FROM python:3.10-slim

# Установка необходимых пакетов
RUN apt-get update && apt-get install -y tzdata

# Установка часового пояса
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
ENV BOT_TOKEN=7207580139:AAGD32zSX_e6EWAI5kaFEoj0CMuywZ5nMBg
ENV ADMIN_USER_ID=795051614


# Запустите приложение
CMD ["python", "app/main.py"]