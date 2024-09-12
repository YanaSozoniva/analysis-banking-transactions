import logging
import json
from os import getcwd
from os.path import dirname, join
from typing import Optional
from functools import wraps
from typing import Any, Callable

import pandas as pd

from src.utils import filter_by_date_range

pd.options.mode.chained_assignment = None

PATH_LOG = dirname(getcwd())

logging.basicConfig(
    encoding="utf-8",
    filename=PATH_LOG + r"\logs\reports.log",
    format="%(asctime)s:%(filename)s:%(funcName)s %(levelname)s: %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger("reports")


def write_to_file(file_name: str = 'reports.json') -> Callable:
    """Декоратор для функций-отчетов, записывающий в файл результат, который возвращает функция, формирующая отчет."""

    def wrapper(func: Any) -> Callable:
        @wraps(func)
        def inner(*args: Any, **kwargs: Any) -> Any:

            result = func(*args, **kwargs)
            path_f = r'C:\Users\user\Desktop\skyPro\ analysis banking transactions\data'
            full_path = join(path_f, file_name)

            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=4, ensure_ascii=False)

            return result

        return inner

    return wrapper


@write_to_file()
def spending_by_weekday(transactions: pd.DataFrame, date: Optional[str] = None) -> pd.DataFrame | str:
    """Функция возвращает средние траты в каждый из дней недели за последние три месяца (от переданной даты)
    Если дата не передана, то берется текущая дата"""
    try:

        transactions_3_month = filter_by_date_range(transactions, date=date, count_month=3)
        logger.info('Преобразуем столбец "Дата операции" в формат datetime')
        transactions_3_month["Дата операции"] = pd.to_datetime(
            transactions_3_month.loc[:, "Дата операции"], format="%d.%m.%Y %H:%M:%S", dayfirst=True
        )

        logger.info("Добавляем столбец с днем недели и фильтруем только расходы")
        transactions_3_month = transactions_3_month.assign(
            weekdays=transactions_3_month["Дата операции"].dt.day_name()
        )
        transactions_3_month_spending = transactions_3_month[transactions_3_month["Сумма платежа"] < 0].copy()

        logger.info("Группируем по дням недели и считаем средние траты")
        spending_day_week = transactions_3_month_spending.groupby("weekdays", as_index=False).agg(
            {"Сумма платежа": "mean"}
        )

        spending_day_week.rename(columns={"Сумма платежа": "spending"}, inplace=True)
        spending_day_week["spending"] = round(spending_day_week.spending.abs(), 2)
        return spending_day_week.to_json(orient="records", force_ascii=False)

    except Exception as e:
        logger.error(f"произошла ошибка {e}")
        return f"произошла ошибка {e}"




# if __name__ == '__main__':
#     # tran = export_data_from_xlsx(r'C:\Users\user\Desktop\skyPro\ analysis banking transactions\data\operations.xlsx')
#     tran = pd.DataFrame(
#         {
#             "Дата операции": [
#                 "21.12.2021 01:06:22",
#                 "20.12.2021 12:06:22",
#                 "01.12.2021 01:06:22",
#                 "31.12.2021 00:12:53",
#                 "08.09.2024 00:12:53",
#             ],
#             "Номер карты": ["*7197", "*7197", "*5091", "*5091", "*7197"],
#             "Сумма платежа": [-160.89, 5000, 23.60, -645.78, 1588.36],
#             "Категория": ["Переводы", "Развлечения", "Переводы", "Такси", "Госуслуги"],
#             "Описание": [
#                 "Перевод Кредитная карта. ТП 10.2 RUR",
#                 "sevs.eduerp.ru",
#                 "Дмитрий Р.",
#                 "Яндекс Такси",
#                 "Почта России",
#             ],
#             "Дата платежа": ["21.12.2021", "20.12.2021", "01.12.2021", "31.12.2021", "08.09.2024"],
#         }
#     )
#     print(spending_by_weekday(tran, '2022-01-21 17:39:33'))
