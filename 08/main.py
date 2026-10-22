# Лабораторная работа N8. Вариант 7
# Автосервис: паттерны проектирования
# Repository, Factory, Strategy, Command + история команд (undo)
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol


# ---------- Enum статусов ----------
class OrderStatus(str, Enum):
    CREATED = "created"
    DIAGNOSIS = "diagnosis"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    ISSUED = "issued"


# ---------- Model ----------
@dataclass
class ServiceItem:
    """Вид ремонтной услуги (создаётся Factory)."""
    name: str
    base_rate: float

    def cost(self, hours: float) -> float:
        return self.base_rate * hours


@dataclass
class RepairOrder:
    id: int
    car_brand: str
    car_model: str
    service: ServiceItem
    hours: float
    status: OrderStatus = OrderStatus.CREATED

    def calculate(self, strategy) -> float:
        return strategy.calculate(self)


# ---------- Repository ----------
class Repository(Protocol):
    def add(self, entity):
        ...

    def get_all(self):
        ...

    def delete(self, entity_id):
        ...


class InMemoryRepository:
    def __init__(self):
        self._items = []
        self._next_id = 1

    def add(self, entity):
        entity.id = self._next_id
        self._items.append(entity)
        self._next_id += 1
        return entity

    def get_all(self):
        return self._items

    def delete(self, entity_id):
        self._items = [i for i in self._items if i.id != entity_id]


# ---------- Factory ----------
class ServiceFactory:
    @staticmethod
    def create(service_type):
        st = service_type.lower()
        if st in ("diagnostics", "диагностика"):
            return ServiceItem("Диагностика", 1000.0)
        if st in ("maintenance", "то"):
            return ServiceItem("Техническое обслуживание", 2000.0)
        if st in ("repair", "ремонт"):
            return ServiceItem("Ремонт", 3000.0)
        raise ValueError(f"Неизвестный тип услуги: {service_type}")


# ---------- Strategy ----------
class PricingStrategy(Protocol):
    def calculate(self, order: RepairOrder) -> float:
        ...


class StandardPricing:
    def calculate(self, order):
        return order.service.cost(order.hours)


class UrgentPricing:
    def calculate(self, order):
        return order.service.cost(order.hours) * 1.5


class CorporatePricing:
    def calculate(self, order):
        return order.service.cost(order.hours) * 0.8


class PricingFactory:
    @staticmethod
    def create(strategy_type):
        st = strategy_type.lower()
        if st in ("standard", "стандартный"):
            return StandardPricing()
        if st in ("urgent", "срочный"):
            return UrgentPricing()
        if st in ("corporate", "корпоративный"):
            return CorporatePricing()
        raise ValueError(f"Неизвестная стратегия: {strategy_type}")


# ---------- Command ----------
class Command(Protocol):
    def execute(self):
        ...

    def undo(self):
        ...


class CreateOrderCommand:
    def __init__(self, repository, car_brand, car_model, service, hours):
        self.repository = repository
        self.car_brand = car_brand
        self.car_model = car_model
        self.service = service
        self.hours = hours
        self.created = None

    def execute(self):
        self.created = self.repository.add(
            RepairOrder(0, self.car_brand, self.car_model,
                        self.service, self.hours)
        )
        return self.created

    def undo(self):
        if self.created:
            self.repository.delete(self.created.id)


# ---------- Сервис ----------
class AutoService:
    def __init__(self, repository: Repository):
        self.repository = repository
        self.history = []

    def execute(self, command: Command):
        result = command.execute()
        self.history.append(command)
        return result

    def undo(self):
        if not self.history:
            return "Нечего отменять"
        command = self.history.pop()
        command.undo()
        return "Последняя операция отменена"

    def calculate_order(self, order, strategy):
        return strategy.calculate(order)


def main():
    repo = InMemoryRepository()
    service = AutoService(repo)

    # Factory создаёт услугу
    service_diag = ServiceFactory.create("diagnostics")
    service_repair = ServiceFactory.create("repair")

    # Command создаёт заказы + история
    order1 = service.execute(CreateOrderCommand(repo, "Toyota", "Camry",
                                                service_diag, 2))
    order2 = service.execute(CreateOrderCommand(repo, "Hyundai", "Solaris",
                                                service_repair, 3))

    print("Созданные заказы:")
    for order in repo.get_all():
        print(f"  #{order.id} {order.car_brand} {order.car_model} - "
              f"{order.service.name}, {order.hours} ч")

    # Strategy: разные способы расчёта
    print("\nРасчёт стоимости (смена стратегии):")
    strategy = PricingFactory.create("standard")
    print(f"  #1 стандартный: {service.calculate_order(order1, strategy):.2f} ₽")
    strategy = PricingFactory.create("urgent")
    print(f"  #1 срочный: {service.calculate_order(order1, strategy):.2f} ₽")
    strategy = PricingFactory.create("corporate")
    print(f"  #2 корпоративный: {service.calculate_order(order2, strategy):.2f} ₽")

    # История команд / undo
    print(f"\nИстория команд: {len(service.history)}")
    print(service.undo())
    print(f"После undo заказов: {len(repo.get_all())}")

    # Тесты паттернов
    assert len(repo.get_all()) == 1
    assert order1.calculate(StandardPricing()) == 2000.0
    assert order1.calculate(UrgentPricing()) == 3000.0
    factory_repr = ServiceFactory.create("repair")
    assert factory_repr.name == "Ремонт"
    print("\nВсе проверки паттернов пройдены.")


if __name__ == "__main__":
    main()