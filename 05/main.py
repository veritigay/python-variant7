# Лабораторная работа N5. Вариант 7
# Банковские счета: функциональные возможности Python
# (map, filter, sorted, any, all, lambda, comprehension, генераторы)
#
# Сущность (вариант 7): банковский счёт (владелец, номер, баланс, тип).
# Реализовано: фильтрация счетов с положительным балансом, получение балансов,
# сортировка по балансу, расчёт общего баланса, проверка наличия
# отрицательных счетов, генератор счетов определённого типа.

from dataclasses import dataclass


@dataclass
class Account:
    """Банковский счёт."""
    owner: str
    number: str
    balance: float
    account_type: str

    def __str__(self):
        return (f"{self.owner}: {self.number} ({self.account_type}), "
                f"баланс {self.balance:.2f}")


# ----------------- Функции высшего порядка -----------------
def filter_objects(objects, predicate):
    """Универсальная фильтрация через filter()."""
    return list(filter(predicate, objects))


def transform_objects(objects, operation):
    """Универсальное преобразование через map()."""
    return list(map(operation, objects))


def sort_objects(objects, key_function, reverse=False):
    """Универсальная сортировка через sorted(key=...)."""
    return sorted(objects, key=key_function, reverse=reverse)


# ----------------- Конкретные операции по варианту -----------------
def positive_balance_filter(accounts):
    """Фильтрация счетов с положительным балансом (filter + lambda)."""
    return filter_objects(accounts, lambda acc: acc.balance > 0)


def get_balances(accounts):
    """Получение балансов всех счетов (map + lambda)."""
    return transform_objects(accounts, lambda acc: acc.balance)


def sort_by_balance(accounts, reverse=True):
    """Сортировка по балансу."""
    return sort_objects(accounts, lambda acc: acc.balance, reverse=reverse)


def total_balance(accounts):
    """Общий баланс всех счетов (sum + generator expression)."""
    return sum(acc.balance for acc in accounts)


def has_negative(accounts):
    """Проверка наличия отрицательных счетов (any)."""
    return any(acc.balance < 0 for acc in accounts)


def all_types_valid(accounts, allowed_types):
    """Проверка, что все счета имеют корректный тип (all)."""
    return all(acc.account_type in allowed_types for acc in accounts)


def accounts_by_type(accounts, account_type):
    """Генератор счетов заданного типа."""
    for acc in accounts:
        if acc.account_type == account_type:
            yield acc


def unique_types(accounts):
    """Множество уникальных типов счетов (set comprehension)."""
    return {acc.account_type for acc in accounts}


def main():
    # исходные данные
    accounts = [
        Account("Иванов", "4081701", 50000.0, "текущий"),
        Account("Петрова", "4230507", 120000.0, "накопительный"),
        Account("Сидоров", "4081702", -3000.0, "текущий"),
        Account("Кузнецов", "4230508", 75000.0, "накопительный"),
        Account("Орлов", "4081703", 0.0, "текущий"),
    ]

    print("=== Исходные счета ===")
    for acc in accounts:
        print(" ", acc)

    print("\n=== Счета с положительным балансом (filter) ===")
    for acc in positive_balance_filter(accounts):
        print(" ", acc)

    print("\n=== Балансы всех счетов (map) ===")
    print(" ", get_balances(accounts))

    print("\n=== Сортировка по балансу (убыв., sorted+lambda) ===")
    for acc in sort_by_balance(accounts):
        print(" ", acc)

    print("\n=== Статистика ===")
    print(f"  Общий баланс: {total_balance(accounts):.2f}")
    print(f"  Наличие отрицательных счетов: {has_negative(accounts)}")
    allowed = {"текущий", "накопительный", "депозит"}
    print(f"  Все счета имеют корректный тип: {all_types_valid(accounts, allowed)}")

    print("\n=== Уникальные типы счетов (set comprehension) ===")
    print(" ", unique_types(accounts))

    print("\n=== Генератор: накопительные счета ===")
    for acc in accounts_by_type(accounts, "накопительный"):
        print(" ", acc)


if __name__ == "__main__":
    main()