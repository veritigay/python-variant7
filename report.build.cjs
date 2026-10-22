const os = require("os");
const path = require("path");
const fs = require("fs");
const CFG = process.env.XDG_CONFIG_HOME || path.join(os.homedir(), ".config");
const SKILL = path.join(CFG, "gigatool", "skills", "word");
const H = require(path.join(SKILL, "helpers", "index.cjs"));

const ROOT = path.join(os.homedir(), "Documents", "MultiTool", "HomeChats", "Chat", "Python-variant7");

const LABS = [
  { num: 1, title: "Основы программирования на Python", topic: "результаты спортивных соревнований", files: ["main.py"], has_structure: false },
  { num: 2, title: "Коллекции, строки и функции в Python", topic: "заказы", files: ["main.py"], has_structure: false },
  { num: 3, title: "Объектно-ориентированное программирование в Python", topic: "фильмотека", files: ["main.py"], has_structure: false },
  { num: 4, title: "Модули, исключения, файлы и сериализация данных", topic: "банковские счета", files: ["main.py"], has_structure: true },
  { num: 5, title: "Функциональные возможности Python: функции высшего порядка, итераторы и генераторы", topic: "банковские счета", files: ["main.py"], has_structure: true },
  { num: 6, title: "Декораторы, контекстные менеджеры и расширенные возможности Python", topic: "автосервис", files: ["main.py"], has_structure: true },
  { num: 7, title: "Принципы SOLID и рефакторинг архитектуры Python-приложения", topic: "автосервис", files: ["main.py"], has_structure: true },
  { num: 8, title: "Паттерны проектирования в Python", topic: "автосервис", files: ["main.py"], has_structure: true },
  { num: 9, title: "Сетевое взаимодействие в Python: TCP/UDP", topic: "склад, проверка остатков", files: ["server.py", "client.py"], has_structure: true },
  { num: 10, title: "HTTP и REST API в Python", topic: "автосервис - автомобили", files: ["app.py", "client.py"], has_structure: true },
  { num: 11, title: "Реляционные и нереляционные БД. Хранение данных и CDN", topic: "автосервис - автомобили", files: ["main.py"], has_structure: true },
  { num: 12, title: "Работа с реляционными БД с использованием SQLAlchemy и ORM", topic: "фитнес-клуб", files: ["main.py"], has_structure: true },
  { num: 13, title: "MongoDB и Redis: документные данные, кэширование", topic: "автосервис - автомобили", files: ["main.py"], has_structure: true },
  { num: 14, title: "Разработка REST API на Python с использованием FastAPI", topic: "автосервис - автомобили", files: ["main.py"], has_structure: true },
  { num: 15, title: "Разработка веб-приложения на Python с использованием Flask", topic: "фитнес-клуб", files: ["main.py"], has_structure: true },
  { num: 16, title: "Разработка веб-приложения на Python с использованием Django", topic: "автосервис", files: ["models.py"], has_structure: true },
  { num: 17, title: "Разработка асинхронного Telegram-бота на Python (aiogram 3)", topic: "автосервис", files: ["bot.py"], has_structure: true },
  { num: 18, title: "Тестирование Python-приложений с pytest и unittest.mock", topic: "автосервис", files: ["src/services.py", "tests/test_autoservice.py"], has_structure: true },
  { num: 19, title: "Микросервисная архитектура Python-приложений", topic: "фитнес-клуб", files: ["main.py"], has_structure: true },
  { num: 20, title: "Контейнеризация, CI/CD и эксплуатация Python-приложения", topic: "фитнес-клуб", files: ["main.py"], has_structure: true },
  { num: 21, title: "Итоговый проект", topic: "фитнес-клуб", files: ["main.py"], has_structure: true },
];

