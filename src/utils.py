import json
import logging
import os
from datetime import datetime
from os import getcwd
from os.path import dirname, exists

import pandas as pd
import requests
from dotenv import load_dotenv
from pandas import DataFrame

load_dotenv()
API_KEY_CURRENCY = os.getenv("API_KEY_CURRENCY")
API_KEY_STOCK = os.getenv("API_KEY_STOCK")
PATH_LOG = dirname(getcwd())


logging.basicConfig(
    encoding="utf-8",
    filemode="w",
    filename=PATH_LOG + r"\logs\utils.log",
    format="%(asctime)s:%(filename)s:%(funcName)s %(levelname)s: %(message)s",
    level=logging.DEBUG,
)

logger = logging.getLogger("utils")


def get_greetings() -> str:
    """Функция печатает Приветствие — «Доброе утро» / «Добрый день» / «Добрый вечер» / «Доброй ночи»
    в зависимости от текущего времени"""

    greetings = "Добр"
    logger.info("Определение текущего времени")
    time_now = datetime.now().time().strftime("%H:%M:%S")
    if "00:00:00" < time_now < "06:00:00":
        greetings += "ой ночи"
    elif "06:00:00" <= time_now < "12:00:00":
        greetings += "ое утро"
    elif "12:00:00" <= time_now < "18:00:00":
        greetings += "ый день"
    else:
        greetings += "ый вечер"
    logger.info("Вывод приветствия")

    return greetings


def export_data_from_xlsx(file_name: str) -> DataFrame | str:
    """Функция считывание финансовых операций из XLSX-файла"""
    logger.info("Проверка существования xlsx-файла")
    if not exists(file_name):
        logger.info("Файл не найден")
        return "Файл не найден"
    try:
        logger.info("Считывание информации из xlsx-файла")
        reader = pd.read_excel(file_name)
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        return "Ошибка чтения файла"
    else:
        return reader


