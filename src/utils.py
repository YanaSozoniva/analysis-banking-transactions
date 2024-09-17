import json

import os
from datetime import datetime

from os.path import  exists
from typing import Optional

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY_CURRENCY = os.getenv("API_KEY_CURRENCY")
API_KEY_STOCK = os.getenv("API_KEY_STOCK")

from src.logger import logger_setup

logger = logger_setup()


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


def export_data_from_xlsx(file_name: str) -> pd.DataFrame | str:
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


def filter_by_date_range(df: pd.DataFrame, date: Optional[str] = None, count_month: int = 1) -> pd.DataFrame | str:
    """Фильтрует данные с начала месяца, на который выпадает входящая дата,
    по входящую дату (по умолчанию берется текущая дата) или фильтрует на указанное количество месяцев."""
    try:
        logger.info("проверка ввода даты")
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        logger.info("Удаляем значения nan из столбца 'Дата операции'")
        df["Дата операции"].dropna(inplace=True)

        logger.info("Преобразуем дату в формат %Y-%m-%d")
        date_obj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        logger.info("Определяем начало месяца")
        start_date = date_obj.replace(day=1, hour=0, minute=0, second=0)
        if count_month > 1:
            start_date = date_obj - pd.DateOffset(months=count_month)

        logger.info(
            "Преобразовываем столбец с датами в объект datetime" " и фильтруем данные по дате в указанном диапазоне"
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


def get_card_information(df: pd.DataFrame) -> list[dict] | str:
    """Функция выводит информацию по каждой карте (последние 4 цифры карты,
    общая сумма расходов, кешбэк (1 рубль на каждые 100 рублей))"""
    try:
        cards = []

        logger.info("Группировка по номеру карты и подсчет расходов по каждой карте")
        df = df[df["Сумма платежа"] < 0].copy()
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


def get_top_transactions_by_amount(df: pd.DataFrame) -> list[dict] | str:
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
    with open(
        r"user_settings.json", encoding="utf-8"
    ) as json_file:
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
    with open(
        r"user_settings.json", encoding="utf-8"
    ) as json_file:
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

    if not result.get("error", True):
        logger.error("Нет информации по валютам")
        raise ValueError("Нет информации по валютам")

    logger.info("формирование списка с данными по валюте")
    stock_prices = []
    for item in range(len(symbols)):
        stock_prices.append(
            {
                "stock": result.get("data")[item].get("symbol", None),
                "price": round(result.get("data")[item].get("adj_close", 0), 2),
            }
        )

    return stock_prices


if __name__ == "__main__":
    df = pd.DataFrame(
        {
            "Дата операции": [
                "21.12.2021 01:06:22",
                "20.12.2021 12:06:22",
                "01.12.2021 01:06:22",
                "31.12.2021 00:12:53",
                "08.09.2024 00:12:53",
            ],
            "Номер карты": ["*7197", "*7197", "*5091", "*5091", "*7197"],
            "Сумма платежа": [-160.89, 5000, 23.60, -645.78, 1588.36],
            "Категория": ["Переводы", "Развлечения", "Переводы", "Такси", "Госуслуги"],
            "Описание": [
                "Перевод Кредитная карта. ТП 10.2 RUR",
                "sevs.eduerp.ru",
                "Дмитрий Р.",
                "Яндекс Такси",
                "Почта России",
            ],
            "Дата платежа": ["21.12.2021", "20.12.2021", "01.12.2021", "31.12.2021", "08.09.2024"],
        }
    )
    print(get_stocks())