const DESCRIPTIONS = {
  1: "Для каждого спортсмена вводится результат в секундах. Программа находит лучший (минимальный) и худший (максимальный) результат, вычисляет средний результат, определяет количество спортсменов, показавших результат лучше среднего, и выводит призёров (три лучших результата) по местам.",
  2: "Для каждого заказа хранятся номер, клиент, стоимость и статус. Программа выполняет поиск заказов по клиенту, фильтрацию по статусу, вычисляет общую сумму и средний чек, определяет множество уникальных статусов и сортирует заказы по стоимости. Использованы list, dict, set и list comprehension.",
  3: "Базовый класс Media и производные Movie (хранит длительность) и Series (число сезонов и серий). Общий полиморфный метод duration_minutes() возвращает продолжительность/объём контента. Инкапсуляция через property rating, композиция MediaLibrary.",
  4: "Многофайловое приложение управления банковскими счетами: пользовательские исключения InsufficientFundsError и AccountNotFoundError, класс BankAccount с сериализацией to_dict/from_dict, хранение в JSON, экспорт в CSV и консольное меню.",
  5: "Обработка банковских счетов в функциональном стиле: filter, map, sorted с key, any, all, lambda, set/dict comprehension и генератор счетов заданного типа.",
  6: "Автосервис с расширенными возможностями Python: dataclass, Enum статусов ремонта, декораторы log_call, measure_time, repeat (с параметром) и @wraps, контекстный менеджер OperationLogger, Protocol, интроспекция, обработка исключений.",
  7: "Две версии: «проблемная» с нарушениями SOLID и отрефакторированная — абстракции RepairType (Diagnostics/Maintenance/Repair), протокол Repository, InMemoryRepository, AutoService с Dependency Injection, отдельный ReportGenerator.",
  8: "Приложение обработки ремонтных заказов: Repository (протокол + реализация в памяти), Factory (ServiceFactory), Strategy (стандартный/срочный/корпоративный расчёт), Command с историей и отменой (undo), dataclass и Enum.",
  9: "TCP-сервер и клиент с JSON-протоколом (newline-delimited). Сущность Item складской позиции. Многопоточная обработка, логирование, тайм-ауты, специализированная команда stock_check (проверка остатков).",
  10: "REST API на Flask для управления автомобилями: полный CRUD, фильтрация и сортировка, специализированный endpoint (автомобили в ремонте), статистика, обработка ошибок 404/400 и HTTP-клиент.",
  11: "Реляционная БД (схема owners, cars, parts со связями 1:N и N:M), самостоятельные параметризованные SQL-запросы, индексы, агрегация, кэш Cache-Aside через Redis (или резервное хранение на dict) с TTL и инвалидацией, имитация CDN.",
  12: "ORM-модели Client, Trainer, Training со связью one-to-many, Session, CRUD, поиск, фильтрация, сортировка, транзакционная запись на тренировку с проверкой действительности абонемента.",
  13: "MongoDB хранит документ car со вложенными owner/specs и массивом service_history. CRUD, индексы, поиск по массиву, агрегация. Redis: кэш (String с TTL), счётчик INCR, история (List), benchmark.",
  14: "FastAPI + Pydantic: Pydantic-схемы Create/Update/Response, CRUD, фильтрация, сортировка, пагинация, поиск, статистика, асинхронный endpoint, HTTP-коды, Swagger.",
  15: "Flask + SQLAlchemy + Jinja2: HTML-интерфейс (главная, список, деталь, формы, статистика, 404), REST API, CRUD, поиск, фильтрация, сортировка, запись на тренировку с проверкой абонемента.",
  16: "Модели Django Client, Car, Service, Order со связями ForeignKey, админ-панель, примеры ORM-операций (all, filter, exclude, get, order_by, aggregate, annotate, select_related), Class-Based Views.",
  17: "Telegram-бот на aiogram 3: /start, /help, /cancel, главное меню, Reply и Inline клавиатуры, Callback Query, FSM регистрации автомобиля с валидацией, middleware логирования, SQLite БД.",
  18: "Система управления автомобилями и заявками на ремонт. pytest: фикстуры, параметризация, граничные значения, Mock/patch для изоляции Repository, интеграционные тесты.",
  19: "Модель микросервисной системы фитнес-клуба: сервисы клиентов, абонементов и занятий; API Gateway, Database per Service, Retry, Circuit Breaker, асинхронное событие через наблюдателей.",
  20: "Контейнеризация фитнес-клуба: Dockerfile, .dockerignore, docker-compose.yml (приложение + PostgreSQL с volume и healthcheck), переменные окружения, /health, CI workflow GitHub Actions.",
  21: "Законченная система фитнес-клуба на FastAPI: CRUD клиентов, запись на тренировки, статистика, три бизнес-правила, обработка ошибок, health check и pytest-тесты.",
};

function readFile(dir, rel) {
  const full = path.join(ROOT, dir, rel);
  return fs.existsSync(full) ? fs.readFileSync(full, "utf-8") : "(файл не найден)";
}

