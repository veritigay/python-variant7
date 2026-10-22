# Лабораторная работа N11. Вариант 7
# Автосервис - автомобили. Реляционная БД (SQLite/PostgreSQL) + Redis-кэш + CDN.
#
# Эта часть: схема БД, самостоятельные SQL-запросы и интеграция Python
# через самонаписанный SQL (БЕЗ ORM), параметризованные запросы.
#
# Файлы:
#   schema.sql   - создание таблиц
#   seed.py      - заполнение тестовыми данными
#   database.py  - подключение и Repository на чистых SQL-запросах
#   redis_cache.py - Cache-Aside через Redis (имитация через dict при отстуствии redis)
#   main.py      - консольное меню
#
# Запуск: pip install redis; python main.py
# Если redis недоступен - используем имитацию кэша на dict.

import os
import sqlite3

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cars.db")


# ============ schema.sql (для справки и автосоздания) ============
SCHEMA = """
CREATE TABLE IF NOT EXISTS owners (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    phone TEXT
);

CREATE TABLE IF NOT EXISTS cars (
    id INTEGER PRIMARY KEY,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    year INTEGER NOT NULL,
    owner_id INTEGER NOT NULL,
    mileage INTEGER NOT NULL DEFAULT 0,
    category TEXT,
    condition TEXT NOT NULL DEFAULT 'good',
    FOREIGN KEY (owner_id) REFERENCES owners(id)
);

CREATE TABLE IF NOT EXISTS parts (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL
);

-- Связь многие-ко-многим: автомобиль <-> запчасти (история замен)
CREATE TABLE IF NOT EXISTS car_parts (
    car_id INTEGER NOT NULL,
    part_id INTEGER NOT NULL,
    replaced_at TEXT,
    PRIMARY KEY (car_id, part_id),
    FOREIGN KEY (car_id) REFERENCES cars(id),
    FOREIGN KEY (part_id) REFERENCES parts(id)
);

CREATE INDEX IF NOT EXISTS idx_cars_brand ON cars(brand);
CREATE INDEX IF NOT EXISTS idx_cars_owner ON cars(owner_id);
"""


# ============ database.py - Repository на чистых SQL ============
class DatabaseError(Exception):
    pass


