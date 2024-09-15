import os
from src.views import get_data_for_home_page
from src.utils import filter_by_date_range, export_data_from_xlsx
from src.reports import spending_by_weekday
from src.services import search_transfers_to_individuals


def main():
    """Главная функция приложения"""
    answer_user = int(
        input(
            """Привет! Добро пожаловать в программу работы с банковскими транзакциями.
Выберите необходимый пункт меню:
    1. Получить информацию к страницы Главная 
    2. Получить информацию о переводах физ. лицам
    3. Получить отчет по тратам по дням недели за три последних месяца от указанной даты\n"""
        )
    )

    transaction = export_data_from_xlsx(
        r"data\operations.xlsx")

    if answer_user == 1:
        print('''Уточните за какой месяц нужно вывести информацию? (дата вводится в формате  YYYY-MM-DD HH:MM:SS - 
указывайте по какой день нужна информация с начала месяца)
(Если вас интересует текущий месяц, оставьте поле пустым)\n''')
        date = input()
        result = get_data_for_home_page(date)

    elif answer_user == 2:

        services = input("Информация нужна за определенный месяц? да/нет").lower()

        if services == 'да':
            date_ser = input('''Введите конечную дату, по которую будет выводиться информация с начала указанного месяца
                             (дата вводится в формате  YYYY-MM-DD HH:MM:SS)\n''')
            transaction = filter_by_date_range(transaction, date_ser)

        result = search_transfers_to_individuals(transaction)

    else:
        date_report = input("""Уточните за какие  месяц нужно вывести информацию? (дата вводится в формате  YYYY-MM-DD HH:MM:SS - 
указывайте по какой день нужна информация за последние 3 месяца)
(Если вас интересует текущий месяц, оставьте поле пустым)\n""")
        result = spending_by_weekday(transaction, date_report)

    print(result)


if __name__ == "__main__":
    main()
