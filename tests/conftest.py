import pandas as pd
import pytest


@pytest.fixture()
def df_test():
    return pd.DataFrame(
        {
            "Дата операции": [
                "21.12.2021 01:06:22",
                "20.12.2021 12:06:22",
                "01.12.2021 01:06:22",
                "31.12.2021 00:12:53",
                "08.09.2024 00:12:53",
            ],
            "Номер карты": ["*7197", "*7197", "*5091", "*5091", "*7197"],
            "Сумма платежа": [-160.89, 5000, 23.60, -645.78, -1588.36],
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


@pytest.fixture()
def result_json():
    return {
        "greeting": "Доброе утро",
        "cards": [
            {"last_digits": "4556", "total_spent": 2547.1, "cashback": 25.47},
            {"last_digits": "5091", "total_spent": 10133.09, "cashback": 101.33},
            {"last_digits": "7197", "total_spent": 12689.61, "cashback": 126.9},
        ],
        "top_transactions": [
            {"date": "16.12.2021", "amount": -14216.42, "category": "ЖКХ", "description": "ЖКУ Квартира"},
            {"date": "02.12.2021", "amount": -5510.8, "category": "Каршеринг", "description": "Ситидрайв"},
            {"date": "14.12.2021", "amount": -5000.0, "category": "Переводы", "description": "Светлана Т."},
            {
                "date": "05.12.2021",
                "amount": 3500.0,
                "category": "Пополнения",
                "description": "Внесение наличных через банкомат Тинькофф",
            },
            {"date": "04.12.2021", "amount": -3499.0, "category": "Электроника и техника", "description": "DNS"},
        ],
        "currency_rates": [{"currency": "USD", "rate": 91.0}, {"currency": "EUR", "rate": 100.52}],
        "stock_prices": [
            {"stock": "AAPL", "price": 220.11},
            {"stock": "AMZN", "price": 179.55},
            {"stock": "GOOGL", "price": 148.66},
            {"stock": "MSFT", "price": 414.2},
            {"stock": "TSLA", "price": 226.17},
        ],
    }
