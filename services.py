"""Основні операції фітнес-планувальника.

У цьому модулі немає Flet, input() або print().
Функції працюють зі списком Workout, а клас Planner відповідає за збереження.
"""
from datetime import date, datetime, timedelta

from models import (
    ValidationError,
    Workout,
    check_day,
    clean_exercise
)
from storage import DEFAULT_PATH, StorageError, load_workouts, save_workouts


def parse_date(text):
    """Перетворює текст на дату. Підтримує ДД.ММ.РРРР та РРРР-ММ-ДД."""
    text = (text or "").strip()

    if not text:
        raise ValidationError("Вкажіть дату у форматі ДД.ММ.РРРР.")

    try:
        parsed = datetime.strptime(text, "%d.%m.%Y").date()
    except ValueError:
        try:
            parsed = datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError(
                "Введіть коректну дату у форматі ДД.ММ.РРРР, "
                "наприклад 25.11.2026."
            )

    return check_day(parsed)


def parse_int(text, label):
    """Перевіряє, що у полі введено ціле число."""
    text = (text or "").strip()

    if not text:
        raise ValidationError("Поле «" + label + "» не може бути порожнім.")

    # Дозволяємо цифри та знак мінус на першому місці.
    digits = text
    if digits.startswith(("-", "+")):
        digits = digits[1:]

    if not digits or not digits.isdigit():
        raise ValidationError("Поле «" + label + "» має бути цілим числом.")

    try:
        return int(text)
    except ValueError:
        # Наприклад, коли введено надто довге число.
        raise ValidationError(
            "Поле «" + label + "» має бути цілим числом у розумних межах."
        )


def format_date(day):
    return day.strftime("%d.%m.%Y")


def today_text():
    return format_date(date.today())


def check_index(workouts, index):
    """Перевіряє, чи існує вибраний номер запису."""
    if isinstance(index, bool) or not isinstance(index, int):
        raise ValidationError("Неправильний номер запису.")

    if index < 0 or index >= len(workouts):
        raise ValidationError(
            "Запис не знайдено. Оновіть таблицю й виберіть запис ще раз."
        )


def add_workout(workouts, date_text, exercise, duration_text, reps_text, done=False):
    """Перевіряє введення та додає нове тренування."""
    day = parse_date(date_text)
    name = clean_exercise(exercise)
    duration = parse_int(duration_text, "Тривалість")
    reps = parse_int(reps_text, "Повторення")

    workout = Workout(day, name, duration, reps, bool(done))

    # Не дозволяємо додати ту саму вправу на ту саму дату двічі.
    for old_workout in workouts:
        same_day = old_workout.day == workout.day
        same_exercise = old_workout.exercise.casefold() == workout.exercise.casefold()

        if same_day and same_exercise:
            raise ValidationError("Такий запис уже є: та сама дата і вправа.")

    workouts.append(workout)
    return workout


def toggle_done(workouts, index):
    """Змінює статус тренування на протилежний."""
    check_index(workouts, index)
    workouts[index].done = not workouts[index].done
    return workouts[index].done


def delete_workout(workouts, index):
    """Видаляє вибраний запис."""
    check_index(workouts, index)
    return workouts.pop(index)


def search(workouts, query):
    """Шукає за датою або частиною назви вправи."""
    query = (query or "").strip()
    rows = list(enumerate(workouts))

    if query:
        # Спочатку пробуємо сприйняти запит як дату.
        day = None
        try:
            day = parse_date(query)
        except ValidationError:
            pass

        if day is not None:
            filtered = []
            for index, workout in rows:
                if workout.day == day:
                    filtered.append((index, workout))
            rows = filtered
        else:
            filtered = []
            for index, workout in rows:
                if query.casefold() in workout.exercise.casefold():
                    filtered.append((index, workout))
            rows = filtered

    # Сортування за датою.
    rows.sort(key=lambda row: (row[1].day, row[0]))
    return rows


class WeekSummary:

    def __init__(self, start, end, total_minutes, done_count):
        self.start = start
        self.end = end
        self.total_minutes = total_minutes
        self.done_count = done_count


class PlanFact:

    def __init__(self, start, end, planned_count, done_count,
                 planned_minutes, done_minutes, planned_reps, done_reps):
        self.start = start
        self.end = end
        self.planned_count = planned_count
        self.done_count = done_count
        self.planned_minutes = planned_minutes
        self.done_minutes = done_minutes
        self.planned_reps = planned_reps
        self.done_reps = done_reps

        self.count_percent = self.get_percent(done_count, planned_count)
        self.minutes_percent = self.get_percent(done_minutes, planned_minutes)
        self.reps_percent = self.get_percent(done_reps, planned_reps)

    @staticmethod
    def get_percent(done, planned):
        if planned == 0:
            return 0.0
        return round(done * 100 / planned, 1)


def week_bounds(day):
    monday = day - timedelta(days=day.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def week_summary(workouts, day):
    start, end = week_bounds(day)
    total_minutes = 0
    done_count = 0

    for workout in workouts:
        if workout.done and start <= workout.day <= end:
            total_minutes += workout.duration
            done_count += 1

    return WeekSummary(start, end, total_minutes, done_count)


def plan_vs_fact(workouts, start, end):
    if start > end:
        raise ValidationError("Початок періоду не може бути пізніше за кінець.")

    planned = []
    done = []

    for workout in workouts:
        if start <= workout.day <= end:
            planned.append(workout)
            if workout.done:
                done.append(workout)

    planned_minutes = sum(item.duration for item in planned)
    done_minutes = sum(item.duration for item in done)
    planned_reps = sum(item.reps for item in planned)
    done_reps = sum(item.reps for item in done)

    return PlanFact(
        start,
        end,
        len(planned),
        len(done),
        planned_minutes,
        done_minutes,
        planned_reps,
        done_reps
    )


class Planner:

    def __init__(self, path=DEFAULT_PATH):
        self.path = path
        self.workouts, self.warnings = load_workouts(path)

    def save_change(self, change_function):
        backup = []
        for workout in self.workouts:
            backup.append(
                Workout(
                    workout.day,
                    workout.exercise,
                    workout.duration,
                    workout.reps,
                    workout.done
                )
            )

        try:
            result = change_function(self.workouts)
            save_workouts(self.workouts, self.path)
            return result
        except StorageError:
            self.workouts = backup
            raise

    def add(self, date_text, exercise, duration_text, reps_text, done=False):
        return self.save_change(
            lambda items: add_workout(
                items, date_text, exercise, duration_text, reps_text, done
            )
        )

    def toggle(self, index):
        return self.save_change(lambda items: toggle_done(items, index))

    def remove(self, index):
        return self.save_change(lambda items: delete_workout(items, index))

    def rows(self, query=""):
        return search(self.workouts, query)

    @staticmethod
    def get_day(date_text):
        if (date_text or "").strip():
            return parse_date(date_text)
        return date.today()

    def week_summary(self, date_text=""):
        return week_summary(self.workouts, self.get_day(date_text))

    def plan_vs_fact(self, date_text=""):
        start, end = week_bounds(self.get_day(date_text))
        return plan_vs_fact(self.workouts, start, end)
