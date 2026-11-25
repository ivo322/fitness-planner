from datetime import date

from models import ValidationError
from services import (
    add_workout,
    delete_workout,
    plan_vs_fact,
    search,
    toggle_done,
    week_summary
)


def add(items, day="25.11.2026", exercise="Присідання",
        minutes="30", reps="20", done=False):
    return add_workout(items, day, exercise, minutes, reps, done)


def must_raise(function, *args):
    try:
        function(*args)
    except ValidationError:
        return
    raise AssertionError("Очікувалася помилка ValidationError.")


#5 позитивних тестів

def test_01_add_workout():
    items = []
    workout = add_workout(items, "25.11.2026", "  Присідання ", "30", "20")

    assert items == [workout]
    assert workout.day == date(2026, 11, 25)
    assert workout.exercise == "Присідання"
    assert workout.duration == 30
    assert workout.reps == 20
    assert workout.done is False


def test_02_toggle_done():
    items = []
    add(items)

    assert toggle_done(items, 0) is True
    assert items[0].done is True
    assert toggle_done(items, 0) is False
    assert items[0].done is False


def test_03_delete_workout():
    items = []
    add(items, exercise="Присідання")
    add(items, exercise="Планка")

    removed = delete_workout(items, 0)

    assert removed.exercise == "Присідання"
    assert len(items) == 1
    assert items[0].exercise == "Планка"


def test_04_search():
    items = []
    add(items, day="24.11.2026", exercise="Присідання")
    add(items, day="25.11.2026", exercise="Біг")

    assert [i for i, item in search(items, "присід")] == [0]
    assert [i for i, item in search(items, "25.11.2026")] == [1]
    assert len(search(items, "")) == 2


def test_05_plan_and_fact():
    items = []
    add(items, exercise="Біг", minutes="60", reps="0", done=True)
    add(items, exercise="Прес", minutes="30", reps="40")

    result = plan_vs_fact(
        items,
        date(2026, 11, 23),
        date(2026, 11, 29)
    )

    assert (result.planned_minutes, result.done_minutes) == (90, 60)
    assert result.minutes_percent == 66.7
    assert (result.planned_reps, result.done_reps) == (40, 0)
    assert result.reps_percent == 0.0
    assert (result.planned_count, result.done_count) == (2, 1)
    assert result.count_percent == 50.0


#2 негативних тести

def test_06_wrong_input():
    bad_data = [
        ("25.11.2026", "   ", "30", "20"),
        ("25.11.2026", "​﻿", "30", "20"),
        ("25.11.2026", "Біг", "abc", "20"),
        ("25.11.2026", "Біг", "30.5", "20"),
        ("31.02.2026", "Біг", "30", "20"),
        ("25.11.2026", "Біг", "", "20")
    ]

    for data in bad_data:
        items = []
        must_raise(add_workout, items, data[0], data[1], data[2], data[3])
        assert items == []


def test_07_wrong_index_and_duplicate():
    items = []
    add(items)

    for bad_index in (-1, 1, 99):
        must_raise(toggle_done, items, bad_index)
        must_raise(delete_workout, items, bad_index)

    must_raise(add, items, "25.11.2026", "присідання", "30", "20")
    assert len(items) == 1


#3 тести граничних значень

def test_08_field_limits():
    # Допустимі значення на межах.
    items = []
    add(items, exercise="Біг", minutes="1", reps="0")
    add(items, exercise="Б" * 50, minutes="600", reps="1000")
    assert len(items) == 2

    bad_data = [
        ("0", "10", "Біг"),
        ("601", "10", "Біг"),
        ("-5", "10", "Біг"),
        ("30", "-1", "Біг"),
        ("30", "1001", "Біг"),
        ("30", "10", "Б" * 51)
    ]

    for minutes, reps, name in bad_data:
        must_raise(add, [], "25.11.2026", name, minutes, reps)


def test_09_week_boundaries():
    items = []
    add(items, day="22.11.2026", exercise="Минула неділя", done=True)
    add(items, day="23.11.2026", exercise="Понеділок", minutes="20", done=True)
    add(items, day="26.11.2026", exercise="Не виконано", minutes="99")
    add(items, day="29.11.2026", exercise="Неділя", minutes="40", done=True)
    add(items, day="30.11.2026", exercise="Наступний понеділок", done=True)

    result = week_summary(items, date(2026, 11, 25))

    assert result.start == date(2026, 11, 23)
    assert result.end == date(2026, 11, 29)
    assert result.done_count == 2
    assert result.total_minutes == 60


def test_10_empty_week():
    week_start = date(2026, 11, 23)
    week_end = date(2026, 11, 29)

    result = plan_vs_fact([], week_start, week_end)

    assert result.planned_minutes == 0
    assert result.done_minutes == 0
    assert result.count_percent == 0.0
    assert result.minutes_percent == 0.0
    assert result.reps_percent == 0.0

    items = []
    add(items, day="01.01.2026")
    result = plan_vs_fact(items, week_start, week_end)
    assert result.planned_count == 0

    must_raise(plan_vs_fact, [], week_end, week_start)


def run_tests():
    tests = [
        test_01_add_workout,
        test_02_toggle_done,
        test_03_delete_workout,
        test_04_search,
        test_05_plan_and_fact,
        test_06_wrong_input,
        test_07_wrong_index_and_duplicate,
        test_08_field_limits,
        test_09_week_boundaries,
        test_10_empty_week
    ]

    passed = 0

    for test in tests:
        try:
            test()
            print("OK:", test.__name__)
            passed += 1
        except Exception as error:
            print("ПОМИЛКА:", test.__name__, "-", error)

    print("Пройдено тестів:", passed, "з", len(tests))
    return passed == len(tests)


if __name__ == "__main__":
    if run_tests():
        print("Усі тести успішні.")
    else:
        print("Є тести з помилками.")
