import logging
from datetime import datetime
from os import getcwd
from os.path import dirname, exists

import pandas as pd
from pandas import DataFrame

PATH_LOG = dirname(getcwd())


logging.basicConfig(
    encoding="utf-8",
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


def get_card_information(df: DataFrame, ):
    """По каждой карте: последние 4 цифры карты; общая сумма расходов;кешбэк (1 рубль на каждые 100 рублей)."""
    pass


if __name__ == '__main__':
    result = export_data_from_xlsx(r'C:\Users\user\Desktop\skyPro\ analysis banking transactions\data\operations.xlsx')
    print(result)
