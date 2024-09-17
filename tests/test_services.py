import pandas as pd

from src.services import search_transfers_to_individuals


def test_search_transfers_to_individuals_success(df_test):
    """Тестирование успешной выдачи JSON со всеми транзакциями, которые относятся к переводам физ. лицам."""
    assert search_transfers_to_individuals(df_test) == (
        '[{"Дата операции":"01.12.2021 01:06:22",'
        '"Номер карты":"*5091",'
        '"Сумма платежа":23.6,"Категория":"Переводы",'
        '"Описание":"Дмитрий Р.","Дата платежа":"01.12.2021"}]'
    )


def test_search_transfers_to_individuals_zero_df():
    """Тестирование при пустом DataFrame"""
    df = pd.DataFrame()
    assert search_transfers_to_individuals(df) == "Произошла ошибка 'Категория'"


def test_search_transfers_to_individuals_not_found_cat():
    """Тестирование при отсутствии нужной категории"""
    data = {
        "Категория": ["Супермаркеты", "Фастфуд", "Супермаркеты", "Госуслуги"],
        "Описание": ["Иванов И.", "Петров П.", "Сидоров.", "Петров П."],
    }
    df = pd.DataFrame(data)
    assert search_transfers_to_individuals(df) == "[]"


def test_search_transfers_to_individuals_not_found_name():
    """Тестирование при отсутствии в описании подходящего шаблона"""
    data = {
        "Категория": ["Супермаркеты", "Фастфуд", "Переводы", "Госуслуги"],
        "Описание": ["Иванов И.", "Петров П.", "Сидоров.", "Петров П."],
    }
    df = pd.DataFrame(data)
    assert search_transfers_to_individuals(df) == "[]"
