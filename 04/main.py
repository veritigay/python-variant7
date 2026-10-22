# Лабораторная работа N4. Вариант 7
# Банковские счета: модули, JSON-хранилище, пользовательские исключения
#
# Структура проекта:
#   exceptions.py  - пользовательское исключение InsufficientFundsError
#   models.py      - класс BankAccount + сериализация
#   storage.py     - сохранение/загрузка JSON и экспорт CSV
#   services.py    - бизнес-логика
#   main.py        - консольное меню

# ============ exceptions.py ============

class InsufficientFundsError(Exception):
    """Исключение при недостатке средств на счёте."""
    pass


class AccountNotFoundError(Exception):
    """Исключение при отсутствии счёта."""
    pass


# ============ models.py ============

class BankAccount:
    def __init__(self, number, owner, balance=0.0, account_type="текущий"):
        if balance < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self.number = number
        self.owner = owner
        self._balance = balance
        self.account_type = account_type

    @property
    def balance(self):
        return self._balance

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        self._balance += amount

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("Сумма списания должна быть положительной")
        if amount > self._balance:
            raise InsufficientFundsError(
                f"Недостаточно средств на счёте {self.number}"
            )
        self._balance -= amount

    def to_dict(self):
        return {
            "number": self.number,
            "owner": self.owner,
            "balance": self._balance,
            "account_type": self.account_type,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["number"],
            data["owner"],
            data["balance"],
            data["account_type"],
        )

    def __str__(self):
        return (f"Счёт {self.number} ({self.account_type}), "
                f"владелец: {self.owner}, баланс: {self._balance:.2f}")


# ============ storage.py ============

import json
import csv
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "data.json")
CSV_FILE = os.path.join(DATA_DIR, "data.csv")


def ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def save_json(accounts):
    ensure_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump([a.to_dict() for a in accounts], file,
                  ensure_ascii=False, indent=4)


def load_json():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return [BankAccount.from_dict(item) for item in data]
    except (json.JSONDecodeError, KeyError, TypeError):
        print("Ошибка: JSON-файл повреждён, загружена пустая база")
        return []


def export_csv(accounts):
    ensure_dir()
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["number", "owner", "balance", "account_type"])
        for a in accounts:
            writer.writerow([a.number, a.owner, a.balance, a.account_type])
    print(f"Экспортировано в CSV: {CSV_FILE}")


# ============ services.py ============

def find_account(accounts, number):
    for account in accounts:
        if account.number == number:
            return account
    raise AccountNotFoundError(f"Счёт {number} не найден")


# ============ main.py ============

def main():
    accounts = load_json()
    if not accounts:
        # демонстрационные данные
        accounts = [
            BankAccount("40817 1", "Иванов И.", 50000.0, "текущий"),
            BankAccount("42305 7", "Петрова А.", 120000.0, "накопительный"),
            BankAccount("40817 2", "Сидоров К.", 3000.0, "текущий"),
        ]
        save_json(accounts)

    while True:
        print("\n===== МЕНЮ =====")
        print("1. Показать счета")
        print("2. Пополнить счёт")
        print("3. Снять со счёта")
        print("4. Найти счёт")
        print("5. Сохранить JSON")
        print("6. Экспортировать CSV")
        print("0. Выход")
        choice = input("Выберите действие: ")

        if choice == "1":
            for account in accounts:
                print(account)
        elif choice == "2":
            number = input("Номер счёта: ")
            try:
                account = find_account(accounts, number)
                amount = float(input("Сумма пополнения: "))
                account.deposit(amount)
                print(f"Новый баланс: {account.balance:.2f}")
            except (ValueError, AccountNotFoundError) as error:
                print(f"Ошибка: {error}")
        elif choice == "3":
            number = input("Номер счёта: ")
            try:
                account = find_account(accounts, number)
                amount = float(input("Сумма списания: "))
                account.withdraw(amount)
                print(f"Новый баланс: {account.balance:.2f}")
            except (ValueError, AccountNotFoundError, InsufficientFundsError) as error:
                print(f"Ошибка: {error}")
        elif choice == "4":
            owner = input("Владелец: ")
            matches = [a for a in accounts if owner.lower() in a.owner.lower()]
            for account in matches:
                print(account)
            if not matches:
                print("Счета не найдены")
        elif choice == "5":
            save_json(accounts)
            print("Данные сохранены")
        elif choice == "6":
            export_csv(accounts)
        elif choice == "0":
            save_json(accounts)
            break
        else:
            print("Неверный пункт меню")


if __name__ == "__main__":
    main()