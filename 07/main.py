# Лабораторная работа N7. Вариант 7
# Автосервис: рефакторинг по SOLID
#
# Этап 1 - "плохая" версия с нарушением SOLID
# Этап 2 - отрефакторенная версия с принципами SOLID

from abc import ABC, abstractmethod
from typing import Protocol

# =====================================================
# ЭТАП 1. Проблемная архитектура (с нарушениями SOLID)
# =====================================================
class BadAutoService:
    """Класс нарушает SRP и DIP: делает и БД, и логику, и отчёт."""
    def __init__(self):
        self.orders = []
        self.next_id = 1

    def create_order(self, car, work):
        # Нарушение DIP: жёстко заданное хранилище
        self.orders.append({"id": self.next_id, "car": car, "work": work})
        self.next_id += 1
        # Нарушение SRP: бизнес-логика и вывод в консоль в одном классе
        print(f"Создан заказ {self.next_id - 1}")

    def calculate(self, order, order_type):
        # Нарушение OCP: if/elif, который растёт при новых типах работ
        if order_type == "diagnostics":
            return order["work"] * 1
        elif order_type == "maintenance":
            return order["work"] * 2
        elif order_type == "repair":
            return order["work"] * 3
        else:
            return 0

    def save_report(self, orders):
        # Также нарушение SRP
        with open("report.txt", "w", encoding="utf-8") as file:
            file.write(f"Всего заказов: {len(orders)}\n")


# =====================================================
# ЭТАП 2. Отрефакторенная SOLID-архитектура
# =====================================================

# --- SRP: отдельные классы-сущности ---
class Car:
    def __init__(self, reg_number, brand, model):
        self.reg_number = reg_number
        self.brand = brand
        self.model = model


class RepairOrder:
    def __init__(self, order_id, car, works):
        self.order_id = order_id
        self.car = car
        self.works = works  # количество часов работ
        self.status = "created"


# --- LSP + OCP: абстракция типа ремонтных работ ---
class RepairType(ABC):
    @abstractmethod
    def cost_per_hour(self) -> float:
        ...


class Diagnostics(RepairType):
    def cost_per_hour(self):
        return 1000.0


class Maintenance(RepairType):
    def cost_per_hour(self):
        return 2000.0


class Repair(RepairType):
    def cost_per_hour(self):
        return 3000.0


# --- Repository: хранение данных (SRP, DIP) ---
class Repository(Protocol):
    def add(self, entity):
        ...

    def get_all(self):
        ...


class InMemoryRepository:
    def __init__(self):
        self._items = []
        self._next_id = 1

    def add(self, entity):
        entity.order_id = self._next_id
        self._items.append(entity)
        self._next_id += 1
        return entity

    def get_all(self):
        return self._items


# --- Сервис: бизнес-логика (SRP), зависимости через DIP ---
class AutoService:
    def __init__(self, repository: Repository):
        self.repository = repository

    def create_order(self, car, repair_type: RepairType, hours):
        order = RepairOrder(0, car, hours)
        order.repair_type = repair_type
        return self.repository.add(order)

    def calculate_cost(self, order):
        if not hasattr(order, "repair_type"):
            raise ValueError("У заказа не задан тип работ")
        return order.works * order.repair_type.cost_per_hour()

    def all_orders(self):
        return self.repository.get_all()


# --- Отдельный отчёт (SRP) ---
class ReportGenerator:
    @staticmethod
    def generate(orders):
        lines = [f"Заказ {o.order_id}: {o.car.brand} {o.car.model} - {o.status}"
                 for o in orders]
        return "\n".join(lines)


def test_solid_architecture():
    repository = InMemoryRepository()
    service = AutoService(repository)

    car1 = Car("А123ВС77", "Toyota", "Camry")
    car2 = Car("В456ЕР77", "Hyundai", "Solaris")

    order1 = service.create_order(car1, Diagnostics(), 1)
    order2 = service.create_order(car2, Repair(), 3)

    assert order1.order_id == 1
    assert order2.order_id == 2
    assert len(service.all_orders()) == 2
    assert service.calculate_cost(order1) == 1000.0
    assert service.calculate_cost(order2) == 9000.0
    assert "Toyota" in ReportGenerator.generate(service.all_orders())
    return service


def main():
    print("=== ЭТАП 1: проблемная версия ===")
    bad = BadAutoService()
    car = {"id": 1, "brand": "Toyota"}
    bad.create_order(car, 2)
    print("Стоимость (repair):", bad.calculate(bad.orders[0], "repair"))

    print("\n=== ЭТАП 2: SOLID-версия ===")
    service = test_solid_architecture()
    for order in service.all_orders():
        print(f"Заказ {order.order_id}: "
              f"стоимость = {service.calculate_cost(order):.2f} ₽")
    print("\nОтчёт:\n", ReportGenerator.generate(service.all_orders()))
    print("\nВсе тесты SOLID-архитектуры пройдены.")


if __name__ == "__main__":
    main()