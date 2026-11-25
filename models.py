from datetime import date

MIN_DURATION = 1
MAX_DURATION = 600
MIN_REPS = 0
MAX_REPS = 1000
MAX_EXERCISE_LEN = 50

MIN_DATE = date(2000, 1, 1)
MAX_DATE = date(2100, 12, 31)


class ValidationError(ValueError):
    pass


def check_day(day):
    if not isinstance(day, date):
        raise ValidationError("Дата має бути коректною календарною датою.")

    if day < MIN_DATE or day > MAX_DATE:
        raise ValidationError(
            "Дата має бути в межах "
            + MIN_DATE.strftime("%d.%m.%Y")
            + " – "
            + MAX_DATE.strftime("%d.%m.%Y")
            + "."
        )

    return day


def clean_exercise(name):
    if not isinstance(name, str):
        raise ValidationError("Назва вправи має бути текстом.")

    cleaned = ""
    for symbol in name:
        if ord(symbol) == 8203 or ord(symbol) == 65279:
            continue
        if ord(symbol) < 32 and symbol not in ("\\t", "\\n", "\\r"):
            continue
        if ord(symbol) == 127:
            continue
        cleaned += symbol

    name = " ".join(cleaned.split())

    if not name:
        raise ValidationError("Вкажіть назву вправи.")

    if len(name) > MAX_EXERCISE_LEN:
        raise ValidationError(
            "Назва вправи не може бути довшою за "
            + str(MAX_EXERCISE_LEN)
            + " символів."
        )

    return name


def check_number(value, minimum, maximum, message):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(message)

    if value < minimum or value > maximum:
        raise ValidationError(message)

    return value


class Workout:

    def __init__(self, day, exercise, duration, reps, done=False):
        self.day = check_day(day)
        self.exercise = clean_exercise(exercise)

        self.duration = check_number(
            duration,
            MIN_DURATION,
            MAX_DURATION,
            "Тривалість має бути цілим числом від "
            + str(MIN_DURATION)
            + " до "
            + str(MAX_DURATION)
            + " хв."
        )

        self.reps = check_number(
            reps,
            MIN_REPS,
            MAX_REPS,
            "Кількість повторень має бути цілим числом від "
            + str(MIN_REPS)
            + " до "
            + str(MAX_REPS)
            + "."
        )

        if not isinstance(done, bool):
            raise ValidationError("Ознака «виконано» має бути True або False.")

        self.done = done

    def to_dict(self):

        return {
            "date": self.day.isoformat(),
            "exercise": self.exercise,
            "duration": self.duration,
            "reps": self.reps,
            "done": self.done
        }

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValidationError("Запис має бути JSON-об'єктом.")

        required_fields = ["date", "exercise", "duration", "reps", "done"]

        for field in required_fields:
            if field not in data:
                raise ValidationError("У записі відсутнє поле: " + field)

        try:
            day = date.fromisoformat(data["date"])
        except (TypeError, ValueError):
            raise ValidationError("Некоректна дата у файлі.")

        return cls(
            day,
            data["exercise"],
            data["duration"],
            data["reps"],
            data["done"]
        )
