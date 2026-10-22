# Лабораторная работа N13. Вариант 7
# Автосервис - автомобили. MongoDB (документы) + Redis (кэш, Cache-Aside, TTL).
#
# Сущность (вариант 7): автомобиль (car) с вложенными документами и массивами.
# MongoDB - основное хранение, Redis - кэш последней информации и быстрый доступ.
#
# Запуск: pip install pymongo redis; python main.py
# Требует запущенных MongoDB (27017) и Redis (6379).
# Если сервисы недоступны - программа выводит предупреждение и завершается.

import json
import time

try:
    import pymongo
    from pymongo import MongoClient
    MONGO_OK = True
except ImportError:
    MONGO_OK = False

try:
    import redis
    REDIS_OK = True
except ImportError:
    REDIS_OK = False


def mongo_connect():
    client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=2000)
    client.admin.command("ping")
    db = client["autoservice"]
    return db


class AutoServiceMongo:
    """Репозиторий на MongoDB: документ = автомобиль с владельцем, историей, неисправностями."""
    def __init__(self, db):
        self.collection = db["cars"]
        # индексы
        self.collection.create_index("brand")
        self.collection.create_index([("owner.name", 1), ("year", -1)])

    def insert(self, data):
        result = self.collection.insert_one(data)
        return result.inserted_id

    def find_one(self, query):
        return self.collection.find_one(query)

    def find_many(self, query=None, limit=0, sort=None):
        cursor = self.collection.find(query or {})
        if sort:
            cursor = cursor.sort(sort)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    def update(self, query, data):
        return self.collection.update_one(query, {"$set": data})

    def delete(self, query):
        return self.collection.delete_one(query)

    def stats(self):
        total = self.collection.count_documents({})
        by_brand = self.collection.aggregate([
            {"$group": {"_id": "$brand", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ])
        return total, list(by_brand)


class CarCache:
    """Redis: кэш информации об автомобиле (String), счётчики (INCR), история (List)."""
    def __init__(self):
        self.client = redis.Redis(host="localhost", port=6379,
                                  decode_responses=True, socket_connect_timeout=2)

    def cache_get(self, car_id):
        return self.client.get(f"car:{car_id}")

    def cache_set(self, car_id, value, ttl=120):
        self.client.set(f"car:{car_id}", value, ex=ttl)

    def cache_invalidate(self, car_id):
        self.client.delete(f"car:{car_id}")

    def increment_views(self, car_id):
        return self.client.incr(f"car:{car_id}:views")

    def add_to_history(self, car_id, entry, limit=5):
        key = f"car:{car_id}:history"
        self.client.lpush(key, entry)
        self.client.ltrim(key, 0, limit - 1)

    def get_history(self, car_id):
        return self.client.lrange(f"car:{car_id}:history", 0, -1)

    def clear(self):
        for key in self.client.keys("car:*"):
            self.client.delete(key)


def demo_car(brand, model, year, owner, specs, service_history, faults):
    return {
        "brand": brand,
        "model": model,
        "year": year,
        "owner": owner,  # вложенный документ {"name", "phone"}
        "specs": specs,  # вложенный документ {"engine", "power", "mileage"}
        "service_history": service_history,  # массив {"date","work","cost"}
        "faults": faults,  # массив строк
        "condition": "good",
    }


def main():
    if not MONGO_OK:
        print("Библиотека pymongo не установлена: pip install pymongo")
        return
    if not REDIS_OK:
        print("Библиотека redis не установлена: pip install redis")
        return

    try:
        db = mongo_connect()
    except Exception as error:
        print(f"MongoDB недоступен: {error}. Запустите MongoDB (mongod).")
        return

    try:
        cache = CarCache()
    except Exception as error:
        print(f"Redis недоступен: {error}. Запустите Redis (redis-server).")
        return

    repo = AutoServiceMongo(db)

    # Демо-данные (не менее 20 документов по требованиям)
    if repo.collection.count_documents({}) == 0:
        cars = [
            demo_car("Toyota", "Camry", 2018, {"name": "Иванов", "phone": "111"},
                     {"engine": 2.5, "power": 181, "mileage": 95000},
                     [{"date": "2023-05", "work": "ТО", "cost": 12000}],
                     []),
            demo_car("Hyundai", "Solaris", 2015, {"name": "Петрова", "phone": "222"},
                     {"engine": 1.6, "power": 123, "mileage": 120000},
                     [{"date": "2024-01", "work": "Замена колодок", "cost": 4500}],
                     ["скрип тормозов"]),
            demo_car("Kia", "Rio", 2020, {"name": "Сидоров", "phone": "333"},
                     {"engine": 1.6, "power": 123, "mileage": 50000},
                     [], []),
            demo_car("Toyota", "Rav4", 2016, {"name": "Кузнецов", "phone": "444"},
                     {"engine": 2.0, "power": 145, "mileage": 150000},
                     [{"date": "2023-09", "work": "Амортизаторы", "cost": 24000}],
                     ["стук подвески"]),
            demo_car("Volkswagen", "Golf", 2017, {"name": "Орлов", "phone": "555"},
                     {"engine": 1.4, "power": 125, "mileage": 80000},
                     [], []),
            demo_car("Toyota", "Corolla", 2019, {"name": "Иванов", "phone": "111"},
                     {"engine": 1.6, "power": 122, "mileage": 70000},
                     [{"date": "2024-04", "work": "Масло", "cost": 6000}],
                     []),
            demo_car("Kia", "Sportage", 2021, {"name": "Петрова", "phone": "222"},
                     {"engine": 2.0, "power": 150, "mileage": 30000},
                     [], []),
            demo_car("Hyundai", "Creta", 2019, {"name": "Сидоров", "phone": "333"},
                     {"engine": 2.0, "power": 149, "mileage": 88000},
                     [{"date": "2024-02", "work": "Свечи", "cost": 3000}],
                     ["не запускается в мороз"]),
        ]
        # добавим ещё, чтобы было ~20 документов
        for i in range(12):
            cars.append(demo_car(f"Brand{i%3}", f"Model{i}", 2010 + i % 12,
                                 {"name": f"Владелец{i}", "phone": f"99{i}"},
                                 {"engine": 1.5, "power": 100 + i, "mileage": 100000 - i * 5000},
                                 [], []))
        for car in cars:
            repo.insert(car)

    while True:
        print("\n===== МЕНЮ (MongoDB + Redis) =====")
        print("1. Список автомобилей")
        print("2. Найти по марке")
        print("3. Автомобиль по ID (через Redis-кэш)")
        print("4. Найти с неисправностями (массив)")
        print("5. Сортировка по году")
        print("6. Агрегация по маркам")
        print("7. Просмотр авто + счётчик + история (Redis)")
        print("8. Обновить автомобиль")
        print("9. Удалить автомобиль")
        print("10. Тест производительности MongoDB vs Redis")
        print("0. Выход")
        choice = input("Выберите действие: ")

        if choice == "1":
            for c in repo.find_many(limit=10):
                print(f"  {c['_id']} {c['brand']} {c['model']} ({c['year']})")
        elif choice == "2":
            brand = input("Марка: ")
            for c in repo.find_many({"brand": brand}):
                print(f"  {c['_id']} {c['brand']} {c['model']} ({c['year']}), "
                      f"пробег {c['specs']['mileage']}")
        elif choice == "3":
            car_id = input("ID (вставьте из списка _id): ")
            key = f"car:{car_id}"
            cached = cache.cache_get(car_id)
            if cached is not None:
                print("  [из Redis кэша]")
                print(cached)
            else:
                try:
                    from bson import ObjectId
                    car = repo.find_one({"_id": ObjectId(car_id)})
                except Exception:
                    print("Некорректный ID")
                    continue
                if not car:
                    print("Не найден")
                    continue
                info = (f"#{car['_id']} {car['brand']} {car['model']} "
                        f"({car['year']}), владелец {car['owner']['name']}")
                cache.cache_set(car_id, info, ttl=120)
                print("  [из MongoDB, помещён в Redis]")
                print(info)
        elif choice == "4":
            # поиск по элементу массива
            for c in repo.find_many({"faults": {"$ne": []}}):
                print(f"  {c['brand']} {c['model']}: {c['faults']}")
        elif choice == "5":
            for c in repo.find_many(sort=[("year", -1)], limit=5):
                print(f"  {c['brand']} {c['model']} ({c['year']})")
        elif choice == "6":
            total, by_brand = repo.stats()
            print(f"Всего: {total}")
            for row in by_brand:
                print(f"  {row['_id']}: {row['count']}")
        elif choice == "7":
            car_id = input("ID: ")
            from bson import ObjectId
            car = repo.find_one({"_id": ObjectId(car_id)})
            if not car:
                print("Не найден")
                continue
            views = cache.increment_views(car_id)
            entry = json.dumps({"viewed": str(car["_id"]), "at": time.time()}, ensure_ascii=False)
            cache.add_to_history(car_id, entry)
            print(f"  {car['brand']} {car['model']} - просмотров: {views}")
            print("  Последние обращения:", cache.get_history(car_id))
        elif choice == "8":
            car_id = input("ID: ")
            from bson import ObjectId
            r = repo.update({"_id": ObjectId(car_id)}, {"condition": "repair"})
            cache.cache_invalidate(car_id)
            print(f" Обновлено: {r.modified_count}, кэш инвалидирован")
        elif choice == "9":
            car_id = input("ID: ")
            from bson import ObjectId
            r = repo.delete({"_id": ObjectId(car_id)})
            cache.cache_invalidate(car_id)
            print(f" Удалено: {r.deleted_count}")
        elif choice == "10":
            from bson import ObjectId
            all_cars = repo.find_many()
            car_id = str(all_cars[0]["_id"])
            # MongoDB
            start = time.perf_counter()
            for _ in range(100):
                repo.find_one({"_id": ObjectId(car_id)})
            mongo_time = time.perf_counter() - start
            # Redis (после заполнения кэша)
            repo.find_one({"_id": ObjectId(car_id)})
            info = f"кэш {car_id}"
            cache.cache_set(car_id, info, ttl=600)
            start = time.perf_counter()
            for _ in range(1000):
                cache.cache_get(car_id)
            redis_time = time.perf_counter() - start
            print(f"MongoDB 100 чтений: {mongo_time:.4f} с")
            print(f"Redis 1000 чтений: {redis_time:.4f} с")
        elif choice == "0":
            break
        else:
            print("Неверный пункт")


if __name__ == "__main__":
    main()