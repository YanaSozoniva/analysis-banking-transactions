import json

from src.utils import *

from typing import Iterable
import logging
from os import getcwd
from os.path import dirname


PATH_LOG = dirname(getcwd())


logging.basicConfig(
    encoding="utf-8",
    filemode="w",
    filename=PATH_LOG + r"\logs\views.log",
    format="%(asctime)s:%(filename)s:%(funcName)s %(levelname)s: %(message)s",
    level=logging.DEBUG,
)

logger = logging.getLogger("views")


def get_data_for_home_page(date: str) -> Iterable | str:
    """Основная функция для генерации JSON-ответа для страницы «Главная»
    (датой и время в формате YYYY-MM-DD HH:MM:SS)"""
    try:
        logger.info('Получение данных из excel, фильтрация данных')
        main_info = {}
        card_info = export_data_from_xlsx(
            r'C:\Users\user\Desktop\skyPro\ analysis banking transactions\data\operations.xlsx')
        card_info = filter_by_date_range(card_info, date)
        card_info_list = get_card_information(card_info)

        logger.info('Формирование словаря с данными')
        main_info['greeting'] = get_greetings()
        main_info['cards'] = card_info_list
        main_info['top_transactions'] = get_top_transactions_by_amount(card_info)
        main_info['currency_rates'] = get_currency_rates()
        main_info['stock_prices'] = get_stocks()

        logger.info('Сериализация')
        main_info_json = json.dumps(main_info, indent=4, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Произошла ошибка {e}")
        return f"Произошла ошибка {e}"
    else:
        logger.info("Вывод json-ответа")
        return main_info_json
#
#
# if __name__ == '__main__':
#     print(get_data_for_home_page('2021-12-20 06:20:03'))
