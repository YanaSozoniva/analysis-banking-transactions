from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest
from freezegun import freeze_time

from src.utils import (
    export_data_from_xlsx,
    filter_by_date_range,
    get_card_information,
    get_greetings,
    get_top_transactions_by_amount,
)


@freeze_time("06:00:19")
def test_get_greetings_good_morning():
    """Тестирование приветсвия утром"""
    assert get_greetings() == "Доброе утро"


@freeze_time("12:00:00")
def test_get_greetings_good_day():
    """Тестирование приветсвия днем"""
    assert get_greetings() == "Добрый день"


@freeze_time("18:00:01")
def test_get_greetings_good_evening():
    """Тестирование приветсвия вечером"""
    assert get_greetings() == "Добрый вечер"


@patch("src.utils.datetime")
def test_get_greeting_good_night(mock_datetime):
    """Тестирование приветсвия ночью"""
    mock_datetime.now.return_value = datetime(2024, 1, 1, 5, 59, 59)
    assert get_greetings() == "Доброй ночи"


@pytest.fixture
def path_exl():
    return r"C:\Users\user\Desktop\skyPro\ analysis banking transactions\data\operations.xlsx"


@pytest.fixture
def test_df():
    """Фикстура, создающая тестовый DataFrame"""

    test_dict = {
        "id": [650703.0, 3598919.0],
        "state": ["EXECUTED", "EXECUTED"],
        "date": ["2023-09-05T11:30:32Z", "2020-12-06T23:00:58Z"],
        "amount": [16210.0, 29740.0],
        "currency_name": ["Sol", "Peso"],
    }
    return test_dict


@patch("src.utils.pd.read_excel")
def test_export_data_from_xlsx(mock_reader, path_exl, test_df):
    """Тестирует успешное открытие файла"""
    mock_reader.return_value = test_df
    result = export_data_from_xlsx(path_exl)
    assert result == test_df
    mock_reader.assert_called_once()


@patch("src.utils.pd.read_excel")
def test_export_data_from_exl_zero(mock_reader, path_exl):
    """Тестирует пустой файл"""
    mock_reader.return_value = []
    result = export_data_from_xlsx(path_exl)
    assert result == []
    mock_reader.assert_called_once()


def test_export_data_from_exl_not_found_file():
    """Тестирует, если файл не найден"""
    path_file = ""
    assert export_data_from_xlsx(path_file) == "Файл не найден"


def test_filter_by_date_range_by_specified_date(df_test):
    """Тест успешной фильтрации данных по заданной дате"""
    result = filter_by_date_range(df_test, "2021-12-21 02:06:15")
    executed = pd.DataFrame(
        {
            "Дата операции": ["21.12.2021 01:06:22", "20.12.2021 12:06:22", "01.12.2021 01:06:22"],
            "Номер карты": ["*7197", "*7197", "*5091"],
            "Сумма платежа": [-160.89, 5000, 23.60],
            "Дата платежа": ["21.12.2021", "20.12.2021", "01.12.2021"],
            "Категория": ["Переводы", "Развлечения", "Переводы"],
            "Описание": ["Перевод Кредитная карта. ТП 10.2 RUR", "sevs.eduerp.ru", "Дмитрий Р."],
        }
    )
    assert result.to_dict() == executed.to_dict()


def test_filter_by_date_range_not_found_date(df_test):
    """Тест успешной фильтрации данных, если дата не указана"""
    result = filter_by_date_range(df_test)
    executed = {
        "Дата операции": {4: "08.09.2024 00:12:53"},
        "Сумма платежа": {4: 1588.36},
        "Номер карты": {4: "*7197"},
        "Дата платежа": {4: "08.09.2024"},
        "Категория": {4: "Госуслуги"},
        "Описание": {4: "Почта России"},
    }
    assert result.to_dict() == executed


def test_filter_by_date_range(df_test):
    """Тест фильтрации данных, если в указанный диапазон нет ни одной операции"""
    result = filter_by_date_range(df_test, "2022-12-22 02:06:15")
    executed = pd.DataFrame(
        {
            "Дата операции": [],
            "Номер карты": [],
            "Сумма платежа": [],
            "Категория": [],
            "Описание": [],
            "Дата платежа": [],
        }
    )
    assert result.to_dict() == executed.to_dict()


def test_filter_by_date_range_error():
    """Тест фильтрации данных при отсутствии столбца с датами"""
    df = pd.DataFrame({"Номер карты": ["*7197", "*7197", "*5091"], "Сумма платежа": [-160.89, 5000, 23.60]})
    result = filter_by_date_range(df, "2021-12-21 02:06:15")
    assert result == "Произошла ошибка 'Дата операции'"


def test_get_card_information_success(df_test):
    """Тест успешной выдачи информации по заданным параметрам"""
    result = get_card_information(df_test)
    assert result == [
        {"last_digits": "5091", "total_spent": 622.18, "cashback": 6.22},
        {"last_digits": "7197", "total_spent": 6427.47, "cashback": 64.27},
    ]


def test_get_card_information_zero_df():
    """Тест пустого dataFrame"""
    result = get_card_information(pd.DataFrame())
    assert result == "Произошла ошибка 'Номер карты'"


def test_get_top_transactions_by_amount_success(df_test):
    """Тестирование вывода топ-5 транзакций по сумме платежа"""
    execute = [
        {"date": "20.12.2021", "amount": 5000.0, "category": "Развлечения", "description": "sevs.eduerp.ru"},
        {"date": "08.09.2024", "amount": 1588.36, "category": "Госуслуги", "description": "Почта России"},
        {"date": "31.12.2021", "amount": -645.78, "category": "Такси", "description": "Яндекс Такси"},
        {
            "date": "21.12.2021",
            "amount": -160.89,
            "category": "Переводы",
            "description": "Перевод Кредитная карта. ТП 10.2 RUR",
        },
        {"date": "01.12.2021", "amount": 23.6, "category": "Переводы", "description": "Дмитрий Р."},
    ]

    assert get_top_transactions_by_amount(df_test) == execute


def test_get_top_transactions_by_amount_zero_df():
    """Тест пустого dataFrame"""
    result = get_top_transactions_by_amount(pd.DataFrame())
    assert result == "Произошла ошибка 'Категория'"
