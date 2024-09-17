from unittest.mock import patch

from src.views import get_data_for_home_page


@patch("src.views.get_currency_rates")
@patch("src.views.get_stocks")
@patch("src.views.json.dumps")
def test_get_data_for_home_page_success(mock_json_dumps, mock_get_currency_rates, mock_get_stocks, result_json):
    """Тестирование успешного формирования JSON-ответа для страницы «Главная»"""
    mock_get_currency_rates.return_value = [{"currency": "USD", "rate": 91.0}, {"currency": "EUR", "rate": 100.52}]
    mock_get_stocks.return_value = [
        {"stock": "AAPL", "price": 220.11},
        {"stock": "AMZN", "price": 179.55},
        {"stock": "GOOGL", "price": 148.66},
        {"stock": "MSFT", "price": 414.2},
        {"stock": "TSLA", "price": 226.17},
    ]
    mock_json_dumps.return_value = result_json
    result = get_data_for_home_page("2021-12-20 06:20:03")
    assert result == result_json
    mock_json_dumps.assert_called_once()
