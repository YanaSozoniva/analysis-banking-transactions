import logging
from datetime import datetime, timedelta
from os import getcwd
from os.path import dirname, exists

import pandas as pd
from pandas import DataFrame

PATH_LOG = dirname(getcwd())


logging.basicConfig(
    encoding="utf-8",
    filemode='w',
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


def get_card_information(df: DataFrame, date: str = datetime.now().strftime("%d.%m.%Y")) -> dict | str:
    """Функция выводит информацию по каждой карте (последние 4 цифры карты,
    общая сумма расходов, кешбэк (1 рубль на каждые 100 рублей)) с начала месяца по заданную дату
    (по умолчанию берется текущая дата)."""
    try:
        card_info = dict()
        logger.info("Удаляем значения nan из столбца 'Дата операции'")
        df['Дата операции'].dropna(inplace=True)

        date_obj = datetime.strptime(date, '%d.%m.%Y')
        date_obj += timedelta(days=1)
        logger.info('Определяем начало месяца')
        start_date = date_obj.replace(day=1)

        logger.info("Преобразовываем столбец с датами в объект datetime и фильтруем данные по дате операции с начала месяца")
        for index, row in df.iterrows():
            row.loc['Дата операции'] = datetime.strptime(row.loc['Дата операции'], '%d.%m.%Y  %H:%M:%S')
            df['Дата операции'][index] = row.loc['Дата операции']

        df_by_date = df[(start_date <= df['Дата операции']) & (df['Дата операции'] <= date_obj)]

        logger.info("Группировка по номеру карты и нахождение суммы платежей по каждой карте")
        group_by_card = df_by_date.groupby('Номер карты', dropna=True).agg({'Сумма платежа': 'sum'})

        logger.info("формирования словаря с информацией по карте")
        for index, row in group_by_card.iterrows():
            card_info[index[1:]] = {
                'total_spent': round(row.loc['Сумма платежа'], 2),
                'cashback': round(row.loc['Сумма платежа'] / 100, 2)}
    except Exception as e:
        logger.error(f"Произошла ошибка {e}")
        return f"Произошла ошибка {e}"
    else:
        logger.info("Вывод словаря")
        return card_info


def get_top_transactions_by_amount():
    """"""
    pass


if __name__ == '__main__':
    result = pd.DataFrame({
        'Дата операции': ['21.12.2021 01:06:22', '20.05.2021 12:06:22', '01.12.2021 01:06:22', '31.12.2021 00:12:53'],
        'Номер карты': ['*7197', '*7197', '*5091', '*5091'],
        'Сумма платежа': [-160.89, 5000, 23.60, -645.78]
    })
    print(get_card_information(result))
    # result = export_data_from_xlsx(r'C:\Users\user\Desktop\skyPro\ analysis banking transactions\data\operations.xlsx')


