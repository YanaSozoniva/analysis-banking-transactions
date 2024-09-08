from datetime import datetime
from unittest.mock import patch

import pytest
from freezegun import freeze_time

from src.utils import export_data_from_xlsx, get_greetings


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
def test_get_greeting___(mock_datetime):
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
