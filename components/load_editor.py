import flet as ft
import time


class LoadEditor(ft.Row):
    def __init__(self, initial_load, exercise_id, on_save, supabase, enabled=False):
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
        if not self.enabled:
            return
        self.load_text.visible = False
        self.load_field.visible = True
        self.edit_button.visible = False
        self.save_button.visible = True
        self.update()

    def confirm_save(self, e):
        if not self.enabled:
            return

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

    def disable(self):
        self.enabled = False
        self.edit_button.disabled = True
        self.save_button.disabled = True
        self.update()