def filter_by_date_range(df: DataFrame, date: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")) -> DataFrame | str:
    """Фильтрует данные с начала месяца, на который выпадает входящая дата,
    по входящую дату (по умолчанию берется текущая дата)."""
    try:
        logger.info("Удаляем значения nan из столбца 'Дата операции'")
        df["Дата операции"].dropna(inplace=True)

        logger.info("Преобразуем дату в формат %Y-%m-%d")
        date_obj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        logger.info("Определяем начало месяца")
        start_date = date_obj.replace(day=1, hour=0, minute=0, second=0)

        logger.info(
            "Преобразовываем столбец с датами в объект datetime" " и фильтруем данные по дате операции с начала месяца"
        )
        for index, row in df.iterrows():
            row.loc["Дата операции"] = datetime.strptime(row.loc["Дата операции"], "%d.%m.%Y %H:%M:%S")
            df["Дата операции"][index] = row.loc["Дата операции"]

        df_by_date = df[(start_date <= df["Дата операции"]) & (df["Дата операции"] <= date_obj)]
    except Exception as e:
        logger.error(f"Произошла ошибка {e}")
        return f"Произошла ошибка {e}"
    else:
        logger.info("Вывод DataFrame")
        return df_by_date


def get_card_information(df: DataFrame) -> list[dict] | str:
    """Функция выводит информацию по каждой карте (последние 4 цифры карты,
    общая сумма расходов, кешбэк (1 рубль на каждые 100 рублей)) с начала месяца по заданную дату
    (по умолчанию берется текущая дата)."""
    try:
        cards = []

        logger.info("Группировка по номеру карты и нахождение суммы платежей по каждой карте")
        group_by_card = df.groupby("Номер карты", dropna=True).agg({"Сумма платежа": "sum"})

        logger.info("формирования словаря с информацией по карте")
        for index, row in group_by_card.iterrows():
            cards.append(
                {
                    "last_digits": str(index)[1:],
                    "total_spent": round(abs(row.loc["Сумма платежа"]), 2),
                    "cashback": round(abs(row.loc["Сумма платежа"]) / 100, 2),
                }
            )
    except Exception as e:
        logger.error(f"Произошла ошибка {e}")
        return f"Произошла ошибка {e}"
    else:
        logger.info("Вывод словаря")
        return cards


def get_top_transactions_by_amount(df: DataFrame) -> list[dict] | str:
    """Функция возвращает Топ-5 транзакций по сумме платежа"""
    try:
        top_transactions = []
        logger.info("Замена значений nan и сортировка по Сумма платежа")

        df["Категория"] = df["Категория"].fillna("Нет категории")
        df["Описание"] = df["Описание"].fillna("Нет описания")
        df["Дата платежа"] = df["Дата платежа"].fillna("Неизвестна")
        df["Сумма платежа"] = df["Сумма платежа"].fillna(0)

        df.sort_values("Сумма платежа", inplace=True, ignore_index=True, key=lambda x: abs(x), ascending=False)

        logger.info("формирования словаря с информацией по Топ-5 транзакций")
        for index, row in df.head(5).iterrows():
            top_transactions.append(
                {
                    "date": row.loc["Дата платежа"],
                    "amount": round(row.loc["Сумма платежа"], 2),
                    "category": row.loc["Категория"],
                    "description": row.loc["Описание"],
                }
            )
    except Exception as e:
        logger.error(f"Произошла ошибка {e}")
        return f"Произошла ошибка {e}"
    else:
        logger.info("Вывод DataFrame с топ 5")
        return top_transactions


def get_currency_rates() -> list[dict]:
    """Функция обращается к внешнему API для получения текущего курса валют, указанных в пользовательских настройках"""
    logger.info("Открытие файла с пользовательскими настройками")
    with open(r'C:\Users\user\Desktop\skyPro\ analysis banking transactions\user_settings.json',
              encoding="utf-8") as json_file:
        reader = json.load(json_file)
        symbols = reader["user_currencies"]

    logger.info("запрос курса валют по API")
    headers = {"apikey": API_KEY_CURRENCY}
    base = "RUB"
    url = f"https://api.apilayer.com/fixer/latest?symbols={','.join(reader["user_currencies"])}&base={base}"
    response = requests.get(url, headers=headers)

    logger.info("Проверка status_code")
    if response.status_code != 200:
        logger.error(f"Ошибка {response.status_code}")
        raise ValueError("Не удалось получить курс валюты")

    result = response.json()

    if not result.get("success"):
        logger.error("Нет информации по валютам")
        raise ValueError("Нет информации по валютам")

    logger.info("формирование списка с данными по валюте")
    currency_rates = []
    for symbol in symbols:
        currency_rates.append({"currency": symbol, "rate": round(1 / result.get("rates").get(symbol, 0), 2)})

    return currency_rates


def get_stocks() -> list[dict]:
    """Функция обращается к внешнему API для получения стоимости акций, указанных в пользовательских настройках"""
    logger.info("Открытие файла с пользовательскими настройками")
    with open(r'C:\Users\user\Desktop\skyPro\ analysis banking transactions\user_settings.json',
              encoding="utf-8") as json_file:
        reader = json.load(json_file)
        symbols = reader["user_stocks"]

    logger.info("запрос курса акций по API")
    url = f"https://api.marketstack.com/v1/eod/latest?access_key={API_KEY_STOCK}&symbols={','.join(symbols)}"

    response = requests.get(url)

    logger.info("Проверка status_code")
    if response.status_code != 200:
        logger.error(f"Ошибка {response.status_code}")
        raise ValueError("Не удалось получить курс валюты")

    result = response.json()

    if not result.get('error', True):
        logger.error("Нет информации по валютам")
        raise ValueError("Нет информации по валютам")

    logger.info("формирование списка с данными по валюте")
    stock_prices = []
    for item in range(len(symbols)):
        stock_prices.append({"stock": result.get('data')[item].get('symbol', None),
                             "price": round(result.get('data')[item].get('adj_close', 0), 2)})

    return stock_prices


# if __name__ == "__main__":
#     print(get_stocks())
# {'pagination': {'limit': 100, 'offset': 0, 'count': 100, 'total': 1255}, 'data': [{'open': 216.2, 'high': 219.87, 'low': 213.67, 'close': 216.27, 'volume': 67443518.0, 'adj_high': 219.87, 'adj_low': 213.67, 'adj_close': 216.27, 'adj_open': 216.2, 'adj_volume': 67443518.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'TSLA', 'exchange': 'XNAS', 'date': '2024-09-09T00:00:00+0000'}, {'open': 174.53, 'high': 175.85, 'low': 173.51, 'close': 175.4, 'volume': 29037362.0, 'adj_high': 175.85, 'adj_low': 173.51, 'adj_close': 175.4, 'adj_open': 174.53, 'adj_volume': 29037362.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AMZN', 'exchange': 'XNAS', 'date': '2024-09-09T00:00:00+0000'}, {'open': 152.51, 'high': 153.4, 'low': 147.215, 'close': 148.71, 'volume': 39260449.0, 'adj_high': 153.4, 'adj_low': 147.215, 'adj_close': 148.71, 'adj_open': 152.51, 'adj_volume': 39260451.0, 'split_factor': 1.0, 'dividend': 0.2, 'symbol': 'GOOGL', 'exchange': 'XNAS', 'date': '2024-09-09T00:00:00+0000'}, {'open': 407.24, 'high': 408.65, 'low': 402.15, 'close': 405.72, 'volume': 15275400.0, 'adj_high': 408.65, 'adj_low': 402.15, 'adj_close': 405.72, 'adj_open': 407.24, 'adj_volume': 15295134.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'MSFT', 'exchange': 'XNAS', 'date': '2024-09-09T00:00:00+0000'}, {'open': 220.9, 'high': 221.27, 'low': 216.72, 'close': 220.91, 'volume': 66246080.0, 'adj_high': 221.27, 'adj_low': 216.71, 'adj_close': 220.91, 'adj_open': 220.82, 'adj_volume': 67179965.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AAPL', 'exchange': 'XNAS', 'date': '2024-09-09T00:00:00+0000'}, {'open': 232.6, 'high': 233.6, 'low': 210.51, 'close': 210.73, 'volume': 112177004.0, 'adj_high': 233.6, 'adj_low': 210.51, 'adj_close': 210.73, 'adj_open': 232.6, 'adj_volume': 112177004.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'TSLA', 'exchange': 'XNAS', 'date': '2024-09-06T00:00:00+0000'}, {'open': 177.24, 'high': 178.38, 'low': 171.16, 'close': 171.39, 'volume': 41466537.0, 'adj_high': 178.38, 'adj_low': 171.16, 'adj_close': 171.39, 'adj_open': 177.24, 'adj_volume': 41466537.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AMZN', 'exchange': 'XNAS', 'date': '2024-09-06T00:00:00+0000'}, {'open': 157.3, 'high': 157.83, 'low': 150.55, 'close': 150.92, 'volume': 37912129.0, 'adj_high': 157.83, 'adj_low': 150.55, 'adj_close': 150.72, 'adj_open': 157.3, 'adj_volume': 37912130.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'GOOGL', 'exchange': 'XNAS', 'date': '2024-09-06T00:00:00+0000'}, {'open': 409.06, 'high': 410.65, 'low': 400.8, 'close': 401.7, 'volume': 19382200.0, 'adj_high': 410.65, 'adj_low': 400.8, 'adj_close': 401.7, 'adj_open': 409.06, 'adj_volume': 19609526.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'MSFT', 'exchange': 'XNAS', 'date': '2024-09-06T00:00:00+0000'}, {'open': 223.95, 'high': 225.24, 'low': 219.77, 'close': 220.82, 'volume': 48388600.0, 'adj_high': 225.24, 'adj_low': 219.77, 'adj_close': 220.82, 'adj_open': 223.95, 'adj_volume': 48423011.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AAPL', 'exchange': 'XNAS', 'date': '2024-09-06T00:00:00+0000'}, {'open': 223.49, 'high': 235.0, 'low': 222.25, 'close': 230.17, 'volume': 119247877.0, 'adj_high': 235.0, 'adj_low': 222.25, 'adj_close': 230.17, 'adj_open': 223.49, 'adj_volume': 119355013.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'TSLA', 'exchange': 'XNAS', 'date': '2024-09-05T00:00:00+0000'}, {'open': 175.0, 'high': 179.875, 'low': 174.995, 'close': 177.89, 'volume': 40142961.0, 'adj_high': 179.875, 'adj_low': 174.995, 'adj_close': 177.89, 'adj_open': 175.0, 'adj_volume': 40170526.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AMZN', 'exchange': 'XNAS', 'date': '2024-09-05T00:00:00+0000'}, {'open': 156.3, 'high': 159.45, 'low': 155.9805, 'close': 157.24, 'volume': 18688747.0, 'adj_high': 159.45, 'adj_low': 155.9805, 'adj_close': 157.24, 'adj_open': 156.3, 'adj_volume': 18688747.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'GOOGL', 'exchange': 'XNAS', 'date': '2024-09-05T00:00:00+0000'}, {'open': 408.205, 'high': 413.1, 'low': 406.13, 'close': 408.39, 'volume': 14089837.0, 'adj_high': 413.1, 'adj_low': 406.13, 'adj_close': 408.39, 'adj_open': 407.62, 'adj_volume': 14195516.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'MSFT', 'exchange': 'XNAS', 'date': '2024-09-05T00:00:00+0000'}, {'open': 221.52, 'high': 225.48, 'low': 221.52, 'close': 222.38, 'volume': 35741943.0, 'adj_high': 225.48, 'adj_low': 221.52, 'adj_close': 222.38, 'adj_open': 221.625, 'adj_volume': 36615398.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AAPL', 'exchange': 'XNAS', 'date': '2024-09-05T00:00:00+0000'}, {'open': 210.59, 'high': 222.22, 'low': 210.57, 'close': 219.41, 'volume': 80541509.0, 'adj_high': 222.22, 'adj_low': 210.57, 'adj_close': 219.41, 'adj_open': 210.59, 'adj_volume': 80217329.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'TSLA', 'exchange': 'XNAS', 'date': '2024-09-04T00:00:00+0000'}, {'open': 174.48, 'high': 175.98, 'low': 172.54, 'close': 173.33, 'volume': 30288953.0, 'adj_high': 175.98, 'adj_low': 172.54, 'adj_close': 173.33, 'adj_open': 174.48, 'adj_volume': 29682478.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AMZN', 'exchange': 'XNAS', 'date': '2024-09-04T00:00:00+0000'}, {'open': 156.655, 'high': 159.0, 'low': 155.9616, 'close': 156.45, 'volume': 19353759.0, 'adj_high': 159.0, 'adj_low': 155.9616, 'adj_close': 156.45, 'adj_open': 156.655, 'adj_volume': 19197458.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'GOOGL', 'exchange': 'XNAS', 'date': '2024-09-04T00:00:00+0000'}, {'open': 405.63, 'high': 411.24, 'low': 404.37, 'close': 408.9, 'volume': 14860891.0, 'adj_high': 411.24, 'adj_low': 404.37, 'adj_close': 408.9, 'adj_open': 405.91, 'adj_volume': 14886710.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'MSFT', 'exchange': 'XNAS', 'date': '2024-09-04T00:00:00+0000'}, {'open': 221.66, 'high': 221.755, 'low': 217.48, 'close': 220.85, 'volume': 43617462.0, 'adj_high': 221.78, 'adj_low': 217.48, 'adj_close': 220.85, 'adj_open': 221.66, 'adj_volume': 43262758.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AAPL', 'exchange': 'XNAS', 'date': '2024-09-04T00:00:00+0000'}, {'open': 215.26, 'high': 219.9043, 'low': 209.64, 'close': 210.6, 'volume': 76714222.0, 'adj_high': 219.9043, 'adj_low': 209.64, 'adj_close': 210.6, 'adj_open': 215.26, 'adj_volume': 76714222.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'TSLA', 'exchange': 'XNAS', 'date': '2024-09-03T00:00:00+0000'}, {'open': 177.55, 'high': 178.26, 'low': 175.26, 'close': 176.25, 'volume': 37817511.0, 'adj_high': 178.26, 'adj_low': 175.26, 'adj_close': 176.25, 'adj_open': 177.55, 'adj_volume': 37817511.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AMZN', 'exchange': 'XNAS', 'date': '2024-09-03T00:00:00+0000'}, {'open': 161.72, 'high': 161.85, 'low': 156.48, 'close': 157.36, 'volume': 38945301.0, 'adj_high': 161.85, 'adj_low': 156.48, 'adj_close': 157.36, 'adj_open': 161.72, 'adj_volume': 38945301.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'GOOGL', 'exchange': 'XNAS', 'date': '2024-09-03T00:00:00+0000'}, {'open': 417.99, 'high': 419.88, 'low': 407.03, 'close': 409.44, 'volume': 19788534.0, 'adj_high': 419.88, 'adj_low': 407.03, 'adj_close': 409.44, 'adj_open': 417.91, 'adj_volume': 20313603.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'MSFT', 'exchange': 'XNAS', 'date': '2024-09-03T00:00:00+0000'}, {'open': 228.61, 'high': 229.0, 'low': 221.17, 'close': 222.77, 'volume': 48082190.0, 'adj_high': 229.0, 'adj_low': 221.17, 'adj_close': 222.77, 'adj_open': 228.55, 'adj_volume': 50190574.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AAPL', 'exchange': 'XNAS', 'date': '2024-09-03T00:00:00+0000'}, {'open': 208.63, 'high': 214.5701, 'low': 207.03, 'close': 214.11, 'volume': 63370608.0, 'adj_high': 214.5701, 'adj_low': 207.03, 'adj_close': 214.11, 'adj_open': 208.63, 'adj_volume': 63370608.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'TSLA', 'exchange': 'XNAS', 'date': '2024-08-30T00:00:00+0000'}, {'open': 172.78, 'high': 178.9, 'low': 172.6, 'close': 178.5, 'volume': 43429355.0, 'adj_high': 178.9, 'adj_low': 172.6, 'adj_close': 178.5, 'adj_open': 172.78, 'adj_volume': 43429355.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AMZN', 'exchange': 'XNAS', 'date': '2024-08-30T00:00:00+0000'}, {'open': 162.615, 'high': 163.66, 'low': 161.6925, 'close': 163.38, 'volume': 22123811.0, 'adj_high': 163.66, 'adj_low': 161.6925, 'adj_close': 163.38, 'adj_open': 162.615, 'adj_volume': 22123811.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'GOOGL', 'exchange': 'XNAS', 'date': '2024-08-30T00:00:00+0000'}, {'open': 415.6, 'high': 417.49, 'low': 412.13, 'close': 417.14, 'volume': 24308324.0, 'adj_high': 417.49, 'adj_low': 412.13, 'adj_close': 417.14, 'adj_open': 415.6, 'adj_volume': 24308324.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'MSFT', 'exchange': 'XNAS', 'date': '2024-08-30T00:00:00+0000'}, {'open': 230.19, 'high': 230.4, 'low': 227.48, 'close': 229.0, 'volume': 52990770.0, 'adj_high': 230.4, 'adj_low': 227.48, 'adj_close': 229.0, 'adj_open': 230.19, 'adj_volume': 52990770.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AAPL', 'exchange': 'XNAS', 'date': '2024-08-30T00:00:00+0000'}, {'open': 209.8, 'high': 214.89, 'low': 205.97, 'close': 206.28, 'volume': 62308818.0, 'adj_high': 214.89, 'adj_low': 205.97, 'adj_close': 206.28, 'adj_open': 209.8, 'adj_volume': 62308818.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'TSLA', 'exchange': 'XNAS', 'date': '2024-08-29T00:00:00+0000'}, {'open': 173.22, 'high': 174.29, 'low': 170.81, 'close': 172.12, 'volume': 26407815.0, 'adj_high': 174.29, 'adj_low': 170.81, 'adj_close': 172.12, 'adj_open': 173.22, 'adj_volume': 26407815.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AMZN', 'exchange': 'XNAS', 'date': '2024-08-29T00:00:00+0000'}, {'open': 164.31, 'high': 165.97, 'low': 160.25, 'close': 161.78, 'volume': 19699767.0, 'adj_high': 165.97, 'adj_low': 160.25, 'adj_close': 161.78, 'adj_open': 164.31, 'adj_volume': 19699767.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'GOOGL', 'exchange': 'XNAS', 'date': '2024-08-29T00:00:00+0000'}, {'open': 414.94, 'high': 422.05, 'low': 410.6, 'close': 413.12, 'volume': 17030800.0, 'adj_high': 422.05, 'adj_low': 410.6, 'adj_close': 413.12, 'adj_open': 414.94, 'adj_volume': 17045241.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'MSFT', 'exchange': 'XNAS', 'date': '2024-08-29T00:00:00+0000'}, {'open': 230.28, 'high': 232.92, 'low': 228.88, 'close': 229.79, 'volume': 51342429.0, 'adj_high': 232.92, 'adj_low': 228.88, 'adj_close': 229.79, 'adj_open': 230.1, 'adj_volume': 51906297.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AAPL', 'exchange': 'XNAS', 'date': '2024-08-29T00:00:00+0000'}, {'open': 209.72, 'high': 211.84, 'low': 202.59, 'close': 205.75, 'volume': 64116350.0, 'adj_high': 211.84, 'adj_low': 202.59, 'adj_close': 205.75, 'adj_open': 209.72, 'adj_volume': 64116350.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'TSLA', 'exchange': 'XNAS', 'date': '2024-08-28T00:00:00+0000'}, {'open': 173.69, 'high': 173.69, 'low': 168.92, 'close': 170.8, 'volume': 29045025.0, 'adj_high': 173.69, 'adj_low': 168.92, 'adj_close': 170.8, 'adj_open': 173.69, 'adj_volume': 29045025.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AMZN', 'exchange': 'XNAS', 'date': '2024-08-28T00:00:00+0000'}, {'open': 165.035, 'high': 165.6, 'low': 161.5284, 'close': 162.85, 'volume': 16407444.0, 'adj_high': 165.6, 'adj_low': 161.5284, 'adj_close': 162.85, 'adj_open': 165.035, 'adj_volume': 16407444.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'GOOGL', 'exchange': 'XNAS', 'date': '2024-08-28T00:00:00+0000'}, {'open': 414.88, 'high': 415.0, 'low': 407.31, 'close': 410.6, 'volume': 14846300.0, 'adj_high': 415.0, 'adj_low': 407.31, 'adj_close': 410.6, 'adj_open': 414.88, 'adj_volume': 14882660.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'MSFT', 'exchange': 'XNAS', 'date': '2024-08-28T00:00:00+0000'}, {'open': 228.05, 'high': 229.85, 'low': 225.6801, 'close': 226.49, 'volume': 37794932.0, 'adj_high': 229.86, 'adj_low': 225.68, 'adj_close': 226.49, 'adj_open': 227.92, 'adj_volume': 38052167.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AAPL', 'exchange': 'XNAS', 'date': '2024-08-28T00:00:00+0000'}, {'open': 213.25, 'high': 215.66, 'low': 206.94, 'close': 209.21, 'volume': 62821390.0, 'adj_high': 215.66, 'adj_low': 206.94, 'adj_close': 209.21, 'adj_open': 213.25, 'adj_volume': 62821390.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'TSLA', 'exchange': 'XNAS', 'date': '2024-08-27T00:00:00+0000'}, {'open': 174.15, 'high': 174.89, 'low': 172.25, 'close': 173.12, 'volume': 29841979.0, 'adj_high': 174.89, 'adj_low': 172.25, 'adj_close': 173.12, 'adj_open': 174.15, 'adj_volume': 29841979.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AMZN', 'exchange': 'XNAS', 'date': '2024-08-27T00:00:00+0000'}, {'open': 165.835, 'high': 166.4426, 'low': 164.46, 'close': 164.68, 'volume': 11821941.0, 'adj_high': 166.4426, 'adj_low': 164.46, 'adj_close': 164.68, 'adj_open': 165.835, 'adj_volume': 11821941.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'GOOGL', 'exchange': 'XNAS', 'date': '2024-08-27T00:00:00+0000'}, {'open': 412.86, 'high': 414.36, 'low': 410.25, 'close': 413.84, 'volume': 13473900.0, 'adj_high': 414.36, 'adj_low': 410.25, 'adj_close': 413.84, 'adj_open': 412.86, 'adj_volume': 13492911.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'MSFT', 'exchange': 'XNAS', 'date': '2024-08-27T00:00:00+0000'}, {'open': 226.2101, 'high': 228.79, 'low': 224.89, 'close': 228.03, 'volume': 35851754.0, 'adj_high': 228.85, 'adj_low': 224.89, 'adj_close': 228.03, 'adj_open': 225.995, 'adj_volume': 35934559.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AAPL', 'exchange': 'XNAS', 'date': '2024-08-27T00:00:00+0000'}, {'open': 218.75, 'high': 219.09, 'low': 211.01, 'close': 213.21, 'volume': 59301187.0, 'adj_high': 219.09, 'adj_low': 211.01, 'adj_close': 213.21, 'adj_open': 218.75, 'adj_volume': 59301187.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'TSLA', 'exchange': 'XNAS', 'date': '2024-08-26T00:00:00+0000'}, {'open': 176.7, 'high': 177.4682, 'low': 174.3, 'close': 175.5, 'volume': 22366236.0, 'adj_high': 177.4682, 'adj_low': 174.3, 'adj_close': 175.5, 'adj_open': 176.7, 'adj_volume': 22366236.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AMZN', 'exchange': 'XNAS', 'date': '2024-08-26T00:00:00+0000'}, {'open': 166.38, 'high': 167.55, 'low': 164.455, 'close': 166.16, 'volume': 14190417.0, 'adj_high': 167.55, 'adj_low': 164.455, 'adj_close': 166.16, 'adj_open': 166.38, 'adj_volume': 14190417.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'GOOGL', 'exchange': 'XNAS', 'date': '2024-08-26T00:00:00+0000'}, {'open': 416.37, 'high': 417.28, 'low': 411.34, 'close': 413.49, 'volume': 13134700.0, 'adj_high': 417.2799, 'adj_low': 411.34, 'adj_close': 413.49, 'adj_open': 416.365, 'adj_volume': 13152830.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'MSFT', 'exchange': 'XNAS', 'date': '2024-08-26T00:00:00+0000'}, {'open': 227.21, 'high': 227.28, 'low': 223.8905, 'close': 227.18, 'volume': 29834257.0, 'adj_high': 227.28, 'adj_low': 223.8905, 'adj_close': 227.18, 'adj_open': 226.76, 'adj_volume': 30602208.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AAPL', 'exchange': 'XNAS', 'date': '2024-08-26T00:00:00+0000'}, {'open': 214.455, 'high': 221.48, 'low': 214.21, 'close': 220.32, 'volume': 81525207.0, 'adj_high': 221.48, 'adj_low': 214.21, 'adj_close': 220.32, 'adj_open': 214.455, 'adj_volume': 81525207.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'TSLA', 'exchange': 'XNAS', 'date': '2024-08-23T00:00:00+0000'}, {'open': 177.34, 'high': 178.9699, 'low': 175.24, 'close': 177.04, 'volume': 29150091.0, 'adj_high': 178.9699, 'adj_low': 175.24, 'adj_close': 177.04, 'adj_open': 177.34, 'adj_volume': 29150091.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AMZN', 'exchange': 'XNAS', 'date': '2024-08-23T00:00:00+0000'}, {'open': 164.72, 'high': 166.18, 'low': 163.83, 'close': 165.62, 'volume': 13955741.0, 'adj_high': 166.18, 'adj_low': 163.83, 'adj_close': 165.62, 'adj_open': 164.72, 'adj_volume': 13955741.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'GOOGL', 'exchange': 'XNAS', 'date': '2024-08-23T00:00:00+0000'}, {'open': 416.98, 'high': 419.26, 'low': 412.09, 'close': 416.79, 'volume': 18473000.0, 'adj_high': 419.26, 'adj_low': 412.09, 'adj_close': 416.79, 'adj_open': 416.98, 'adj_volume': 18493784.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'MSFT', 'exchange': 'XNAS', 'date': '2024-08-23T00:00:00+0000'}, {'open': 225.66, 'high': 228.22, 'low': 224.33, 'close': 226.84, 'volume': 38629400.0, 'adj_high': 228.22, 'adj_low': 224.33, 'adj_close': 226.84, 'adj_open': 225.6589, 'adj_volume': 38677250.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AAPL', 'exchange': 'XNAS', 'date': '2024-08-23T00:00:00+0000'}, {'open': 223.82, 'high': 224.8, 'low': 210.32, 'close': 210.66, 'volume': 79514482.0, 'adj_high': 224.8, 'adj_low': 210.32, 'adj_close': 210.66, 'adj_open': 223.82, 'adj_volume': 79514482.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'TSLA', 'exchange': 'XNAS', 'date': '2024-08-22T00:00:00+0000'}, {'open': 181.38, 'high': 181.47, 'low': 175.68, 'close': 176.13, 'volume': 32047482.0, 'adj_high': 181.47, 'adj_low': 175.68, 'adj_close': 176.13, 'adj_open': 181.38, 'adj_volume': 32047482.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AMZN', 'exchange': 'XNAS', 'date': '2024-08-22T00:00:00+0000'}, {'open': 167.26, 'high': 167.59, 'low': 163.31, 'close': 163.8, 'volume': 22493275.0, 'adj_high': 167.59, 'adj_low': 163.31, 'adj_close': 163.8, 'adj_open': 167.26, 'adj_volume': 22493275.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'GOOGL', 'exchange': 'XNAS', 'date': '2024-08-22T00:00:00+0000'}, {'open': 227.6, 'high': 228.34, 'low': 223.9, 'close': 224.53, 'volume': 43434198.0, 'adj_high': 228.34, 'adj_low': 223.9, 'adj_close': 224.53, 'adj_open': 227.79, 'adj_volume': 43695321.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AAPL', 'exchange': 'XNAS', 'date': '2024-08-22T00:00:00+0000'}, {'open': 424.36, 'high': 426.79, 'low': 414.61, 'close': 415.55, 'volume': 19348500.0, 'adj_high': 426.7899, 'adj_low': 414.61, 'adj_close': 415.55, 'adj_open': 424.36, 'adj_volume': 19361901.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'MSFT', 'exchange': 'XNAS', 'date': '2024-08-22T00:00:00+0000'}, {'open': 222.67, 'high': 224.6594, 'low': 218.86, 'close': 223.27, 'volume': 70145964.0, 'adj_high': 224.6594, 'adj_low': 218.86, 'adj_close': 223.27, 'adj_open': 222.67, 'adj_volume': 70145964.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'TSLA', 'exchange': 'XNAS', 'date': '2024-08-21T00:00:00+0000'}, {'open': 179.92, 'high': 182.385, 'low': 178.8937, 'close': 180.11, 'volume': 35599120.0, 'adj_high': 182.385, 'adj_low': 178.8937, 'adj_close': 180.11, 'adj_open': 179.92, 'adj_volume': 35599120.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AMZN', 'exchange': 'XNAS', 'date': '2024-08-21T00:00:00+0000'}, {'open': 165.15, 'high': 166.85, 'low': 164.67, 'close': 165.85, 'volume': 22901997.0, 'adj_high': 166.85, 'adj_low': 164.67, 'adj_close': 165.85, 'adj_open': 165.15, 'adj_volume': 22901997.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'GOOGL', 'exchange': 'XNAS', 'date': '2024-08-21T00:00:00+0000'}, {'open': 226.49, 'high': 227.98, 'low': 225.191, 'close': 226.4, 'volume': 33246786.0, 'adj_high': 227.98, 'adj_low': 225.05, 'adj_close': 226.4, 'adj_open': 226.52, 'adj_volume': 34765480.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AAPL', 'exchange': 'XNAS', 'date': '2024-08-21T00:00:00+0000'}, {'open': 424.08, 'high': 426.4, 'low': 421.72, 'close': 424.14, 'volume': 15744000.0, 'adj_high': 426.4, 'adj_low': 421.72, 'adj_close': 424.14, 'adj_open': 424.075, 'adj_volume': 16067298.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'MSFT', 'exchange': 'XNAS', 'date': '2024-08-21T00:00:00+0000'}, {'open': 224.88, 'high': 228.22, 'low': 219.56, 'close': 221.1, 'volume': 74001182.0, 'adj_high': 228.22, 'adj_low': 219.56, 'adj_close': 221.1, 'adj_open': 224.88, 'adj_volume': 74001182.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'TSLA', 'exchange': 'XNAS', 'date': '2024-08-20T00:00:00+0000'}, {'open': 177.92, 'high': 179.01, 'low': 177.4308, 'close': 178.88, 'volume': 26255204.0, 'adj_high': 179.01, 'adj_low': 177.4308, 'adj_close': 178.88, 'adj_open': 177.92, 'adj_volume': 26255204.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AMZN', 'exchange': 'XNAS', 'date': '2024-08-20T00:00:00+0000'}, {'open': 166.9, 'high': 168.64, 'low': 166.82, 'close': 167.18, 'volume': 18341533.0, 'adj_high': 168.64, 'adj_low': 166.82, 'adj_close': 167.18, 'adj_open': 166.9, 'adj_volume': 18341533.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'GOOGL', 'exchange': 'XNAS', 'date': '2024-08-20T00:00:00+0000'}, {'open': 225.77, 'high': 227.17, 'low': 225.45, 'close': 226.51, 'volume': 30241200.0, 'adj_high': 227.17, 'adj_low': 225.45, 'adj_close': 226.51, 'adj_open': 225.77, 'adj_volume': 30299033.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AAPL', 'exchange': 'XNAS', 'date': '2024-08-20T00:00:00+0000'}, {'open': 421.7, 'high': 425.86, 'low': 421.64, 'close': 424.8, 'volume': 16352000.0, 'adj_high': 425.86, 'adj_low': 421.64, 'adj_close': 424.8, 'adj_open': 421.7, 'adj_volume': 16387581.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'MSFT', 'exchange': 'XNAS', 'date': '2024-08-20T00:00:00+0000'}, {'open': 225.72, 'high': 225.99, 'low': 223.04, 'close': 225.89, 'volume': 40639000.0, 'adj_high': 225.99, 'adj_low': 223.04, 'adj_close': 225.89, 'adj_open': 225.72, 'adj_volume': 40687813.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AAPL', 'exchange': 'XNAS', 'date': '2024-08-19T00:00:00+0000'}, {'open': 177.64, 'high': 178.3, 'low': 176.16, 'close': 178.22, 'volume': 31129807.0, 'adj_high': 178.3, 'adj_low': 176.16, 'adj_close': 178.22, 'adj_open': 177.64, 'adj_volume': 31129807.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AMZN', 'exchange': 'XNAS', 'date': '2024-08-19T00:00:00+0000'}, {'open': 165.28, 'high': 166.69, 'low': 164.26, 'close': 166.67, 'volume': 22416185.0, 'adj_high': 166.69, 'adj_low': 164.26, 'adj_close': 166.67, 'adj_open': 165.28, 'adj_volume': 22416185.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'GOOGL', 'exchange': 'XNAS', 'date': '2024-08-19T00:00:00+0000'}, {'open': 217.07, 'high': 222.98, 'low': 214.09, 'close': 222.72, 'volume': 76435222.0, 'adj_high': 222.98, 'adj_low': 214.09, 'adj_close': 222.72, 'adj_open': 217.07, 'adj_volume': 76435222.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'TSLA', 'exchange': 'XNAS', 'date': '2024-08-19T00:00:00+0000'}, {'open': 418.96, 'high': 421.75, 'low': 416.46, 'close': 421.53, 'volume': 15210800.0, 'adj_high': 421.75, 'adj_low': 416.46, 'adj_close': 421.53, 'adj_open': 418.96, 'adj_volume': 15233957.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'MSFT', 'exchange': 'XNAS', 'date': '2024-08-19T00:00:00+0000'}, {'open': 420.6, 'high': 421.34, 'low': 417.3, 'close': 418.47, 'volume': 22757000.0, 'adj_high': 421.34, 'adj_low': 417.3, 'adj_close': 418.47, 'adj_open': 420.6, 'adj_volume': 22775593.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'MSFT', 'exchange': 'XNAS', 'date': '2024-08-16T00:00:00+0000'}, {'open': 223.92, 'high': 226.83, 'low': 223.65, 'close': 226.05, 'volume': 44289900.0, 'adj_high': 226.8271, 'adj_low': 223.6501, 'adj_close': 226.05, 'adj_open': 223.92, 'adj_volume': 44340240.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AAPL', 'exchange': 'XNAS', 'date': '2024-08-16T00:00:00+0000'}, {'open': 177.04, 'high': 178.34, 'low': 176.2601, 'close': 177.06, 'volume': 31489175.0, 'adj_high': 178.34, 'adj_low': 176.2601, 'adj_close': 177.06, 'adj_open': 177.04, 'adj_volume': 31489175.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AMZN', 'exchange': 'XNAS', 'date': '2024-08-16T00:00:00+0000'}, {'open': 211.15, 'high': 219.8, 'low': 210.8, 'close': 216.12, 'volume': 88765122.0, 'adj_high': 219.8, 'adj_low': 210.8, 'adj_close': 216.12, 'adj_open': 211.15, 'adj_volume': 88765122.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'TSLA', 'exchange': 'XNAS', 'date': '2024-08-16T00:00:00+0000'}, {'open': 161.47, 'high': 165.06, 'low': 161.13, 'close': 162.96, 'volume': 24208647.0, 'adj_high': 165.06, 'adj_low': 161.13, 'adj_close': 162.96, 'adj_open': 161.47, 'adj_volume': 24208647.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'GOOGL', 'exchange': 'XNAS', 'date': '2024-08-16T00:00:00+0000'}, {'open': 419.8, 'high': 421.11, 'low': 417.66, 'close': 421.03, 'volume': 20721500.0, 'adj_high': 421.11, 'adj_low': 417.66, 'adj_close': 421.03, 'adj_open': 419.8, 'adj_volume': 20752144.0, 'split_factor': 1.0, 'dividend': 0.75, 'symbol': 'MSFT', 'exchange': 'XNAS', 'date': '2024-08-15T00:00:00+0000'}, {'open': 224.6, 'high': 225.35, 'low': 222.76, 'close': 224.72, 'volume': 46335300.0, 'adj_high': 225.35, 'adj_low': 222.76, 'adj_close': 224.72, 'adj_open': 224.6, 'adj_volume': 46414013.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AAPL', 'exchange': 'XNAS', 'date': '2024-08-15T00:00:00+0000'}, {'open': 174.86, 'high': 177.91, 'low': 173.99, 'close': 177.59, 'volume': 51698513.0, 'adj_high': 177.91, 'adj_low': 173.99, 'adj_close': 177.59, 'adj_open': 174.86, 'adj_volume': 51698513.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AMZN', 'exchange': 'XNAS', 'date': '2024-08-15T00:00:00+0000'}, {'open': 205.02, 'high': 215.88, 'low': 204.82, 'close': 214.14, 'volume': 89848530.0, 'adj_high': 215.88, 'adj_low': 204.82, 'adj_close': 214.14, 'adj_open': 205.02, 'adj_volume': 89848530.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'TSLA', 'exchange': 'XNAS', 'date': '2024-08-15T00:00:00+0000'}, {'open': 160.5, 'high': 161.635, 'low': 159.61, 'close': 161.3, 'volume': 31524252.0, 'adj_high': 161.635, 'adj_low': 159.61, 'adj_close': 161.3, 'adj_open': 160.5, 'adj_volume': 31524252.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'GOOGL', 'exchange': 'XNAS', 'date': '2024-08-15T00:00:00+0000'}, {'open': 220.57, 'high': 223.03, 'low': 219.7, 'close': 221.72, 'volume': 41888500.0, 'adj_high': 223.03, 'adj_low': 219.7, 'adj_close': 221.72, 'adj_open': 220.57, 'adj_volume': 41960574.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AAPL', 'exchange': 'XNAS', 'date': '2024-08-14T00:00:00+0000'}, {'open': 172.11, 'high': 172.28, 'low': 168.86, 'close': 170.1, 'volume': 28843804.0, 'adj_high': 172.28, 'adj_low': 168.86, 'adj_close': 170.1, 'adj_open': 172.11, 'adj_volume': 28843804.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AMZN', 'exchange': 'XNAS', 'date': '2024-08-14T00:00:00+0000'}, {'open': 207.39, 'high': 208.44, 'low': 198.75, 'close': 201.38, 'volume': 70250014.0, 'adj_high': 208.44, 'adj_low': 198.75, 'adj_close': 201.38, 'adj_open': 207.39, 'adj_volume': 70250014.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'TSLA', 'exchange': 'XNAS', 'date': '2024-08-14T00:00:00+0000'}, {'open': 414.8, 'high': 417.72, 'low': 412.45, 'close': 416.86, 'volume': 18250400.0, 'adj_high': 417.72, 'adj_low': 412.4456, 'adj_close': 416.11, 'adj_open': 414.8, 'adj_volume': 18266980.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'MSFT', 'exchange': 'XNAS', 'date': '2024-08-14T00:00:00+0000'}, {'open': 162.4, 'high': 163.22, 'low': 157.71, 'close': 160.37, 'volume': 40591126.0, 'adj_high': 163.22, 'adj_low': 157.71, 'adj_close': 160.37, 'adj_open': 162.4, 'adj_volume': 40591126.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'GOOGL', 'exchange': 'XNAS', 'date': '2024-08-14T00:00:00+0000'}, {'open': 219.01, 'high': 221.89, 'low': 219.01, 'close': 221.27, 'volume': 44095400.0, 'adj_high': 221.89, 'adj_low': 219.01, 'adj_close': 221.27, 'adj_open': 219.01, 'adj_volume': 44155331.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AAPL', 'exchange': 'XNAS', 'date': '2024-08-13T00:00:00+0000'}, {'open': 167.81, 'high': 171.04, 'low': 167.1, 'close': 170.23, 'volume': 39237915.0, 'adj_high': 171.04, 'adj_low': 167.1, 'adj_close': 170.23, 'adj_open': 167.81, 'adj_volume': 39237915.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AMZN', 'exchange': 'XNAS', 'date': '2024-08-13T00:00:00+0000'}, {'open': 198.47, 'high': 208.49, 'low': 197.06, 'close': 207.83, 'volume': 76247387.0, 'adj_high': 208.49, 'adj_low': 197.06, 'adj_close': 207.83, 'adj_open': 198.47, 'adj_volume': 76247387.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'TSLA', 'exchange': 'XNAS', 'date': '2024-08-13T00:00:00+0000'}, {'open': 410.08, 'high': 414.95, 'low': 409.58, 'close': 414.01, 'volume': 18533284.0, 'adj_high': 414.95, 'adj_low': 409.57, 'adj_close': 414.01, 'adj_open': 409.59, 'adj_volume': 19414271.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'MSFT', 'exchange': 'XNAS', 'date': '2024-08-13T00:00:00+0000'}, {'open': 163.41, 'high': 164.73, 'low': 162.97, 'close': 164.16, 'volume': 18551690.0, 'adj_high': 164.73, 'adj_low': 162.97, 'adj_close': 164.16, 'adj_open': 163.41, 'adj_volume': 18551690.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'GOOGL', 'exchange': 'XNAS', 'date': '2024-08-13T00:00:00+0000'}, {'open': 407.06, 'high': 408.76, 'low': 404.24, 'close': 406.81, 'volume': 16739400.0, 'adj_high': 408.76, 'adj_low': 404.2434, 'adj_close': 406.81, 'adj_open': 407.06, 'adj_volume': 16762883.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'MSFT', 'exchange': 'XNAS', 'date': '2024-08-12T00:00:00+0000'}, {'open': 168.14, 'high': 168.55, 'low': 166.1101, 'close': 166.8, 'volume': 30072788.0, 'adj_high': 168.55, 'adj_low': 166.1101, 'adj_close': 166.8, 'adj_open': 168.14, 'adj_volume': 30072788.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'AMZN', 'exchange': 'XNAS', 'date': '2024-08-12T00:00:00+0000'}, {'open': 199.02, 'high': 199.26, 'low': 194.67, 'close': 197.49, 'volume': 64044903.0, 'adj_high': 199.26, 'adj_low': 194.67, 'adj_close': 197.49, 'adj_open': 199.02, 'adj_volume': 64044903.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'TSLA', 'exchange': 'XNAS', 'date': '2024-08-12T00:00:00+0000'}, {'open': 164.35, 'high': 164.9, 'low': 161.84, 'close': 162.29, 'volume': 15895286.0, 'adj_high': 164.9, 'adj_low': 161.84, 'adj_close': 162.29, 'adj_open': 164.35, 'adj_volume': 15895286.0, 'split_factor': 1.0, 'dividend': 0.0, 'symbol': 'GOOGL', 'exchange': 'XNAS', 'date': '2024-08-12T00:00:00+0000'}, {'open': 216.07, 'high': 219.51, 'low': 215.6, 'close': 217.53, 'volume': 37992400.0, 'adj_high': 219.5099, 'adj_low': 215.6, 'adj_close': 217.53, 'adj_open': 216.07, 'adj_volume': 38028092.0, 'split_factor': 1.0, 'dividend': 0.25, 'symbol': 'AAPL', 'exchange': 'XNAS', 'date': '2024-08-12T00:00:00+0000'}]}
# [{'stock': 'TSLA', 'price': 216.27}, {'stock': 'AMZN', 'price': 175.4}, {'stock': 'GOOGL', 'price': 148.71}, {'stock': 'MSFT', 'price': 405.72}, {'stock': 'AAPL', 'price': 220.91}]
