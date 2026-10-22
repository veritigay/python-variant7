# Лабораторная работа N10. Вариант 7
# HTTP-клиент для REST API автосервиса (Flask)
import requests

BASE = "http://127.0.0.1:5000"


def main():
    while True:
        print("\n=== REST CLIENT (Автосервис) ===")
        print("1. Список автомобилей")
        print("2. Получить автомобиль")
        print("3. Добавить автомобиль")
        print("4. Изменить (PUT)")
        print("5. Частично изменить (PATCH)")
        print("6. Удалить")
        print("7. Фильтрация/сортировка")
        print("8. Автомобили в ремонте")
        print("9. Статистика")
        print("0. Выход")
        choice = input("Выберите действие: ")

        try:
            if choice == "1":
                r = requests.get(f"{BASE}/cars")
                print(r.status_code, r.json())
            elif choice == "2":
                car_id = int(input("ID: "))
                r = requests.get(f"{BASE}/cars/{car_id}")
                print(r.status_code, r.json())
            elif choice == "3":
                data = {
                    "brand": input("Марка: "),
                    "model": input("Модель: "),
                    "year": int(input("Год: ")),
                    "owner": input("Владелец: "),
                    "mileage": int(input("Пробег: ")),
                    "category": input("Категория: "),
                    "condition": input("Состояние (good/repair): "),
                }
                r = requests.post(f"{BASE}/cars", json=data)
                print(r.status_code, r.json())
            elif choice == "4":
                car_id = int(input("ID: "))
                data = {
                    "brand": input("Марка: "),
                    "model": input("Модель: "),
                    "year": int(input("Год: ")),
                    "owner": input("Владелец: "),
                    "mileage": int(input("Пробег: ")),
                    "category": input("Категория: "),
                    "condition": input("Состояние: "),
                }
                r = requests.put(f"{BASE}/cars/{car_id}", json=data)
                print(r.status_code, r.json())
            elif choice == "5":
                car_id = int(input("ID: "))
                mileage = input("Новый пробег (пусто - пропустить): ")
                data = {"mileage": int(mileage)} if mileage else {}
                r = requests.patch(f"{BASE}/cars/{car_id}", json=data)
                print(r.status_code, r.json())
            elif choice == "6":
                car_id = int(input("ID: "))
                r = requests.delete(f"{BASE}/cars/{car_id}")
                print(r.status_code)
            elif choice == "7":
                brand = input("Марка (пусто - все): ")
                params = {"brand": brand} if brand else {}
                r = requests.get(f"{BASE}/cars", params=params)
                print(r.status_code, r.json())
            elif choice == "8":
                r = requests.get(f"{BASE}/cars/in-repair")
                print(r.status_code, r.json())
            elif choice == "9":
                r = requests.get(f"{BASE}/cars/statistics")
                print(r.status_code, r.json())
            elif choice == "0":
                break
            else:
                print("Неверный пункт")
        except requests.ConnectionError:
            print("Ошибка: сервер недоступен. Запустите app.py")


if __name__ == "__main__":
    main()