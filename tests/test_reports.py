import pandas as pd

from src.reports import spending_by_weekday


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
    assert spending_by_weekday(df) == "произошла ошибка 'str' object has no attribute 'loc'"