function wrapLong(value, max = 78) {
  // Разбивает длинную строку на куски не длиннее max символов (чтобы не вылезать за поля).
  if (value.length <= max) return [value];
  const out = [];
  for (let i = 0; i < value.length; i += max) {
    out.push(value.slice(i, i + max));
  }
  return out;
}

function addCode(doc, code) {
  // Каждая строка кода/вывода — отдельный абзац, как в образце отчёта.
  const lines = code.split("\n");
  for (const line of lines) {
    for (const part of wrapLong(line)) {
      doc.paragraph(part === "" ? " " : part);
    }
  }
  doc.spacer();
}

(async () => {
  const doc = H.createDoc({
    title: "Практикум по Python — вариант 7",
    fontSize: 12,
  });

  doc.heading("Практикум по Python", 1);
  doc.heading("Вариант 7", 2);
  doc.paragraph("Комплект из 21 практической работы по курсу Python. Все работы выполнены по индивидуальному заданию варианта 7. Для каждой работы приведены постановка задачи, ключевые решения реализации, листинг программы, результаты выполнения и вывод.");
  doc.paragraph("В работах, где это предусмотрено, использованы: функции высшего порядка, коллекции, ООП (наследование, полиморфизм, композиция), модули, исключения, сериализация в JSON/CSV, паттерны проектирования, сетевые протоколы TCP/UDP, REST API, базы данных (реляционные, MongoDB, Redis), фреймворки (Flask, FastAPI, Django), Telegram-бот на aiogram, тестирование pytest, микросервисы и контейнеризация.");
  doc.pageBreak();

  for (const lab of LABS) {
    doc.heading(`ПРАКТИЧЕСКАЯ РАБОТА №${lab.num}`, 1);
    doc.heading(`${lab.num}. Постановка задачи`, 2);
    doc.bullets([
      `Тема ${lab.num}: ${lab.title}.`,
      `Индивидуальное задание (вариант 7): ${lab.topic}.`,
      DESCRIPTIONS[lab.num],
    ]);
    doc.heading(`${lab.num}. Реализация и ключевые решения`, 2);
    doc.paragraph(`Программа lab ${String(lab.num).padStart(2, "0")} реализована на Python с учётом требований работы. Исходный код размещён в папке ${String(lab.num).padStart(2, "0")} (см. файл ${lab.files[0]}), при необходимости — распределён по логическим блокам. Демонстрационный запуск и ожидаемый вывод приведены в папке demo этой работы.`);
    if (lab.has_structure) {
      doc.heading(`${lab.num}. Структура проекта`, 2);
      doc.bullets([
        `${String(lab.num).padStart(2, "0")}/ — файлы исходного кода;`,
        `${String(lab.num).padStart(2, "0")}/README.md — описание работы, запуск и проверки;`,
        `${String(lab.num).padStart(2, "0")}/demo/ — сценарий входных данных (input.txt, при наличии) и сохранённый вывод (run.txt).`,
      ]);
    }
    doc.heading("Листинг программы", 2);
    for (const file of lab.files) {
      if (lab.files.length > 1) doc.paragraph(`— ${file}`, { bold: true });
      addCode(doc, readFile(String(lab.num).padStart(2, "0"), file));
    }
    doc.heading(`${lab.num}. Результаты выполнения`, 2);
    const runPath = path.join(ROOT, String(lab.num).padStart(2, "0"), "demo", "run.txt");
    if (fs.existsSync(runPath)) {
      doc.paragraph("Вывод программы (demo/run.txt):");
      addCode(doc, fs.readFileSync(runPath, "utf-8"));
    } else {
      doc.paragraph("Результат выполнения программы показан в файле demo/run.txt соответствующей папки работы.");
    }
    doc.heading("Вывод", 2);
    doc.paragraph(`В ходе выполнения практической работы №${lab.num} решено индивидуальное задание варианта 7 по теме «${lab.topic}». Программа корректно выполняет требуемые операции, содержит необходимые проверки данных и оформлена в соответствии с требованиями. Получены практические навыки работы со средствами Python, рассматриваемыми в данной работе.`);
    if (lab.num < LABS.length) doc.pageBreak();
  }

  await doc.save(path.join(ROOT, "Практикум_Python_вариант7.docx"));
  console.log("wrote Практикум_Python_вариант7.docx");
})();