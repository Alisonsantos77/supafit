import flet as ft
import asyncio
from .base_step import BaseStep, logger


class Carousel(ft.Row):
    def __init__(
        self,
        items: list[ft.Control],
        *,
        width=360,
        height=240,
        item_spacing=20,
        scroll_speed=10,
    ):
        super().__init__(scroll=ft.ScrollMode.ALWAYS)
        self.width = width
        self.height = height
        self.controls = items
        self.spacing = item_spacing
        self.scroll_speed = scroll_speed
        self._running = False
        logger.info("Carousel inicializado com %d itens", len(items))

    def did_mount(self):
        self._running = True
        logger.info("Carousel did_mount, iniciando auto scroll")
        if self.page:
            self.page.run_task(self._auto_scroll)

    async def _auto_scroll(self):
        await asyncio.sleep(0.2)
        item_width = self.controls[0].width if self.controls else 160
        max_scroll = len(self.controls) * (item_width + self.spacing) - self.width
        pos = 0
        direction = 1
        logger.info("Auto scroll: item_width=%d, max_scroll=%d", item_width, max_scroll)
        while self._running:
            await asyncio.sleep(0.05)
            pos += direction * self.scroll_speed
            if pos >= max_scroll or pos <= 0:
                direction *= -1
            try:
                self.scroll_to(pos, duration=0, curve=ft.AnimationCurve.BOUNCE_IN_OUT)
                self.update()
            except AssertionError:
                await asyncio.sleep(0.1)

    def will_unmount(self):
        self._running = False
        logger.info("Carousel will_unmount, parando auto scroll")


class ProfileItem(ft.Column):
    def __init__(self, label: str, value: str, icon, *, width: int = 160):
        logger.info("Criando ProfileItem: %s -> '%s'", label, value)
        controls = [
            ft.Icon(icon, size=40, color=ft.Colors.BLUE_400),
            ft.Text(
                label, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600
            ),
            ft.Text(value, size=16, weight=ft.FontWeight.BOLD),
        ]
        if label == "Restrições":
            controls[2] = ft.Text(
                value,
                size=14,
                weight=ft.FontWeight.NORMAL,
                width=width,
                max_lines=4,
                overflow=ft.TextOverflow.ELLIPSIS,
                no_wrap=False,
            )
        super().__init__(
            controls=controls,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )
        self.width = width


class Step8Review(BaseStep):
    """Etapa 8: Revisão dos dados do perfil com carrossel."""

    def __init__(
        self,
        page: ft.Page,
        profile_data: dict,
        current_step: list,
        on_next,
        on_previous,
        supabase_service=None,
        on_create=None,
    ):
        logger.info("Inicializando Step8Review com profile_data: %s", profile_data)
        super().__init__(
            page, profile_data, current_step, on_next, on_previous, on_create
        )
        self.supabase_service = supabase_service
        self.carousel: Carousel | None = None
        logger.info("Step8Review inicializado com sucesso.")

    def build_step_progress(self) -> ft.Control:
        steps = []
        for i in range(8):
            is_current = self.current_step[0] == i
            is_completed = self.current_step[0] > i
            steps.append(
                ft.Container(
                    width=30,
                    height=30,
                    border_radius=15,
                    bgcolor=ft.Colors.BLUE_400 if is_current else None,
                    border=ft.border.all(
                        2,
                        (
                            ft.Colors.BLUE_400
                            if is_current
                            else (
                                ft.Colors.GREEN_400
                                if is_completed
                                else ft.Colors.GREY_400
                            )
                        ),
                    ),
                    content=ft.Text(
                        str(i + 1),
                        color=ft.Colors.WHITE if is_current else ft.Colors.BLACK,
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    alignment=ft.alignment.center,
                    animate_opacity=300,
                    animate_scale=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                    scale=1.2 if is_current else 1.0,
                )
            )
        return ft.Row(steps, alignment=ft.MainAxisAlignment.CENTER, spacing=10)

    def build_view(self) -> ft.Control:
        logger.info("Construindo view Step8Review")
        header = ft.Text("Revisão do Perfil", size=22, weight=ft.FontWeight.BOLD)
        mascot = ft.Image(
            src="mascote_supafit/step_review.png",
            width=150,
            height=150,
            fit=ft.ImageFit.CONTAIN,
        )
        # Cria itens e carrossel
        items = self.build_review_items()
        logger.info("build_view: itens para carrossel gerados: %d", len(items))
        self.carousel = Carousel(items)
        # Atualiza os dados imediatamente
        self.update_review()
        actions = ft.Row(
            [
                ft.ElevatedButton("Voltar", on_click=self.on_previous),
                ft.ElevatedButton("Criar Perfil", on_click=self.on_create),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=12,
        )
        return ft.Column(
            [
                self.build_step_progress(),
                header,
                ft.Container(content=mascot, alignment=ft.alignment.center, padding=20),
                ft.Container(content=self.carousel, padding=10, width=380, height=260),
                actions,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=24,
        )

    def validate(self) -> bool:
        logger.info("Validate Step8Review chamada")
        return True

    def build_review_items(self) -> list[ft.Control]:
        data = self.profile_data
        logger.info("build_review_items: profile_data=%s", data)

        def get_val(key, suffix=""):
            v = data.get(key)
            logger.info("get_val: chave=%s, valor_bruto=%s", key, v)
            if v is None or v == "":
                return None
            return f"{v}{suffix}"

        raw = [
            ("Nome", get_val("name"), ft.Icons.PERSON),
            ("Idade", get_val("age", " anos"), ft.Icons.CALENDAR_TODAY),
            ("Gênero", get_val("gender"), ft.Icons.PEOPLE),
            ("Peso", get_val("weight", " kg"), ft.Icons.FITNESS_CENTER),
            ("Altura", get_val("height", " cm"), ft.Icons.HEIGHT),
            ("Objetivo", get_val("goal"), ft.Icons.STAR),
            ("Nível", get_val("level"), ft.Icons.FITNESS_CENTER),
            ("Restrições", get_val("restrictions"), ft.Icons.WARNING),
        ]
        items = []
        for label, val, icon in raw:
            display = (
                val
                if val
                else ("Nenhuma" if label == "Restrições" else "Não informado")
            )
            logger.info("raw item: %s -> %s => exibindo '%s'", label, val, display)
            items.append(ProfileItem(label, display, icon))
        return items

    def update_review(self):
        logger.info("update_review chamado, current_step=%d", self.current_step[0])
        if self.carousel and self.page and self.current_step[0] == 7:
            items = self.build_review_items()
            logger.info("update_review: re-gerando itens: %d", len(items))
            self.carousel.controls = items
            self.carousel.update()
            self.page.update()
            logger.info("Carrossel de revisão atualizado com dados atuais.")
