# Лабораторная работа N14. Вариант 7
# Автосервис - автомобили. REST API на FastAPI (Pydantic, CRUD, фильтрация,
# сортировка, пагинация, поиск, статистика, асинхронный endpoint).
#
# Запуск: pip install fastapi uvicorn pydantic; uvicorn main:app --reload
# Документация (Swagger): http://127.0.0.1:8000/docs
#
# Хранение данных - в памяти (список). Для простоты не подключаем БД/Redis,
# но структура Router/Service/Repository соблюдена.

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional


app = FastAPI(title="Автосервис API", version="1.0")


# ---------- Schemas (Pydantic) ----------
class CarCreate(BaseModel):
    brand: str = Field(min_length=2)
    model: str = Field(min_length=1)
    year: int = Field(gt=1885, le=2026)
    owner: str = Field(min_length=2)
    mileage: int = Field(ge=0)
    category: str = ""
    condition: str = "good"


class CarUpdate(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    owner: Optional[str] = None
    mileage: Optional[int] = None
    category: Optional[str] = None
    condition: Optional[str] = None


class CarResponse(BaseModel):
    id: int
    brand: str
    model: str
    year: int
    owner: str
    mileage: int
    category: str
    condition: str


class CarListResponse(BaseModel):
    items: list[CarResponse]
    total: int


# ---------- Repository ----------
class CarRepository:
    def __init__(self):
        self._cars = []
        self._next_id = 1

    def get_all(self):
        return list(self._cars)

    def get(self, car_id):
        for car in self._cars:
            if car["id"] == car_id:
                return car
        return None

    def create(self, data):
        car = {"id": self._next_id, **data}
        self._next_id += 1
        self._cars.append(car)
        return car

    def replace(self, car_id, data):
        car = self.get(car_id)
        if not car:
            return None
        updated = {"id": car_id, **data}
        idx = self._cars.index(car)
        self._cars[idx] = updated
        return updated

    def patch(self, car_id, data):
        car = self.get(car_id)
        if not car:
            return None
        car.update({k: v for k, v in data.items() if v is not None})
        return car

    def delete(self, car_id):
        car = self.get(car_id)
        if car:
            self._cars.remove(car)
            return True
        return False


# ---------- Service ----------
class CarService:
    def __init__(self, repository):
        self.repository = repository

    def list_cars(self, category=None, min_year=None, search=None,
                  sort=None, order="asc", limit=10, offset=0):
        cars = self.repository.get_all()
        if category:
            cars = [c for c in cars if category.lower() in c["category"].lower()]
        if min_year:
            cars = [c for c in cars if c["year"] >= min_year]
        if search:
            cars = [c for c in cars
                    if search.lower() in c["brand"].lower()
                    or search.lower() in c["model"].lower()]
        if sort in ("year", "mileage", "brand"):
            reverse = order == "desc"
            cars = sorted(cars, key=lambda c: c[sort], reverse=reverse)
        total = len(cars)
        page = cars[offset:offset + limit]
        return page, total

    def get_car(self, car_id):
        car = self.repository.get(car_id)
        if not car:
            raise HTTPException(status_code=404, detail="Car not found")
        return car

    def create_car(self, data):
        return self.repository.create(data.dict())

    def replace_car(self, car_id, data):
        car = self.repository.replace(car_id, data.dict())
        if not car:
            raise HTTPException(status_code=404, detail="Car not found")
        return car

    def patch_car(self, car_id, data):
        car = self.repository.patch(car_id, data.dict(exclude_none=True))
        if not car:
            raise HTTPException(status_code=404, detail="Car not found")
        return car

    def delete_car(self, car_id):
        if not self.repository.delete(car_id):
            raise HTTPException(status_code=404, detail="Car not found")
        return None

    def cars_in_repair(self):
        return [c for c in self.repository.get_all()
                if c["condition"] in ("repair", "need_diagnostics")]

    def statistics(self):
        cars = self.repository.get_all()
        if not cars:
            return {"count": 0}
        return {
            "count": len(cars),
            "average_mileage": round(sum(c["mileage"] for c in cars) / len(cars), 1),
            "average_year": round(sum(c["year"] for c in cars) / len(cars), 1),
            "cars_in_repair": len([c for c in cars if c["condition"] == "repair"]),
            "by_category": self._group_by(cars, "category"),
        }

    def _group_by(self, cars, key):
        result = {}
        for c in cars:
            result[c[key]] = result.get(c[key], 0) + 1
        return result


# ---------- Инициализация ----------
repository = CarRepository()
service = CarService(repository)

for data in [
    CarCreate(brand="Toyota", model="Camry", year=2018, owner="Иванов",
              mileage=95000, category="sedan", condition="good"),
    CarCreate(brand="Hyundai", model="Solaris", year=2015, owner="Петрова",
              mileage=120000, category="sedan", condition="repair"),
    CarCreate(brand="Kia", model="Rio", year=2020, owner="Сидоров",
              mileage=50000, category="hatchback", condition="good"),
    CarCreate(brand="Toyota", model="Rav4", year=2016, owner="Кузнецов",
              mileage=150000, category="suv", condition="need_diagnostics"),
]:
    service.create_car(data)


# ---------- REST endpoints ----------
@app.get("/cars", response_model=CarListResponse)
def list_cars(
    category: Optional[str] = None,
    min_year: Optional[int] = None,
    search: Optional[str] = None,
    sort: Optional[str] = None,
    order: str = "asc",
    limit: int = 10,
    offset: int = 0,
):
    items, total = service.list_cars(
        category, min_year, search, sort, order, limit, offset
    )
    return {"items": [CarResponse(**c) for c in items], "total": total}


@app.get("/cars/in-repair", response_model=list[CarResponse])
def cars_in_repair():
    return [CarResponse(**c) for c in service.cars_in_repair()]


@app.get("/cars/statistics")
def cars_statistics():
    return service.statistics()


@app.get("/cars/search/{term}")
async def search_cars(term: str):
    items, _ = service.list_cars(search=term)
    return [CarResponse(**c) for c in items]


@app.get("/cars/{car_id}", response_model=CarResponse)
def get_car(car_id: int):
    return CarResponse(**service.get_car(car_id))


@app.post("/cars", response_model=CarResponse, status_code=201)
def create_car(data: CarCreate):
    return CarResponse(**service.create_car(data))


@app.put("/cars/{car_id}", response_model=CarResponse)
def replace_car(car_id: int, data: CarCreate):
    return CarResponse(**service.replace_car(car_id, data))


@app.patch("/cars/{car_id}", response_model=CarResponse)
def patch_car(car_id: int, data: CarUpdate):
    return CarResponse(**service.patch_car(car_id, data))


@app.delete("/cars/{car_id}", status_code=204)
def delete_car(car_id: int):
    service.delete_car(car_id)


@app.get("/health")
def health():
    return {"status": "healthy"}