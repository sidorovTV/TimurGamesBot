# Используйте базовый образ Python
FROM python:3.10-slim

RUN mkdir /data
RUN mkdir /logs


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