class CarRepository:
    def __init__(self, path=DATABASE):
        self.path = path
        self._init()

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self):
        conn = self._connect()
        try:
            conn.executescript(SCHEMA)
            conn.commit()
        finally:
            conn.close()

    # --- CRUD (параметризованные запросы) ---
    def add_owner(self, name, phone):
        conn = self._connect()
        try:
            cur = conn.execute(
                "INSERT INTO owners(name, phone) VALUES (?, ?)",
                (name, phone),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def list_cars(self, brand=None, condition=None, category=None):
        query = ("SELECT c.*, o.name AS owner_name FROM cars c "
                 "JOIN owners o ON o.id = c.owner_id")
        params = []
        conds = []
        if brand:
            conds.append("c.brand = ?")
            params.append(brand)
        if condition:
            conds.append("c.condition = ?")
            params.append(condition)
        if category:
            conds.append("c.category = ?")
            params.append(category)
        if conds:
            query += " WHERE " + " AND ".join(conds)
        query += " ORDER BY c.year DESC"
        conn = self._connect()
        try:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_car(self, car_id):
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT c.*, o.name AS owner_name FROM cars c "
                "JOIN owners o ON o.id = c.owner_id WHERE c.id = ?",
                (car_id,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def add_car(self, brand, model, year, owner_id, mileage, category, condition):
        conn = self._connect()
        try:
            cur = conn.execute(
                "INSERT INTO cars(brand, model, year, owner_id, mileage, category, condition) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (brand, model, year, owner_id, mileage, category, condition),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def update_mileage(self, car_id, mileage):
        if mileage < 0:
            raise DatabaseError("Пробег не может быть отрицательным")
        conn = self._connect()
        try:
            conn.execute("UPDATE cars SET mileage = ? WHERE id = ?",
                         (mileage, car_id))
            conn.commit()
        finally:
            conn.close()

    def delete_car(self, car_id):
        conn = self._connect()
        try:
            conn.execute("DELETE FROM car_parts WHERE car_id = ?", (car_id,))
            conn.execute("DELETE FROM cars WHERE id = ?", (car_id,))
            conn.commit()
        finally:
            conn.close()

    # --- Агрегация / статистика ---
    def brand_stats(self):
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT brand, COUNT(*) AS count, AVG(year) AS avg_year "
                "FROM cars GROUP BY brand HAVING COUNT(*) >= 1 ORDER BY count DESC"
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def total_cars(self):
        conn = self._connect()
        try:
            row = conn.execute("SELECT COUNT(*) AS c FROM cars").fetchone()
            return row["c"]
        finally:
            conn.close()

    def avg_mileage_by_year(self, min_year=None):
        conn = self._connect()
        try:
            if min_year:
                rows = conn.execute(
                    "SELECT year, AVG(mileage) AS avg_mileage, COUNT(*) AS n "
                    "FROM cars WHERE year >= ? GROUP BY year ORDER BY year",
                    (min_year,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT year, AVG(mileage) AS avg_mileage, COUNT(*) AS n "
                    "FROM cars GROUP BY year ORDER BY year"
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # --- JOIN cars + parts ---
    def cars_with_parts(self, part_name=None):
        conn = self._connect()
        try:
            if part_name:
                rows = conn.execute(
                    "SELECT c.brand, c.model, p.name AS part, p.price "
                    "FROM cars c "
                    "JOIN car_parts cp ON cp.car_id = c.id "
                    "JOIN parts p ON p.id = cp.part_id "
                    "WHERE p.name LIKE ? ORDER BY p.price DESC",
                    (f"%{part_name}%",),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT c.brand, c.model, p.name AS part, p.price "
                    "FROM cars c "
                    "JOIN car_parts cp ON cp.car_id = c.id "
                    "JOIN parts p ON p.id = cp.part_id "
                    "ORDER BY p.price DESC"
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def expensive_parts(self, threshold):
        """Подзапрос: детали дороже среднего."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT name, price FROM parts "
                "WHERE price > (SELECT AVG(price) FROM parts) "
                "AND price >= ? ORDER BY price DESC",
                (threshold,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


# ============ redis_cache.py - Cache-Aside ============
class CacheAside:
    """Обёртка кэша. Использует redis при наличии, иначе imitация на dict."""
    def __init__(self):
        self._fake = {}
        self.redis = None
        try:
            import redis
            self.redis = redis.Redis(host="localhost", port=6379,
                                     decode_responses=True, socket_connect_timeout=1)
            self.redis.ping()
        except Exception:
            self.redis = None

    @property
    def available(self):
        return self.redis is not None

    def get(self, key):
        if self.redis:
            return self.redis.get(key)
        return self._fake.get(key)

    def set(self, key, value, ttl=120):
        if self.redis:
            self.redis.set(key, value, ex=ttl)
        else:
            self._fake[key] = value

    def delete(self, key=None, pattern=None):
        if self.redis:
            if pattern:
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)
            elif key:
                self.redis.delete(key)
        else:
            if pattern:
                self._fake = {k: v for k, v in self._fake.items()
                              if not k.startswith(pattern.split("*")[0])}
            elif key:
                self._fake.pop(key, None)


# ============ CDN-имитация ============
class StaticCDN:
    """Раздача статических ресурсов (фото автомобилей) с пониманием заголовков кэша."""
    def __init__(self, base_url):
        self.base_url = base_url
        self.files = {
            "camera1.jpg": "https://cdn.example.com/images/camera1.jpg",
            "car1.jpg": "https://cdn.example.com/images/car1.jpg",
            "style.css": "https://cdn.example.com/css/style.css",
        }
        self.cache_control = {"max-age": 3600}

    def url(self, filename):
        return self.files.get(filename, self.base_url + filename)

    def describe(self):
        out = ["=== CDN (имитация) ==="]
        for filename, url in self.files.items():
            out.append(f"{filename}: {url} | Cache-Control: {self.cache_control}")
        return "\n".join(out)


def main():
    repo = CarRepository()
    cache = CacheAside()
    cdn = StaticCDN("https://cdn.example.com/")

    # Демо-данные при первом запуске
    if repo.total_cars() == 0:
        ivan = repo.add_owner("Иванов", "+79001112233")
        petrova = repo.add_owner("Петрова", "+79002223344")
        sidorov = repo.add_owner("Сидоров", "+79003334455")
        repo.add_car("Toyota", "Camry", 2018, ivan, 95000, "sedan", "good")
        repo.add_car("Hyundai", "Solaris", 2015, petrova, 120000, "sedan", "repair")
        repo.add_car("Kia", "Rio", 2020, sidorov, 50000, "hatchback", "good")
        repo.add_car("Toyota", "Rav4", 2016, ivan, 150000, "suv", "need_diagnostics")
        repo.add_car("Volkswagen", "Golf", 2017, petrova, 80000, "hatchback", "good")

        # Запчасти
        conn = sqlite3.connect(DATABASE)
        conn.executescript("""
            INSERT OR IGNORE INTO parts(name, price) VALUES
                ('тормозные колодки', 4500),
                ('масляный фильтр', 800),
                ('свечи зажигания', 1500),
                ('амортизатор', 12000),
                ('двигатель', 250000);
        """)
        conn.execute("INSERT OR IGNORE INTO car_parts VALUES (1, 1, '2024-01-10')")
        conn.execute("INSERT OR IGNORE INTO car_parts VALUES (1, 2, '2024-05-15')")
        conn.execute("INSERT OR IGNORE INTO car_parts VALUES (2, 1, '2024-02-20')")
        conn.execute("INSERT OR IGNORE INTO car_parts VALUES (3, 4, '2024-03-01')")
        conn.commit()
        conn.close()

    while True:
        print("\n===== МЕНЮ =====")
        print("1. Список автомобилей")
        print("2. Информация об автомобиле (через Redis-кэш)")
        print("3. Статистика по маркам")
        print("4. Пробег по годам")
        print("5. Автомобили и заменённые детали")
        print("6. Дорогие детали")
        print("7. Изменить пробег")
        print("8. CDN")
        print("9. Очистить кэш")
        print("0. Выход")
        choice = input("Выберите действие: ")

        if choice == "1":
            for car in repo.list_cars():
                print(f"  #{car['id']} {car['brand']} {car['model']} ({car['year']}) "
                      f"- {car['condition']} [{car['owner_name']}]")
        elif choice == "2":
            car_id = int(input("ID автомобиля: "))
            key = f"car:{car_id}"
            cached = cache.get(key)
            if cached is not None:
                print("  [кучно из кэша Redis]")
                print(cached)
            else:
                car = repo.get_car(car_id)
                if not car:
                    print("Автомобиль не найден")
                    continue
                info = (f"#{car['id']} {car['brand']} {car['model']} ({car['year']}), "
                        f"пробег {car['mileage']}, {car['condition']}")
                cache.set(key, info, ttl=120)
                print("  [загружено из БД, помещено в кэш]")
                print(info)
        elif choice == "3":
            for row in repo.brand_stats():
                print(f"  {row['brand']}: {row['count']} авто, ср. год {row['avg_year']:.0f}")
        elif choice == "4":
            for row in repo.avg_mileage_by_year():
                print(f"  {row['year']}: ср. пробег {row['avg_mileage']:.0f} ({row['n']} авто)")
        elif choice == "5":
            for row in repo.cars_with_parts():
                print(f"  {row['brand']} {row['model']}: {row['part']} - {row['price']:.0f} ₽")
        elif choice == "6":
            for row in repo.expensive_parts(1000):
                print(f"  {row['name']}: {row['price']:.0f} ₽")
        elif choice == "7":
            car_id = int(input("ID автомобиля: "))
            mileage = int(input("Новый пробег: "))
            try:
                repo.update_mileage(car_id, mileage)
                cache.delete(f"car:{car_id}")  # инвалидация кэша
                print("Обновлено, кэш инвалидирован")
            except DatabaseError as error:
                print(f"Ошибка: {error}")
        elif choice == "8":
            print(cdn.describe())
        elif choice == "9":
            cache.delete(pattern="car:*")
            print("Кэш очищен")
        elif choice == "0":
            break
        else:
            print("Неверный пункт")


if __name__ == "__main__":
    main()