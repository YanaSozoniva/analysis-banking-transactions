import json
import tempfile

import pandas as pd
import pytest

from src.reports import spending_by_weekday, write_to_file


def test_spending_by_weekday_success(df_test):
    """Тестирование успешного выполнения по заданной дате"""

    assert spending_by_weekday(df_test, "2022-01-21 17:39:33") == (
        '[{"weekdays":"Friday","spending":645.78},' '{"weekdays":"Tuesday","spending":160.89}]'
    )


def test_spending_by_weekday_default(df_test):
    """Тестирование успешного выполнения, если дата не заданна"""

    assert spending_by_weekday(df_test) == '[{"weekdays":"Sunday","spending":1588.36}]'


def test_spending_by_weekday_zero_df():
    """Тестирование при пустом DataFrame"""
    df = pd.DataFrame()
    assert spending_by_weekday(df) == None


def test_write_to_file_success_default_file():
    """Тестирует запись в файл (по умолчанию) после успешного выполнения"""

    @write_to_file()
    def my_function(x, y):
        return {'x': x, 'y': y}

    my_function(2, 3)

    file_path = 'reports.json'
    with open(file_path, "r", encoding="utf-8") as file:
        result = json.load(file)

    assert result == {"x": 2, "y": 3}


def test_write_to_file_success():
    """Тестирует запись в указанный файл после успешного выполнения"""

    @write_to_file('test_reports.json')
    def my_function(x, y):
        return {'x': x, 'y': y}

    my_function(2, 3)

    file_path = 'test_reports.json'
    with open(file_path, "r", encoding="utf-8") as file:
        result = json.load(file)

    assert result == {"x": 2, "y": 3}
