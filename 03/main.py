# Лабораторная работа N3. Вариант 7
# Фильмотека (ООП: наследование, полиморфизм, композиция)

class Media:
    """Базовый класс медиа-контента."""
    def __init__(self, title, year):
        self.title = title
        self.year = year
        self._rating = 0.0

    @property
    def rating(self):
        return self._rating

    @rating.setter
    def rating(self, value):
        if not (0 <= value <= 10):
            raise ValueError("Рейтинг должен быть от 0 до 10")
        self._rating = value

    def duration_minutes(self):
        """Продолжительность/объём контента в минутах."""
        raise NotImplementedError

    def get_info(self):
        return f"{self.title} ({self.year}), рейтинг {self.rating}"


class Movie(Media):
    """Фильм: хранит длительность в минутах."""
    def __init__(self, title, year, duration):
        super().__init__(title, year)
        if duration <= 0:
            raise ValueError("Длительность должна быть положительной")
        self.duration = duration

    def duration_minutes(self):
        return self.duration

    def get_info(self):
        return f"Фильм: {self.title} ({self.year}), {self.duration} мин, рейтинг {self.rating}"


class Series(Media):
    """Сериал: хранит количество сезонов и серий в сезоне."""
    def __init__(self, title, year, seasons, episodes_per_season):
        super().__init__(title, year)
        if seasons <= 0 or episodes_per_season <= 0:
            raise ValueError("Число сезонов и серий должно быть положительным")
        self.seasons = seasons
        self.episodes_per_season = episodes_per_season

    def duration_minutes(self):
        # Условно: каждая серия ~45 минут
        return self.seasons * self.episodes_per_season * 45

    def get_info(self):
        return (f"Сериал: {self.title} ({self.year}), "
                f"{self.seasons} сез., {self.episodes_per_season} серий, "
                f"объём ~{self.duration_minutes()} мин, рейтинг {self.rating}")


class MediaLibrary:
    """Композиция: библиотека содержит коллекцию объектов Media."""
    def __init__(self):
        self.items = []

    def add(self, media):
        self.items.append(media)

    def total_duration(self):
        return sum(item.duration_minutes() for item in self.items)

    def show_all(self):
        for item in self.items:
            print(item.get_info())


def main():

    movie = Movie("Интерстеллар", 2014, 169)
    movie.rating = 8.9

    series = Series("Во все тяжкие", 2008, 5, 7)
    series.rating = 9.5

    movie2 = Movie("Матрица", 1999, 136)
    movie2.rating = 8.7

    library = MediaLibrary()
    library.add(movie)
    library.add(series)
    library.add(movie2)

    print("=== Полиморфная коллекция ===")
    library.show_all()
    print(f"\nОбщая продолжительность: {library.total_duration()} мин")
    print(f"Объектов в библиотеке: {len(library.items)}")

    # Проверка инкапсуляции (property)
    try:
        movie.rating = 15
    except ValueError as error:
        print(f"Ошибка: {error}")


if __name__ == "__main__":
    main()