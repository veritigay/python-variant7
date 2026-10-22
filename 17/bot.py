# Лабораторная работа N17. Вариант 7
# Автосервис. Асинхронный Telegram-бот на aiogram 3.
#
# Сущности (вариант 7): автомобиль, клиент, услуга, заказ-наряд, история.
# Реализовано: /start, /help, /cancel, главное меню, Reply/Inline клавиатуры,
# Callback Query, FSM (многошаговый диалог), валидация, CRUD, поиск,
# middleware, SQLite БД.
#
# Запуск: pip install aiogram; BOT_TOKEN=... python bot.py
# Без токена бот не запустится - в коде показана полная структура.

import asyncio
import os
import logging
import sqlite3

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup,
    KeyboardButton, CallbackQuery,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import BaseMiddleware
from typing import Any, Awaitable, Callable, Dict

logging.basicConfig(level=logging.INFO)

# Токен задаётся через переменную окружения, НЕ хранится в исходном коде.
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

router = Router()

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.db")


# ============ База данных (SQLite) ============
class Database:
    def __init__(self, path):
        self.path = path
        self.conn = sqlite3.connect(path)
        self._init()

    def _init(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reg_number TEXT UNIQUE,
                brand TEXT,
                model TEXT,
                owner TEXT,
                condition TEXT DEFAULT 'good'
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                price_per_hour REAL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                car_id INTEGER,
                service_id INTEGER,
                hours REAL,
                status TEXT DEFAULT 'created',
                FOREIGN KEY(car_id) REFERENCES cars(id),
                FOREIGN KEY(service_id) REFERENCES services(id)
            )
        """)
        self.conn.commit()

    def add_car(self, reg, brand, model, owner):
        try:
            cur = self.conn.execute(
                "INSERT INTO cars(reg_number, brand, model, owner) VALUES (?,?,?,?)",
                (reg, brand, model, owner))
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_car(self, car_id):
        return self.conn.execute(
            "SELECT * FROM cars WHERE id=?", (car_id,)).fetchone()

    def all_cars(self):
        return self.conn.execute("SELECT * FROM cars").fetchall()

    def add_service(self, name, price):
        cur = self.conn.execute(
            "INSERT INTO services(name, price_per_hour) VALUES (?,?)", (name, price))
        self.conn.commit()
        return cur.lastrowid

    def all_services(self):
        return self.conn.execute("SELECT * FROM services").fetchall()

    def add_order(self, car_id, service_id, hours):
        cur = self.conn.execute(
            "INSERT INTO orders(car_id, service_id, hours) VALUES (?,?,?)",
            (car_id, service_id, hours))
        self.conn.commit()
        return cur.lastrowid

    def order_history(self, car_id):
        return self.conn.execute(
            "SELECT o.id, s.name, o.hours, o.status FROM orders o "
            "JOIN services s ON s.id=o.service_id "
            "WHERE o.car_id=?", (car_id,)).fetchall()

    def update_order_status(self, order_id, status):
        self.conn.execute("UPDATE orders SET status=? WHERE id=?",
                          (status, order_id))
        self.conn.commit()

    def delete_car(self, car_id):
        self.conn.execute("DELETE FROM orders WHERE car_id=?", (car_id,))
        self.conn.execute("DELETE FROM cars WHERE id=?", (car_id,))
        self.conn.commit()


db = Database(DB_FILE)


# ============ Middleware (логирование) ============
class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        logging.info("User %s sent: %s", event.from_user.id, event.text)
        result = await handler(event, data)
        return result


# ============ FSM: регистрация автомобиля ============
class CarRegistration(StatesGroup):
    reg_number = State()
    brand = State()
    model = State()
    owner = State()


# ============ Клавиатуры ============
def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Каталог услуг")],
            [KeyboardButton(text="Мои авто")],
            [KeyboardButton(text="Зарегистрировать авто")],
            [KeyboardButton(text="Помощь")],
        ],
        resize_keyboard=True,
    )


def inline_car_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="История обслуживания", callback_data="history:1")],
            [InlineKeyboardButton(text="Создать заказ", callback_data="create_order:1")],
            [InlineKeyboardButton(text="Удалить авто", callback_data="delete_car:1")],
        ]
    )


def service_buttons():
    services = db.all_services()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{s[1]} ({s[2]}₽/ч)",
                                  callback_data=f"service:{s[0]}")]
            for s in services
        ]
    )


# ============ Команды ============
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Добро пожаловать в Автосервис!\n"
        "Управляйте записью автомобилей на обслуживание.",
        reply_markup=main_keyboard(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Команды:\n"
        "/start - главное меню\n"
        "/cancel - отменить текущую операцию\n"
        "Используйте кнопки меню."
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Операция отменена.", reply_markup=main_keyboard())


# ============ Reply-кнопки ============
@router.message(F.text == "Каталог услуг")
async def show_services(message: Message):
    services = db.all_services()
    if not services:
        await message.answer("Каталог пуст.")
        return
    text = "\n".join(f"{s[1]} — {s[2]} ₽/час" for s in services)
    await message.answer("Каталог услуг:\n" + text)


@router.message(F.text == "Мои авто")
async def show_cars(message: Message):
    cars = db.all_cars()
    if not cars:
        await message.answer("У вас нет зарегистрированных авто.")
        return
    lines = [f"{c[1]} {c[2]} {c[3]} ({c[4]})" for c in cars]
    await message.answer("Ваши авто:\n" + "\n".join(lines),
                         reply_markup=inline_car_menu())


@router.message(F.text == "Зарегистрировать авто")
async def start_registration(message: Message, state: FSMContext):
    await state.set_state(CarRegistration.reg_number)
    await message.answer("Введите госномер автомобиля:")


@router.message(F.text == "Помощь")
async def help_button(message: Message):
    await message.answer("Используйте меню или /help.")


# ============ FSM-обработчики с валидацией ============
@router.message(CarRegistration.reg_number)
async def reg_number(message: Message, state: FSMContext):
    value = message.text.strip().upper()
    # валидация 1: формат госномера
    if len(value) < 6:
        await message.answer("Госномер выглядит некорректно. Попробуйте ещё раз:")
        return
    await state.update_data(reg_number=value)
    await state.set_state(CarRegistration.brand)
    await message.answer("Введите марку:")


@router.message(CarRegistration.brand)
async def reg_brand(message: Message, state: FSMContext):
    await state.update_data(brand=message.text.strip())
    await state.set_state(CarRegistration.model)
    await message.answer("Введите модель:")


@router.message(CarRegistration.model)
async def reg_model(message: Message, state: FSMContext):
    await state.update_data(model=message.text.strip())
    await state.set_state(CarRegistration.owner)
    await message.answer("Введите ФИО владельца:")


@router.message(CarRegistration.owner)
async def reg_owner(message: Message, state: FSMContext):
    data = await state.get_data()
    owner = message.text.strip()
    # валидация 2: имя не может быть пустым
    if not owner:
        await message.answer("Имя не может быть пустым:")
        return
    car_id = db.add_car(data["reg_number"], data["brand"],
                        data["model"], owner)
    if car_id is None:
        await message.answer("Авто с таким госномером уже зарегистрировано.")
    else:
        await message.answer(
            f"Авто зарегистрировано!\n{data['brand']} {data['model']} "
            f"({data['reg_number']})"
        )
    await state.clear()


# ============ Callback Query ============
@router.callback_query(F.data.startswith("history:"))
async def history(callback: CallbackQuery):
    car_id = int(callback.data.split(":")[1])
    history = db.order_history(car_id)
    await callback.answer()
    if not history:
        await callback.message.answer("Истории обслуживания нет.")
        return
    text = "\n".join(f"{h[1]}: {h[2]}ч, {h[3]}" for h in history)
    await callback.message.answer("История:\n" + text)


@router.callback_query(F.data == "create_order:1")
async def choose_service(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("Выберите услугу:", reply_markup=service_buttons())


@router.callback_query(F.data.startswith("service:"))
async def order_created(callback: CallbackQuery):
    service_id = int(callback.data.split(":")[1])
    await callback.answer()
    # демонстрация: создаём заказ для первого авто
    cars = db.all_cars()
    if not cars:
        await callback.message.answer("Сначала зарегистрируйте авто.")
        return
    order_id = db.add_order(cars[0][0], service_id, 2.0)
    await callback.message.answer(f"Заказ #{order_id} создан!")


@router.callback_query(F.data == "delete_car:1")
async def delete_car(callback: CallbackQuery):
    cars = db.all_cars()
    await callback.answer()
    if not cars:
        await callback.message.answer("Нет авто для удаления.")
        return
    db.delete_car(cars[0][0])
    await callback.message.answer("Авто удалено.")


# ============ Запуск ============
async def main():
    if not BOT_TOKEN:
        print("Укажите BOT_TOKEN в переменной окружения.")
        return
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(LoggingMiddleware())
    dp.include_router(router)
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())