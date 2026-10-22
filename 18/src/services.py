# Лабораторная работа N18. Вариант 7
# Автосервис. Тестирование с pytest и unittest.mock.
#
# Приложение: система управления автомобилями и заявками на ремонт.
# Покрыто тестами: регистрация авто, создание заявки, назначение работ,
# изменение статуса, расчёт стоимости ремонта.
#
# Запуск тестов: pytest tests/

import os


# ================= src/models.py =================
class Car:
    """Автомобиль клиента."""
    def __init__(self, car_id, reg_number, brand, model, owner):
        self.car_id = car_id
        self.reg_number = reg_number
        self.brand = brand
        self.model = model
        self.owner = owner


class RepairOrder:
    """Заказ-наряд на ремонт."""
    VALID_STATUSES = ["created", "diagnosis", "in_progress", "ready", "issued"]

    def __init__(self, order_id, car, works, hour_rate):
        self.order_id = order_id
        self.car = car
        self.works = works          # количество часов работ
        self.hour_rate = hour_rate  # ставка за час
        self.status = "created"

    def total_cost(self):
        return self.works * self.hour_rate

    def change_status(self, new_status):
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Некорректный статус: {new_status}")
        # запрет «перескакивать» через статусы: переход только на следующий
        order_flow = self.VALID_STATUSES
        cur = order_flow.index(self.status)
        target = order_flow.index(new_status)
        if target != cur + 1:
            raise ValueError(
                f"Недопустимый переход: {self.status} -> {new_status}. "
                "Можно переводить только на следующий статус."
            )
        self.status = new_status


# ================= src/repositories.py =================
class AutoRepository:
    """Хранение автомобилей и заказов."""
    def __init__(self):
        self._cars = {}
        self._orders = {}
        self._next_car = 1
        self._next_order = 1

    def save_car(self, car):
        self._cars[car.car_id] = car

    def find_car(self, car_id):
        return self._cars.get(car_id)

    def save_order(self, order):
        self._orders[order.order_id] = order

    def find_order(self, order_id):
        return self._orders.get(order_id)

    def all_orders(self):
        return list(self._orders.values())


# ================= src/services.py =================
class AutoService:
    """Бизнес-логика (не зависит от БД напрямую)."""
    def __init__(self, repository):
        self.repository = repository
        self._car_seq = 0
        self._order_seq = 0

    def register_car(self, reg_number, brand, model, owner):
        if not reg_number.strip() or not brand.strip() or not model.strip():
            raise ValueError("Регистрационный номер, марка и модель обязательны")
        self._car_seq += 1
        car = Car(self._car_seq, reg_number, brand, model, owner)
        self.repository.save_car(car)
        return car

    def create_order(self, car_id, works, hour_rate):
        car = self.repository.find_car(car_id)
        if not car:
            raise ValueError(f"Автомобиль {car_id} не найден")
        if works < 0:
            raise ValueError("Количество часов не может быть отрицательным")
        if hour_rate < 0:
            raise ValueError("Ставка не может быть отрицательной")
        self._order_seq += 1
        order = RepairOrder(self._order_seq, car, works, hour_rate)
        self.repository.save_order(order)
        return order

    def assign_work(self, order_id, works):
        order = self.repository.find_order(order_id)
        if not order:
            raise ValueError(f"Заказ {order_id} не найден")
        order.works = works
        return order

    def change_status(self, order_id, new_status):
        order = self.repository.find_order(order_id)
        if not order:
            raise ValueError(f"Заказ {order_id} не найден")
        order.change_status(new_status)
        return order

    def calculate_cost(self, order_id):
        order = self.repository.find_order(order_id)
        if not order:
            raise ValueError(f"Заказ {order_id} не найден")
        return order.total_cost()


# ================= main.py =================
def main():
    repo = AutoRepository()
    service = AutoService(repo)

    car = service.register_car("А123ВС77", "Toyota", "Camry", "Иванов")
    order = service.create_order(car.car_id, 3, 2000)
    print(f"Заказ #{order.order_id}, стоимость: {service.calculate_cost(order.order_id)}")

    service.change_status(order.order_id, "in_progress")
    print(f"Заказ #{order.order_id} переведён в '{order.status}'")


if __name__ == "__main__":
    main()