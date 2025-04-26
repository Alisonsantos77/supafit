import flet as ft
from components.timer_dialog import TimerDialog
from components.custom_list_tile import CustomListTile
import time
import threading


class LoadEditor(ft.Row):
    def __init__(self, initial_load, exercise_id, on_save, supabase, enabled=True):
        super().__init__()
        self.initial_load = initial_load
        self.exercise_id = exercise_id
        self.on_save = on_save
        self.supabase = supabase
        self.enabled = enabled

        self.load_text = ft.Text(f"{initial_load}kg")
        self.load_field = ft.TextField(
            value=str(initial_load),
            width=100,
            keyboard_type=ft.KeyboardType.NUMBER,
            visible=False,
            label="Carga (kg)",
        )
        self.edit_button = ft.IconButton(
            icon=ft.Icons.EDIT,
            on_click=self.start_edit,
            tooltip="Editar carga",
            disabled=not self.enabled,
        )
        self.save_button = ft.IconButton(
            icon=ft.Icons.SAVE,
            visible=False,
            on_click=self.confirm_save,
            tooltip="Salvar carga",
            disabled=not self.enabled,
        )

        self.controls = [
            self.load_text,
            self.load_field,
            self.edit_button,
            self.save_button,
        ]
        self.spacing = 5
        self.alignment = ft.MainAxisAlignment.END

    def start_edit(self, e):
        self.load_text.visible = False
        self.load_field.visible = True
        self.edit_button.visible = False
        self.save_button.visible = True
        self.update()

    def confirm_save(self, e):
        def save_confirmed(e):
            if e.control.text == "Sim":
                try:
                    load = float(self.load_field.value) if self.load_field.value else 0
                    self.supabase.table("progress").insert(
                        {
                            "exercise_id": self.exercise_id,
                            "load": load,
                            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    ).execute()
                    self.load_text.value = f"{load}kg"
                    self.on_save(load)
                    e.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Carga {load}kg salva!"), action="OK"
                    )
                    e.page.snack_bar.open = True
                except Exception as error:
                    e.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Erro ao salvar carga: {str(error)}"),
                        action="OK",
                    )
                    e.page.snack_bar.open = True
            e.page.close(confirm_dialog)
            self.load_text.visible = True
            self.load_field.visible = False
            self.edit_button.visible = True
            self.save_button.visible = False
            self.update()

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar Carga"),
            content=ft.Text(f"Deseja salvar a carga de {self.load_field.value}kg?"),
            actions=[
                ft.TextButton("Sim", on_click=save_confirmed),
                ft.TextButton("Não", on_click=save_confirmed),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        e.page.open(confirm_dialog)

    def enable(self):
        self.enabled = True
        self.edit_button.disabled = False
        self.save_button.disabled = False
        self.update()


def Treinopage(page: ft.Page, supabase, day):
    # Estado do treino
    training_started = False
    training_time = 0
    training_running = threading.Event()
    training_timer_ref = ft.Ref[ft.Text]()

    def start_training(e):
        nonlocal training_started, training_time
        training_started = True
        training_running.set()
        # Habilitar botões de intervalo e carga
        for card in exercise_grid.controls:
            for control in card.content.content.controls:
                if isinstance(control, CustomListTile):
                    control.trailing.enable()
                elif (
                    isinstance(control, ft.ElevatedButton)
                    and "Iniciar Intervalo" in control.text
                ):
                    control.disabled = False
        # Iniciar cronômetro global
        threading.Thread(target=run_training_timer, daemon=True).start()
        start_button.disabled = True
        page.update()

    def run_training_timer():
        nonlocal training_time
        while training_running.is_set():
            training_time += 1
            minutes, seconds = divmod(training_time, 60)
            training_timer_ref.current.value = (
                f"Tempo de Treino: {minutes:02d}:{seconds:02d}"
            )
            training_timer_ref.current.update()
            time.sleep(1)

    def stop_training(e):
        training_running.clear()
        page.go("/")

    def load_exercises(day):
        try:
            response = (
                supabase.table("exercises").select("*").eq("day", day.lower()).execute()
            )
            if not response.data:
                print(f"Nenhum exercício encontrado para {day}")
            return [
                {
                    **exercise,
                    "image_url": exercise.get("image_url", "https://picsum.photos/200"),
                }
                for exercise in (
                    response.data
                    or [
                        {
                            "id": "1",
                            "name": "Supino Reto",
                            "sets": 4,
                            "reps": 12,
                            "load": 0,
                            "image_url": "https://picsum.photos/200",
                        },
                        {
                            "id": "2",
                            "name": "Agachamento Livre",
                            "sets": 4,
                            "reps": 10,
                            "load": 0,
                            "image_url": "https://picsum.photos/200",
                        },
                    ]
                )
            ]
        except Exception as e:
            print(f"Erro ao carregar exercícios para {day}: {str(e)}")
            return [
                {
                    "id": "1",
                    "name": "Supino Reto",
                    "sets": 4,
                    "reps": 12,
                    "load": 0,
                    "image_url": "https://picsum.photos/200",
                },
                {
                    "id": "2",
                    "name": "Agachamento Livre",
                    "sets": 4,
                    "reps": 10,
                    "load": 0,
                    "image_url": "https://picsum.photos/200",
                },
            ]

    def update_load(load):
        pass

    # Carregar exercícios para o dia
    exercises = load_exercises(day)

    # TimerDialog
    timer_dialog = TimerDialog(duration=60)

    start_button = ft.ElevatedButton("Iniciar", on_click=start_training)

    # Cronômetro global
    training_timer = ft.Text(ref=training_timer_ref, value="Tempo de Treino: 00:00")

    exercise_grid = ft.ResponsiveRow(
        controls=[
            ft.Card(
                col={"xs": 12, "sm": 6, "md": 4},
                content=ft.Container(
                    content=ft.Column(
                        [
                            CustomListTile(
                                leading=ft.Image(
                                    src=exercise["image_url"],
                                    width=64,
                                    height=64,
                                    fit=ft.ImageFit.COVER,
                                    border_radius=ft.border_radius.all(10),
                                    error_content=ft.Icon(ft.Icons.ERROR),
                                ),
                                title=ft.Text(
                                    exercise["name"], weight=ft.FontWeight.BOLD
                                ),
                                subtitle=ft.Text(
                                    f"{exercise['sets']} séries x {exercise['reps']} repetições"
                                ),
                                trailing=LoadEditor(
                                    initial_load=exercise["load"],
                                    exercise_id=exercise["id"],
                                    on_save=update_load,
                                    supabase=supabase,
                                    enabled=False,
                                ),
                            ),
                            ft.ElevatedButton(
                                "Iniciar Intervalo (60s)",
                                on_click=lambda e: timer_dialog.start_timer(page),
                                disabled=True,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        expand=False,
                    ),
                    padding=5,
                    width=350,
                ),
                elevation=3,
            )
            for exercise in exercises
        ],
        columns=12,
        spacing=10,
        run_spacing=10,
    )

    return ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    f"Treino de {day.capitalize()}", size=24, weight=ft.FontWeight.BOLD
                ),
                start_button,
                training_timer,
                exercise_grid,
                ft.ElevatedButton("Finalizar", on_click=stop_training),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=10,
    )
