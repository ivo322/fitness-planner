import flet as ft

from services import (
    Planner,
    StorageError,
    ValidationError,
    format_date,
    today_text,
)
from models import MAX_DURATION, MAX_REPS, MIN_DURATION, MIN_REPS

MAX_SHOWN_WARNINGS = 8
DEBUG_MODE = False


class PlannerApp:

    def __init__(self, page, planner):
        self.page = page
        self.planner = planner
        self.query = ""
        self.selected_index = None
        self._week_view = None

        # Поля форми додавання тренування
        self.day_field = ft.TextField(
            label="Дата (ДД.ММ.РРРР)", value=today_text(), width=190
        )
        self.exercise_field = ft.TextField(
            label="Вправа", width=260
        )
        self.duration_field = ft.TextField(
            label="Тривалість, хв", width=150, keyboard_type=ft.KeyboardType.NUMBER
        )
        self.reps_field = ft.TextField(
            label="Повторення", width=150, keyboard_type=ft.KeyboardType.NUMBER
        )
        self.done_checkbox = ft.Checkbox(label="Вже виконано", value=False)

        # Поля пошуку та вибору тижня
        self.search_field = ft.TextField(
            label="Пошук за датою або вправою", width=280,
            on_submit=self.on_search,
        )
        self.week_field = ft.TextField(
            label="Будь-яка дата тижня", value=today_text(), width=190
        )

        # Написи та індикатор результатів
        self.table_info = ft.Text("Записів: 0")
        self.summary_text = ft.Text(
            "Оберіть дату тижня й натисніть одну з кнопок нижче.",
            selectable=True,
        )
        self.progress_text = ft.Text("", visible=False)
        self.progress_bar = ft.ProgressBar(
            width=320,
            value=0,
            visible=False
        )
        self.status_text = ft.Text("Готово до роботи.")

        self.table = ft.DataTable(
            columns=[
                ft.DataColumn(label=ft.Text("Дата")),
                ft.DataColumn(label=ft.Text("Вправа")),
                ft.DataColumn(label=ft.Text("Хвилини")),
                ft.DataColumn(label=ft.Text("Повтори")),
                ft.DataColumn(label=ft.Text("Статус")),
            ],
            rows=[],
            show_checkbox_column=True,
            column_spacing=24,
        )

        self._build_page()
        self.refresh_table()

    #створення інтерфейсу

    def _build_page(self):
        self.page.title = "Фітнес-планувальник"
        self.page.padding = 20
        self.page.theme_mode = ft.ThemeMode.LIGHT

        form_section = ft.Column(
            controls=[
                ft.Text("Нове тренування", size=20, weight=ft.FontWeight.BOLD),
                ft.Row(
                    controls=[self.day_field, self.exercise_field],
                    wrap=True,
                    spacing=12,
                ),
                ft.Row(
                    controls=[
                        self.duration_field,
                        self.reps_field,
                        self.done_checkbox,
                        ft.Button("Додати", on_click=self.on_add),
                        ft.OutlinedButton("Очистити", on_click=self.clear_form),
                    ],
                    wrap=True,
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(
                    f"Тривалість: {MIN_DURATION}–{MAX_DURATION} хв. "
                    f"Повторення: {MIN_REPS}–{MAX_REPS} "
                    "(0 — для вправ без повторень, наприклад біг).",
                    size=12,
                    color=ft.Colors.GREY_700,
                ),
            ],
            spacing=10,
        )

        search_section = ft.Row(
            controls=[
                self.search_field,
                ft.Button("Знайти", on_click=self.on_search),
                ft.OutlinedButton("Показати всі", on_click=self.on_show_all),
            ],
            wrap=True,
            spacing=10,
        )

        table_section = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Тренування", size=20, weight=ft.FontWeight.BOLD),
                        self.table_info,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                search_section,
                ft.Row(
                    controls=[self.table],
                    scroll=ft.ScrollMode.AUTO,
                ),
                ft.Text(
                    "Щоб вибрати запис, поставте позначку зліва від нього.",
                    size=12,
                    color=ft.Colors.GREY_700,
                ),
                ft.Row(
                    controls=[
                        ft.Button(
                            "Відмітити / зняти виконання",
                            on_click=self.on_toggle,
                        ),
                        ft.OutlinedButton(
                            "Видалити",
                            on_click=self.on_delete,
                        ),
                    ],
                    wrap=True,
                    spacing=10,
                ),
            ],
            spacing=12,
        )

        week_section = ft.Column(
            controls=[
                ft.Text("Тижнева статистика", size=20, weight=ft.FontWeight.BOLD),
                ft.Row(
                    controls=[
                        self.week_field,
                        ft.Button("Підсумок тижня", on_click=self.on_week_summary),
                        ft.Button("План і факт", on_click=self.on_plan_vs_fact),
                    ],
                    wrap=True,
                    spacing=10,
                ),
                self.summary_text,
                ft.Row(
                    controls=[self.progress_bar, self.progress_text],
                    wrap=True,
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=10,
        )

        self.page.add(
            ft.Column(
                controls=[
                    ft.Text("Фітнес-планувальник", size=28, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "Плануйте тренування, відмічайте виконане та стежте за результатом.",
                        color=ft.Colors.GREY_700,
                    ),
                    ft.Divider(),
                    form_section,
                    ft.Divider(),
                    table_section,
                    ft.Divider(),
                    week_section,
                    ft.Divider(),
                    self.status_text,
                ],
                spacing=14,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )
        )

    #повідомлення

    def show_message(self, title, message):
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Text(message, selectable=True),
            actions=[
                ft.TextButton("Зрозуміло", on_click=lambda _event: self.page.pop_dialog())
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dialog)

    def show_error(self, message):
        self.status_text.value = "Помилка: " + message
        self.show_message("Помилка", message)
        self.page.update()

    def show_load_warnings(self):
        warnings = self.planner.warnings
        if not warnings:
            return

        message = "\n".join(warnings[:MAX_SHOWN_WARNINGS])
        extra = len(warnings) - MAX_SHOWN_WARNINGS
        if extra > 0:
            message += f"\n…та ще {extra}."

        self.status_text.value = f"Попереджень під час завантаження: {len(warnings)}"
        self.show_message("Файл даних завантажено з попередженнями", message)

    def handle_error(self, error):
        if DEBUG_MODE:
            breakpoint()
        self.show_error(str(error))

    #таблиця та форма

    def refresh_table(self):
        rows = []

        for index, workout in self.planner.rows(self.query):
            rows.append(
                ft.DataRow(
                    data=index,
                    selected=(index == self.selected_index),
                    on_select_change=self.on_row_select,
                    cells=[
                        ft.DataCell(ft.Text(format_date(workout.day))),
                        ft.DataCell(ft.Text(workout.exercise)),
                        ft.DataCell(ft.Text(str(workout.duration))),
                        ft.DataCell(ft.Text(str(workout.reps))),
                        ft.DataCell(
                            ft.Text("✓ Виконано" if workout.done else "Заплановано")
                        ),
                    ],
                )
            )

        self.table.rows = rows
        self.table_info.value = f"Записів: {len(rows)}"
        self.page.update()

    def on_row_select(self, event):
        # У Flet новий стан прапорця передається в event.data
        # event.control.selected може ще містити попереднє значення
        is_selected = event.data in (True, 1, "true", "True")
        row_index = event.control.data

        if is_selected:
            self.selected_index = row_index
        elif self.selected_index == row_index:
            self.selected_index = None

        # Одночасно може бути вибраний лише один запис
        for row in self.table.rows:
            row.selected = (row.data == self.selected_index)

        self.page.update()

    def clear_form(self, _event=None, keep_date=False):
        if not keep_date:
            self.day_field.value = today_text()
        self.exercise_field.value = ""
        self.duration_field.value = ""
        self.reps_field.value = ""
        self.done_checkbox.value = False
        self.page.update()

    def selected_record_index(self):
        if self.selected_index is None:
            self.status_text.value = "Спочатку виберіть запис у таблиці."
            self.page.update()
            self.show_message("Немає вибору", "Спочатку виберіть запис у таблиці.")
            return None
        return self.selected_index

    #операції користувача

    def on_add(self, _event=None):
        try:
            workout = self.planner.add(
                self.day_field.value,
                self.exercise_field.value,
                self.duration_field.value,
                self.reps_field.value,
                self.done_checkbox.value,
            )

            search_was_active = bool(self.query)
            self.query = ""
            self.search_field.value = ""
            self.selected_index = None
            self.clear_form(keep_date=True)
            self.after_data_change()

            message = f"Додано: {format_date(workout.day)} — {workout.exercise}"
            if search_was_active:
                message += ". Пошук скинуто, щоб запис було видно."
            self.status_text.value = message
            self.page.update()
        except (ValidationError, StorageError) as error:
            self.handle_error(error)
        except Exception as error:
            self.handle_error(error)

    def on_toggle(self, _event=None):
        index = self.selected_record_index()
        if index is None:
            return

        try:
            done = self.planner.toggle(index)
            self.after_data_change()
            self.selected_index = index
            self.refresh_table()
            self.status_text.value = (
                "Відмічено як виконане." if done else "Відмітку виконання знято."
            )
            self.page.update()
        except (ValidationError, StorageError) as error:
            self.handle_error(error)
        except Exception as error:
            self.handle_error(error)

    def on_delete(self, _event=None):
        index = self.selected_record_index()
        if index is None:
            return

        workout = self.planner.workouts[index]
        day_text = format_date(workout.day)
        exercise = workout.exercise

        def cancel_delete(_event):
            self.page.pop_dialog()

        def confirm_delete(_event):
            self.page.pop_dialog()
            try:
                self.planner.remove(index)
                self.selected_index = None
                self.after_data_change()
                self.status_text.value = "Запис видалено."
                self.page.update()
            except (ValidationError, StorageError) as error:
                self.handle_error(error)
            except Exception as error:
                self.handle_error(error)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Підтвердження видалення"),
            content=ft.Text(f"Видалити вправу «{exercise}» від {day_text}?"),
            actions=[
                ft.TextButton("Скасувати", on_click=cancel_delete),
                ft.Button("Видалити", on_click=confirm_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dialog)

    def on_search(self, _event=None):
        self.query = (self.search_field.value or "").strip()
        self.selected_index = None
        self.refresh_table()
        count = len(self.table.rows)
        self.status_text.value = (
            f"Знайдено записів: {count}" if self.query
            else f"Показано всі записи: {count}"
        )
        self.page.update()

    def on_show_all(self, _event=None):
        self.search_field.value = ""
        self.query = ""
        self.selected_index = None
        self.refresh_table()
        self.status_text.value = f"Показано всі записи: {len(self.table.rows)}"
        self.page.update()

    def render_week(self, kind, date_text):
        if kind == "summary":
            result = self.planner.week_summary(date_text)
            self.summary_text.value = (
                f"Тиждень {format_date(result.start)} – {format_date(result.end)}\n"
                f"Виконано тренувань: {result.done_count}\n"
                f"Сумарна тривалість виконаних: {result.total_minutes} хв"
            )
            self.progress_text.visible = True
            self.progress_bar.value = 0
            self.progress_bar.visible = False
            self.progress_text.value = "Підсумок виконаних тренувань"

        else:
            result = self.planner.plan_vs_fact(date_text)
            self.summary_text.value = (
                f"Тиждень {format_date(result.start)} – {format_date(result.end)} "
                "(виконано / заплановано)\n"
                f"Тренування: {result.done_count} / {result.planned_count} "
                f"({result.count_percent:.1f}%)\n"
                f"Хвилини: {result.done_minutes} / {result.planned_minutes} "
                f"({result.minutes_percent:.1f}%)\n"
                f"Повторення: {result.done_reps} / {result.planned_reps} "
                f"({result.reps_percent:.1f}%)"
            )
            self.progress_text.visible = True
            self.progress_bar.value = result.minutes_percent / 100
            self.progress_bar.visible = True
            self.progress_text.value = (
                f"Виконання плану: {result.minutes_percent:.1f}% за хвилинами"
            )

        self._week_view = (kind, date_text)
        self.page.update()

    def after_data_change(self):
        self.refresh_table()
        if self._week_view:
            self.render_week(*self._week_view)

    def on_week_summary(self, _event=None):
        try:
            self.render_week("summary", self.week_field.value)
            self.status_text.value = "Підсумок тижня обчислено."
            self.page.update()
        except (ValidationError, StorageError) as error:
            self.handle_error(error)
        except Exception as error:
            self.handle_error(error)

    def on_plan_vs_fact(self, _event=None):
        try:
            self.render_week("plan", self.week_field.value)
            self.status_text.value = (
                "План і факт порівняно за тренуваннями, за хвилинами."
            )
            self.page.update()
        except (ValidationError, StorageError) as error:
            self.handle_error(error)
        except Exception as error:
            self.handle_error(error)


def run_app():
    def main(page):
        try:
            planner = Planner()
        except StorageError as error:
            page.add(ft.Text("Не вдалося запустити програму: " + str(error)))
            return

        app = PlannerApp(page, planner)
        if planner.warnings:
            app.show_load_warnings()

    ft.run(main)
