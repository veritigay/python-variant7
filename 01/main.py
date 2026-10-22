# Лабораторная работа N1. Вариант 7
# Анализ результатов спортивных соревнований

def read_results(count):
    """Ввод результатов спортсменов в секундах с проверкой."""
    results = []
    for i in range(count):
        while True:
            try:
                value = float(input(f"Результат спортсмена {i + 1} (сек): "))
                if value < 0:
                    print("Ошибка: результат не может быть отрицательным")
                    continue
                results.append(value)
                break
            except ValueError:
                print("Ошибка: введите число")
    return results


def best_result(results):
    """Лучший (минимальный) результат."""
    best = results[0]
    for value in results[1:]:
        if value < best:
            best = value
    return best


def worst_result(results):
    """Худший (максимальный) результат."""
    worst = results[0]
    for value in results[1:]:
        if value > worst:
            worst = value
    return worst


def average_result(results):
    """Средний результат."""
    total = 0
    for value in results:
        total += value
    return total / len(results)


def above_average_count(results):
    """Количество спортсменов лучше среднего (меньше среднего результата)."""
    average = average_result(results)
    count = 0
    for value in results:
        if value < average:
            count += 1
    return count


def winners(results):
    """Призёры (3 лучших результата): места и номера спортсменов."""
    indexed = [(results[i], i + 1) for i in range(len(results))]
    indexed.sort()
    med = [1]
    for i in range(1, len(indexed)):
        if indexed[i][0] == indexed[i - 1][0]:
            med.append(med[-1])
        else:
            med.append(i + 1)
    return indexed, med


def main():
    n = int(input("Введите количество спортсменов: "))
    if n <= 0:
        print("Ошибка: количество должно быть положительным")
        return

    results = read_results(n)

    print("\n=== Анализ результатов ===")
    print(f"Лучший результат: {best_result(results):.2f} сек")
    print(f"Худший результат: {worst_result(results):.2f} сек")
    print(f"Средний результат: {average_result(results):.2f} сек")
    print(f"Спортсменов лучше среднего: {above_average_count(results)}")

    indexed, med = winners(results)
    print("\nПризёры (лучшие результаты):")
    for place in range(1, 4):
        if place <= len(indexed):
            result, num = indexed[place - 1]
            print(f"  {place} место: спортсмен {num}, результат {result:.2f} сек")


if __name__ == "__main__":
    main()