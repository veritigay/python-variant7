# Лабораторная работа N12. Вариант 7
# Фитнес-клуб. SQLAlchemy ORM (SQLite/PostgreSQL)
#
# Сущности (вариант 7): Client, Trainer, Training
# Реализовано: CRUD, связи, поиск, фильтрация, сортировка, транзакция.
#
# Запуск: pip install sqlalchemy; python main.py

from sqlalchemy import (
    create_engine, select, ForeignKey, and_
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session

# Для простоты используем SQLite (файл gym.db). Для PostgreSQL замените URL.
DATABASE_URL = "sqlite:///" + __import__("os").path.join(
    __import__("os").path.dirname(__import__("os").path.abspath(__file__)), "gym.db"
)


class Base(DeclarativeBase):
    pass


# ---------- Модели ----------
class Client(Base):
    __tablename__ = "clients"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    age: Mapped[int]
    phone: Mapped[str] = mapped_column(unique=True)  # уникальное поле
    subscription_expire: Mapped[str]  # дата окончания абонемента (ISO)

    trainings: Mapped[list["Training"]] = relationship(back_populates="client")


class Trainer(Base):
    __tablename__ = "trainers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    specialty: Mapped[str]

    trainings: Mapped[list["Training"]] = relationship(back_populates="trainer")


class Training(Base):
    __tablename__ = "trainings"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    trainer_id: Mapped[int] = mapped_column(ForeignKey("trainers.id"))
    date: Mapped[str]  # дата занятия
    duration: Mapped[int]  # минуты

    client: Mapped["Client"] = relationship(back_populates="trainings")
    trainer: Mapped["Trainer"] = relationship(back_populates="trainings")


# ---------- Repository ----------
class GymRepository:
    def __init__(self, session):
        self.session = session

    # --- Client ---
    def create_client(self, name, age, phone, subscription_expire):
        client = Client(name=name, age=age, phone=phone,
                        subscription_expire=subscription_expire)
        self.session.add(client)
        self.session.commit()
        return client

    def get_client(self, client_id):
        return self.session.get(Client, client_id)

    def all_clients(self):
        return list(self.session.scalars(select(Client)).all())

    def find_clients(self, min_age=None, max_age=None, name=None):
        stmt = select(Client)
        conds = []
        if min_age is not None:
            conds.append(Client.age >= min_age)
        if max_age is not None:
            conds.append(Client.age <= max_age)
        if name:
            conds.append(Client.name.like(f"%{name}%"))
        if conds:
            stmt = stmt.where(and_(*conds))
        return list(self.session.scalars(stmt).all())

    def update_client(self, client, **fields):
        for key, value in fields.items():
            if hasattr(client, key):
                setattr(client, key, value)
        self.session.commit()
        return client

    def delete_client(self, client):
        # из-за внешнего ключа удаляем связанные тренировки
        for t in client.trainings:
            self.session.delete(t)
        self.session.delete(client)
        self.session.commit()

    # --- Trainer ---
    def create_trainer(self, name, specialty):
        trainer = Trainer(name=name, specialty=specialty)
        self.session.add(trainer)
        self.session.commit()
        return trainer

    # --- Training ---
    def book_training(self, client, trainer, date, duration):
        """Транзакция: назначаем тренировку и проверяем абонемент."""
        if client.subscription_expire < date:
            raise ValueError(f"Абонемент клиента {client.name} истёк: {client.subscription_expire}")
        training = Training(client_id=client.id, trainer_id=trainer.id,
                            date=date, duration=duration)
        try:
            self.session.add(training)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return training

    def trainings_of_client(self, client):
        return list(client.trainings)

    def sort_clients_by_age(self, desc=False):
        return list(self.session.scalars(
            select(Client).order_by(Client.age.desc() if desc else Client.age)
        ).all())

    def clients_by_specialty_trainers(self, specialty):
        """Клиенты, чьи тренеры имеют указанную специализацию (работа со связями)."""
        result = []
        for client in self.all_clients():
            for t in client.trainings:
                if t.trainer.specialty == specialty:
                    result.append(client)
                    break
        return result


def main():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)

    session = Session(engine)
    repo = GymRepository(session)

    # Демо-данные
    if not repo.all_clients():
        for name, age, phone in [
            ("Иван Петров", 25, "990001"),
            ("Анна Сидорова", 31, "990002"),
            ("Пётр Кузнецов", 19, "990003"),
            ("Мария Иванова", 40, "990004"),
        ]:
            repo.create_client(name, age, phone, subscription_expire="2026-12-31")

    if not repo.session.scalars(select(Trainer)).all():
        t1 = repo.create_trainer("Тренер А", "силовые")
        t2 = repo.create_trainer("Тренер Б", "кардио")
        t3 = repo.create_trainer("Тренер В", "силовые")

    while True:
        print("\n===== МЕНЮ =====")
        print("1. Список клиентов")
        print("2. Найти клиентов (возраст/имя)")
        print("3. Сортировка по возрасту")
        print("4. Записать на тренировку (транзакция)")
        print("5. Тренировки клиента")
        print("6. Клиенты по специализации тренера")
        print("7. Редактировать клиента")
        print("8. Удалить клиента")
        print("0. Выход")
        choice = input("Выберите действие: ")

        if choice == "1":
            for c in repo.all_clients():
                print(f"  #{c.id} {c.name}, {c.age} лет, абонемент до {c.subscription_expire}")
        elif choice == "2":
            min_age = input("Мин. возраст (пусто - все): ")
            max_age = input("Макс. возраст (пусто - все): ")
            name = input("Имя (пусто - все): ")
            clients = repo.find_clients(
                int(min_age) if min_age else None,
                int(max_age) if max_age else None,
                name or None,
            )
            for c in clients:
                print(f"  #{c.id} {c.name}, {c.age} лет")
            if not clients:
                print("  Клиенты не найдены")
        elif choice == "3":
            for c in repo.sort_clients_by_age():
                print(f"  {c.name}, {c.age} лет")
        elif choice == "4":
            client_id = int(input("ID клиента: "))
            client = repo.get_client(client_id)
            if not client:
                print("Клиент не найден")
                continue
            trainers = repo.session.scalars(select(Trainer)).all()
            print("Тренеры:")
            for t in trainers:
                print(f"  #{t.id} {t.name} ({t.specialty})")
            trainer_id = int(input("ID тренера: "))
            trainer = repo.session.get(Trainer, trainer_id)
            date = input("Дата (ГГГГ-ММ-ДД): ")
            duration = int(input("Длительность (мин): "))
            try:
                tr = repo.book_training(client, trainer, date, duration)
                print(f"Тренировка #{tr.id} создана для {client.name} у {trainer.name}")
            except ValueError as error:
                print(f"Ошибка: {error}")
        elif choice == "5":
            client_id = int(input("ID клиента: "))
            client = repo.get_client(client_id)
            if not client:
                print("Клиент не найден")
                continue
            for t in client.trainings:
                print(f"  {t.date} с {t.trainer.name}, {t.duration} мин")
        elif choice == "6":
            specialty = input("Специализация: ")
            for c in repo.clients_by_specialty_trainers(specialty):
                print(f"  {c.name}")
        elif choice == "7":
            client_id = int(input("ID клиента: "))
            client = repo.get_client(client_id)
            if not client:
                print("Клиент не найден")
                continue
            phone = input("Новый телефон: ")
            age = int(input("Новый возраст: "))
            repo.update_client(client, phone=phone, age=age)
            print("Обновлено")
        elif choice == "8":
            client_id = int(input("ID клиента: "))
            client = repo.get_client(client_id)
            if not client:
                print("Клиент не найден")
                continue
            repo.delete_client(client)
            print("Клиент удалён")
        elif choice == "0":
            break
        else:
            print("Неверный пункт")

    session.close()


if __name__ == "__main__":
    main()