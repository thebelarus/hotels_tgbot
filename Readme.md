# Hotels Bot

Телеграм бот, с помощью него можно получать информацию об отелях, расположенных по всему миру используя сервис Hotels(hotels.com) Rapid Api.

## Используемые технологии

- Python (3.10);
- PyTelegramBotApi;
- Python telegram bot calendar;
- python telegram bot pagination;
- Peewee;
- Loguru;

## Установка

Необходимо скопировать все содержимое репозитария в отдельный каталог.

Установить все библиотеки из файла `requirements.txt`
с помощью команды `pip install -r requirements.txt`

Файл `.env.template` переименовать в `.env`. Открыть и заполнить необходимыми данными.
`BOT_TOKEN`: токен для бота, полученный от @BotFather"
`RAPID_API_KEY`: ключ полученный от API по адресу rapidapi.com/apidojo/api/hotels4/"
`RAPID_API_HOST`: домен API сервиса данных, например hotels4.p.rapidapi.com

## Запуск

Запустить файл `main.py`.
