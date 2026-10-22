# Лабораторная работа N18. Вариант 7
# Тесты: Автосервис (pytest + unittest.mock)
import sys
import os
import pytest
from unittest.mock import Mock, patch

# Путь к исходникам
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from services import AutoService, AutoRepository, Car, RepairOrder  # noqa


# ---------- Фикстуры ----------
@pytest.fixture
def repo():
    return AutoRepository()


@pytest.fixture
def service(repo):
    return AutoService(repo)


@pytest.fixture
def registered_car(service):
    return service.register_car("А123ВС77", "Toyota", "Camry", "Иванов")


@pytest.fixture
def created_order(service, registered_car):
    return service.create_order(registered_car.car_id, 2, 2000)


# ---------- Unit-тесты: регистрация авто ----------
def test_register_car_success(service):
    car = service.register_car("В456ЕР77", "Hyundai", "Solaris", "Петрова")
    assert car.car_id == 1
    assert car.brand == "Hyundai"
    assert service.repository.find_car(car.car_id) is not None


def test_register_car_without_brand_raises(service):
    with pytest.raises(ValueError, match="обязательны"):
        service.register_car("В456ЕР77", "", "Solaris", "Петрова")


def test_register_car_without_reg_raises(service):
    with pytest.raises(ValueError):
        service.register_car("", "Hyundai", "Solaris", "Петрова")


# ---------- Unit-тесты: создание заказа ----------
def test_create_order_success(service, registered_car):
    order = service.create_order(registered_car.car_id, 3, 2000)
    assert order.works == 3
    assert order.hour_rate == 2000


def test_create_order_negative_hours_raises(service, registered_car):
    with pytest.raises(ValueError):
        service.create_order(registered_car.car_id, -1, 2000)


def test_create_order_missing_car_raises(service):
    with pytest.raises(ValueError, match="не найден"):
        service.create_order(999, 3, 2000)


# ---------- Параметризованные тесты ----------
@pytest.mark.parametrize("works,rate,expected", [
    (1, 2000, 2000),
    (2, 1500, 3000),
    (3, 3000, 9000),
    (0, 1000, 0),
])
def test_calculate_cost_parametrized(service, registered_car, works, rate, expected):
    order = service.create_order(registered_car.car_id, works, rate)
    assert service.calculate_cost(order.order_id) == expected


def _go_to(service, order, target):
    """Последовательно переводит заказ к целевому статусу."""
    flow = ["created", "diagnosis", "in_progress", "ready", "issued"]
    for status in flow:
        if order.status == target:
            return
        if order.status == status:
            continue
        service.change_status(order.order_id, status)


@pytest.mark.parametrize("from_status,to_status,valid", [
    ("created", "diagnosis", True),
    ("created", "ready", False),   # нельзя перескочить
    ("ready", "issued", True),
    ("created", "issued", False),
])
def test_status_transitions(service, registered_car, from_status, to_status, valid):
    order = service.create_order(registered_car.car_id, 2, 2000)
    _go_to(service, order, from_status)
    if valid:
        service.change_status(order.order_id, to_status)
        assert order.status == to_status
    else:
        with pytest.raises(ValueError):
            service.change_status(order.order_id, to_status)


def test_invalid_status_raises(service, created_order):
    with pytest.raises(ValueError, match="Некорректный статус"):
        service.change_status(created_order.order_id, "unknown")


# ---------- Boundery: граничные значения ----------
def test_zero_hours_allowed(service, registered_car):
    order = service.create_order(registered_car.car_id, 0, 1000)
    assert service.calculate_cost(order.order_id) == 0


def test_negative_rate_raises(service, registered_car):
    with pytest.raises(ValueError):
        service.create_order(registered_car.car_id, 2, -1)


# ---------- Mock/patch: изоляция от Repository ----------
def test_service_uses_repository_save_car():
    repo = Mock()
    repo.find_car.return_value = None
    service = AutoService(repo)
    service.register_car("А123ВС77", "Toyota", "Camry", "Иванов")
    # Проверяем, что Repository.save_car был вызван
    assert repo.save_car.called
    assert repo.save_car.call_count == 1


def test_service_uses_repository_find_car():
    repo = Mock()
    car = Car(1, "А123ВС77", "Toyota", "Camry", "Иванов")
    repo.find_car.return_value = car
    service = AutoService(repo)
    order = service.create_order(1, 2, 2000)
    repo.find_car.assert_called_once_with(1)
    assert order.car is car


def test_missing_car_with_mock_raises():
    repo = Mock()
    repo.find_car.return_value = None
    service = AutoService(repo)
    with pytest.raises(ValueError):
        service.create_order(5, 2, 2000)
    repo.find_car.assert_called_once_with(5)


# ---------- Интеграционные тесты (Repository + Service + SQLite) ----------
def test_integration_register_and_order(service, registered_car, created_order):
    car = service.repository.find_car(registered_car.car_id)
    order = service.repository.find_order(created_order.order_id)
    assert car is not None
    assert order is not None
    assert order.car.brand == "Toyota"


def test_integration_full_flow(service, registered_car):
    order = service.create_order(registered_car.car_id, 4, 1500)
    _go_to(service, order, "ready")
    assert order.status == "ready"
    assert service.calculate_cost(order.order_id) == 6000


# ---------- Граничные значения (доп.) ----------
def test_empty_string_reg_raises(service):
    with pytest.raises(ValueError):
        service.register_car("   ", "Toyota", "Camry", "Иванов")


if __name__ == "__main__":
    pass