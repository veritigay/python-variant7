# Лабораторная работа N6. Вариант 7
# Автосервис: декораторы, dataclass, Enum, Protocol, интроспекция,
# контекстный менеджер, обработка исключений
import time
from functools import wraps
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol


# ---------- Enum статусов ремонта ----------
class RepairStatus(str, Enum):
    ACCEPTED = "принят"
    DIAGNOSIS = "диагностируется"
    IN_PROGRESS = "ремонтируется"
    READY = "готов"
    ISSUED = "выдан"


# ---------- Пользовательское исключение ----------
class EntityNotFoundError(Exception):
    pass


# ---------- Декораторы ----------
def log_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"[LOG] вызван метод {func.__name__}()")
        return func(*args, **kwargs)
    return wrapper


def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"[PERFORMANCE] {func.__name__}: {elapsed:.4f} sec")
        return result
    return wrapper


def repeat(count):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = None
            for _ in range(count):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator


# ---------- Protocol ----------
class Repairable(Protocol):
    def repair_cost(self) -> float:
        ...


# ---------- Контекстный менеджер ----------
class OperationLogger:
    """Логирует начало и завершение операции."""
    def __enter__(self):
        print("[CTX] Начало операции")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            print(f"[CTX] Завершение операции с ошибкой: {exc_value}")
        else:
            print("[CTX] Завершение операции успешно")
        return False


# ---------- Базовый класс ----------
@dataclass
class Part:
    name: str
    price: float


@dataclass
class Car:
    reg_number: str
    brand: str
    model: str
    owner: str
    parts_replaced: list[Part] = field(default_factory=list)


class Repair:
    """Ремонт автомобиля (композиция: ремонт содержит автомобиль и запчасти)."""
    def __init__(self, repair_id: int, car: Car, status: RepairStatus = RepairStatus.ACCEPTED):
        self.repair_id = repair_id
        self._car = car
        self._status = status
        self.labor_hours = 0.0
        self.hour_rate = 1500.0

    @property
    def status(self) -> RepairStatus:
        return self._status

    def set_status(self, new_status: RepairStatus) -> None:
        self._status = new_status

    @measure_time
    def repair_cost(self) -> float:
        parts_total = sum(p.price for p in self._car.parts_replaced)
        return parts_total + self.labor_hours * self.hour_rate

    def __str__(self) -> str:
        return (f"Заказ-наряд {self.repair_id}: {self._car.brand} {self._car.model} "
                f"({self._car.reg_number}), статус: {self._status.value}, "
                f"стоимость: {self.repair_cost():.2f} ₽")


class AutoService:
    def __init__(self):
        self.repairs: list[Repair] = []

    @log_call
    def add_repair(self, repair: Repair) -> None:
        self.repairs.append(repair)

    def find_repair(self, repair_id: int) -> Repair:
        for r in self.repairs:
            if r.repair_id == repair_id:
                return r
        raise EntityNotFoundError(f"Заказ-наряд {repair_id} не найден")

    def most_replaced_parts(self, limit: int = 3):
        """Наиболее часто заменяемые детали."""
        counters = {}
        for r in self.repairs:
            for p in r._car.parts_replaced:
                counters[p.name] = counters.get(p.name, 0) + 1
        return sorted(counters.items(), key=lambda x: x[1], reverse=True)[:limit]


def inspect_object(obj):
    """Интроспекция объекта: минимум 4 механизма."""
    print("=== ИНФОРМАЦИЯ ОБ ОБЪЕКТЕ ===")
    print("Тип:", type(obj).__name__)
    print("Является экземпляром Repair:", isinstance(obj, Repair))
    print("Атрибуты:", [a for a in dir(obj) if not a.startswith("__")])
    print("Есть статус:", hasattr(obj, "status"))
    print("Статус:", getattr(obj, "status").value)


def statistics(service: AutoService) -> dict:
    total = len(service.repairs)
    ready = sum(1 for r in service.repairs if r.status == RepairStatus.READY)
    avg_cost = (sum(r.repair_cost() for r in service.repairs) / total) if total else 0
    return {"count": total, "ready": ready, "avg_cost": round(avg_cost, 2)}


def main():
    service = AutoService()

    car1 = Car("А123ВС77", "Toyota", "Camry", "Иванов", [Part("тормозные колодки", 4500)])
    car2 = Car("В456ЕР77", "Hyundai", "Solaris", "Петрова", [Part("масляный фильтр", 800)])
    car3 = Car("К789МН77", "Kia", "Rio", "Сидоров", [Part("тормозные колодки", 4500)])

    with OperationLogger():
        r1 = Repair(1, car1)
        r1.labor_hours = 3
        r1.set_status(RepairStatus.DIAGNOSIS)
        service.add_repair(r1)

        r2 = Repair(2, car2)
        r2.labor_hours = 2
        r2.set_status(RepairStatus.READY)
        service.add_repair(r2)

        r3 = Repair(3, car3)
        r3.labor_hours = 4
        r3.set_status(RepairStatus.IN_PROGRESS)
        service.add_repair(r3)

    print("\n=== Демонстрация декораторов ===")
    @repeat(2)
    def ping():
        print("ping")
    ping()

    print("\n=== Список ремонтов ===")
    for r in service.repairs:
        print(r)

    print("\n=== Наиболее часто заменяемые детали ===")
    for name, count in service.most_replaced_parts():
        print(f"  {name}: {count} раз(а)")

    print("\n=== Статистика ===")
    print(statistics(service))

    print("\n=== Интроспекция ===")
    inspect_object(r2)

    print("\n=== Обработка исключения ===")
    try:
        service.find_repair(99)
    except EntityNotFoundError as error:
        print(f"Ошибка: {error}")

    # Демонстрация Protocol-совместимости
    def show_cost(item: Repairable) -> None:
        print(f"Стоимость: {item.repair_cost():.2f} ₽")
    show_cost(r1)


if __name__ == "__main__":
    main()