import json
import os

from models import ValidationError, Workout

PROJECT_FOLDER = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(PROJECT_FOLDER, "data")
DEFAULT_PATH = os.path.join(DATA_FOLDER, "workouts.json")


class StorageError(Exception):
    pass

def quarantine_file(path):
    name_without_extension, extension = os.path.splitext(path)
    broken_path = name_without_extension + ".broken" + extension

    try:
        os.replace(path, broken_path)
    except OSError as error:
        raise StorageError(
            "Файл пошкоджений, але його не вдалося перейменувати: " + str(error)
        )

    return broken_path


def load_workouts(path=DEFAULT_PATH):
    if not os.path.exists(path):
        return [], []

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except OSError as error:
        raise StorageError("Не вдалося прочитати файл: " + str(error))
    except (ValueError, UnicodeError):
        data = None

    if not isinstance(data, list):
        broken_path = quarantine_file(path)
        warning = (
            "Файл даних пошкоджений. Його збережено як "
            + os.path.basename(broken_path)
            + ". Програма почала з порожнього списку."
        )
        return [], [warning]

    workouts = []
    warnings = []

    number = 1
    for item in data:
        try:
            workout = Workout.from_dict(item)
            workouts.append(workout)
        except ValidationError as error:
            warnings.append("Запис №" + str(number) + " пропущено: " + str(error))
        number += 1

    return workouts, warnings


def save_workouts(workouts, path=DEFAULT_PATH):
    folder = os.path.dirname(path)
    temporary_path = path + ".tmp"

    data = []
    for workout in workouts:
        data.append(workout.to_dict())

    text = json.dumps(data, ensure_ascii=False, indent=2)

    try:
        if folder and not os.path.exists(folder):
            os.makedirs(folder)

        with open(temporary_path, "w", encoding="utf-8") as file:
            file.write(text)

        os.replace(temporary_path, path)

    except OSError as error:
        raise StorageError("Не вдалося зберегти дані: " + str(error))
