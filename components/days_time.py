import flet as ft


def DaysTime(page: ft.Page):
    class checkbbox(ft.Checkbox):
        def __init__(self, label, value):
            super().__init__(label=label, value=value)
            self.label = label
            self.value = value
            self.on_change = self.handle_change

        def build(self):
            return ft.Checkbox(label=self.label, value=self.value)

        def handle_change(self, e):
            self.value = e.control.value
            page.update()
            print(f"Checkbox {self.label} changed to {self.value}")

    texto = ft.Text("Frequencia de treino:", size=24, weight=ft.FontWeight.BOLD)
    segunda = checkbbox("Segunda", False)
    terca = checkbbox("Terça", False)
    quarta = checkbbox("Quarta", False)
    quinta = checkbbox("Quinta", False)
    sexta = checkbbox("Sexta", False)
    sabado = checkbbox("Sábado", False)
    domingo = checkbbox("Domingo", False)

    return ft.Container(
        content=ft.Row(
            controls=[texto, segunda, terca, quarta, quinta, sexta, sabado, domingo],
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.HIDDEN,
        ),
        alignment=ft.alignment.center,
        padding=20,
        expand=True,
    )
