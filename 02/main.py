# Лабораторная работа N2. Вариант 7
# Обработка заказов (коллекции: list, dict, set)

def add_order(orders):
    """Добавление заказа."""
    number = input("Номер заказа: ")
    if any(o["number"] == number for o in orders):
        print("Ошибка: заказ с таким номером уже существует")
        return
    client = input("Клиент: ")
    try:
        cost = float(input("Стоимость: "))
    except ValueError:
        print("Ошибка: введите число")
        return
    if cost < 0:
        print("Ошибка: стоимость не может быть отрицательной")
        return
    status = input("Статус: ")
    orders.append({
        "number": number,
        "client": client,
        "cost": cost,
        "status": status
    })
    print("Заказ добавлен")


def show_orders(orders):
    """Вывод всех заказов."""
    if not orders:
        print("Заказов нет")
        return
    for o in orders:
        print(f"{o['number']} | {o['client']} | {o['cost']:.2f} | {o['status']}")


def find_by_client(orders, client):
    """Поиск заказов клиента."""
    return [o for o in orders if o["client"].lower() == client.lower()]


def filter_by_status(orders, status):
    """Фильтрация по статусу."""
    return [o for o in orders if o["status"].lower() == status.lower()]


def total_sum(orders):
    """Общая сумма заказов."""
    return sum(o["cost"] for o in orders)


def average_check(orders):
    """Средний чек."""
    return total_sum(orders) / len(orders) if orders else 0


def unique_statuses(orders):
    """Множество уникальных статусов."""
    return {o["status"] for o in orders}


def sort_by_cost(orders):
    """Сортировка по стоимости (по возрастанию)."""
    return sorted(orders, key=lambda o: o["cost"])


def main():
    orders = []
    while True:
        print("\n===== МЕНЮ =====")
        print("1. Добавить заказ")
        print("2. Показать все заказы")
        print("3. Поиск заказов клиента")
        print("4. Фильтрация по статусу")
        print("5. Сортировка по стоимости")
        print("6. Статистика")
        print("7. Уникальные статусы")
        print("0. Выход")
        choice = input("Выберите действие: ")

        if choice == "1":
            add_order(orders)
        elif choice == "2":
            show_orders(orders)
        elif choice == "3":
            client = input("Клиент: ")
            result = find_by_client(orders, client)
            show_orders(result) if result else print("Заказы не найдены")
        elif choice == "4":
            status = input("Статус: ")
            result = filter_by_status(orders, status)
            show_orders(result) if result else print("Заказы не найдены")
        elif choice == "5":
            if orders:
                show_orders(sort_by_cost(orders))
        elif choice == "6":
            if orders:
                print(f"Общая сумма: {total_sum(orders):.2f}")
                print(f"Средний чек: {average_check(orders):.2f}")
                print(f"Количество заказов: {len(orders)}")
        elif choice == "7":
            statuses = unique_statuses(orders)
            print("Уникальные статусы:", ", ".join(statuses) if statuses else "нет")
        elif choice == "0":
            break
        else:
            print("Неверный пункт меню")


if __name__ == "__main__":
    main()