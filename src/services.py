
from typing import Iterable

from pandas import DataFrame

from src.logger import logger_setup

logger = logger_setup()


def search_transfers_to_individuals(df: DataFrame) -> Iterable:
    """Функция возвращает JSON со всеми транзакциями, которые относятся к переводам физ. лицам."""
    try:
        logger.info('Выборка транзакций по Категории "Переводы"')
        transfers_df = df.loc[df["Категория"] == "Переводы"]

        logger.info("Выборка транзакций, в описании которых есть имя и первая буква фамилии с точкой")
        pattern = r"^[А-Я][а-я]+\s[А-Я]\.$"
        transfers_df = transfers_df[transfers_df["Описание"].str.match(pattern)]
        return transfers_df.to_json(orient="records", force_ascii=False)
    except Exception as e:
        logger.error(f"Произошла ошибка {e}")
        return f"Произошла ошибка {e}"





# if __name__ == "__main__":
#     data = {
#         "Категория": ["Супермаркеты", "Фастфуд", "Супермаркеты", "Переводы"],
#         "Описание": ["Иванов И.", "Петров П.", "Сидоров.", "Петров П."],
#     }
#     df = pandas.DataFrame(data)
#     print(search_transfers_to_individuals(df))
