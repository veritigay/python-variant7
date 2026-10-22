# Лабораторная работа N10. Вариант 7
# Автосервис - автомобили. REST API на Flask
#
# Файлы проекта:
#   models.py     - модель Car (автомобиль)
#   repository.py - хранение в памяти
#   service.py    - бизнес-логика
#   app.py        - Flask endpoints
#   client.py     - HTTP-клиент с меню
#
# Запуск: python app.py  (затем в отдельном терминале python client.py)

from dataclasses import dataclass, asdict


# ============ models.py ============
@dataclass
class Car:
    id: int = 0
    brand: str = ""
    model: str = ""
    year: int = 0
    owner: str = ""
    mileage: int = 0
    category: str = ""
    condition: str = "good"  # good / repair / need_diagnostics

    def to_dict(self):
        return asdict(self)


# ============ exceptions.py ============
class CarNotFoundError(Exception):
    pass


class ValidationError(Exception):
    pass


# ============ repository.py ============
class CarRepository:
    def __init__(self):
        self._cars = {}
        self._next_id = 1

    def get_all(self):
        return list(self._cars.values())

    def get_by_id(self, car_id):
        return self._cars.get(car_id)

    def create(self, car):
        car.id = self._next_id
        self._next_id += 1
        self._cars[car.id] = car
        return car

    def update(self, car):
        self._cars[car.id] = car
        return car

    def delete(self, car_id):
        if car_id not in self._cars:
            raise CarNotFoundError(f"Автомобиль {car_id} не найден")
        del self._cars[car_id]


# ============ service.py ============
class CarService:
    def __init__(self, repository):
        self.repository = repository

    def list_cars(self, category=None, condition=None, brand=None,
                  min_year=None, sort=None, order="asc", limit=None, offset=0):
        cars = self.repository.get_all()
        if category:
            cars = [c for c in cars if c.category.lower() == category.lower()]
        if condition:
            cars = [c for c in cars if c.condition.lower() == condition.lower()]
        if brand:
            cars = [c for c in cars if brand.lower() in c.brand.lower()]
        if min_year:
            cars = [c for c in cars if c.year >= int(min_year)]

        if sort in ("year", "mileage"):
            reverse = order == "desc"
            cars = sorted(cars, key=lambda c: getattr(c, sort), reverse=reverse)

        return cars[offset:offset + limit] if limit else cars

    def get_car(self, car_id):
        car = self.repository.get_by_id(car_id)
        if not car:
            raise CarNotFoundError(f"Автомобиль {car_id} не найден")
        return car

    def create_car(self, data):
        self._validate(data)
        car = Car(
            brand=data["brand"],
            model=data["model"],
            year=int(data["year"]),
            owner=data["owner"],
            mileage=int(data.get("mileage", 0)),
            category=data.get("category", ""),
            condition=data.get("condition", "good"),
        )
        return self.repository.create(car)

    def update_car(self, car_id, data):
        existing = self.get_car(car_id)
        merged = self._merge(existing, data)
        self._validate(merged.to_dict())
        return self.repository.update(merged)

    def patch_car(self, car_id, data):
        existing = self.get_car(car_id)
        merged = self._merge(existing, data)
        self._validate(merged.to_dict())
        return self.repository.update(merged)

    def delete_car(self, car_id):
        self.repository.delete(car_id)

    def cars_in_repair(self):
        """Специализированный endpoint: автомобили в ремонте."""
        cars = [c for c in self.repository.get_all()
                if c.condition in ("repair", "need_diagnostics")]
        return [c.to_dict() for c in cars]

    def statistics(self):
        cars = self.repository.get_all()
        if not cars:
            return {"count": 0}
        avg_mileage = sum(c.mileage for c in cars) / len(cars)
        avg_year = sum(c.year for c in cars) / len(cars)
        return {
            "count": len(cars),
            "average_mileage": round(avg_mileage, 1),
            "average_year": round(avg_year, 1),
            "cars_in_repair": len([c for c in cars if c.condition == "repair"]),
        }

    def _validate(self, data):
        if not data.get("brand") or not data.get("model"):
            raise ValidationError("Марка и модель обязательны")
        if data.get("mileage", 0) < 0:
            raise ValidationError("Пробег не может быть отрицательным")
        if data.get("year", 0) < 1885:
            raise ValidationError("Некорректный год выпуска")

    def _merge(self, car, data):
        allowed = ["brand", "model", "year", "owner", "mileage", "category", "condition"]
        result = Car(
            id=car.id,
            brand=data.get("brand", car.brand),
            model=data.get("model", car.model),
            year=int(data.get("year", car.year)),
            owner=data.get("owner", car.owner),
            mileage=int(data.get("mileage", car.mileage)),
            category=data.get("category", car.category),
            condition=data.get("condition", car.condition),
        )
        return result


# ============ app.py (Flask) ============
from flask import Flask, jsonify, request

app = Flask(__name__)
service = CarService(CarRepository())

# демо-данные
for data in [
    {"brand": "Toyota", "model": "Camry", "year": 2018, "owner": "Иванов",
     "mileage": 95000, "category": "sedan", "condition": "good"},
    {"brand": "Hyundai", "model": "Solaris", "year": 2015, "owner": "Петрова",
     "mileage": 120000, "category": "sedan", "condition": "repair"},
    {"brand": "Kia", "model": "Rio", "year": 2020, "owner": "Сидоров",
     "mileage": 50000, "category": "hatchback", "condition": "good"},
    {"brand": "Toyota", "model": "Rav4", "year": 2016, "owner": "Кузнецов",
     "mileage": 150000, "category": "suv", "condition": "need_diagnostics"},
]:
    service.create_car(data)


@app.errorhandler(CarNotFoundError)
def not_found(error):
    return jsonify({"error": str(error), "code": "CAR_NOT_FOUND"}), 404


@app.errorhandler(ValidationError)
def validation(error):
    return jsonify({"error": str(error), "code": "VALIDATION_ERROR"}), 400


@app.get("/cars")
def list_cars():
    result = service.list_cars(
        category=request.args.get("category"),
        condition=request.args.get("condition"),
        brand=request.args.get("brand"),
        min_year=request.args.get("min_year"),
        sort=request.args.get("sort"),
        order=request.args.get("order", "asc"),
        limit=request.args.get("limit", type=int),
        offset=request.args.get("offset", 0, type=int),
    )
    return jsonify([c.to_dict() for c in result])


@app.get("/cars/<int:car_id>")
def get_car(car_id):
    car = service.get_car(car_id)
    return jsonify(car.to_dict())


@app.post("/cars")
def create_car():
    data = request.get_json(silent=True) or {}
    car = service.create_car(data)
    return jsonify(car.to_dict()), 201


@app.put("/cars/<int:car_id>")
def update_car(car_id):
    data = request.get_json(silent=True) or {}
    car = service.update_car(car_id, data)
    return jsonify(car.to_dict())


@app.patch("/cars/<int:car_id>")
def patch_car(car_id):
    data = request.get_json(silent=True) or {}
    car = service.patch_car(car_id, data)
    return jsonify(car.to_dict())


@app.delete("/cars/<int:car_id>")
def delete_car(car_id):
    service.delete_car(car_id)
    return "", 204


@app.get("/cars/in-repair")
def cars_in_repair():
    return jsonify(service.cars_in_repair())


@app.get("/cars/statistics")
def cars_statistics():
    return jsonify(service.statistics())


if __name__ == "__main__":
    app.run(port=5000, debug=True)