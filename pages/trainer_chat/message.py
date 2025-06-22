import flet as ft
from datetime import datetime
from components.components import AvatarComponent


class Message:
    def __init__(
        self,
        user_name: str,
        text: str,
        user_type: str = "user",
        created_at: str = None,
        show_avatar: bool = False,
    ):
        self.user_name = user_name
        self.text = text
        self.user_type = user_type
        self.created_at = created_at
        self.show_avatar = show_avatar


class ChatMessage(ft.Container):
    def __init__(self, message: Message, page: ft.Page):
        super().__init__()
        self.message = message
        self.page = page
        self.is_user = message.user_type == "user"

        # Avatar apenas para mensagem inicial do treinador
        avatar = (
            AvatarComponent(message.user_name, radius=16, is_trainer=not self.is_user)
            if message.show_avatar and not self.is_user
            else None
        )

        # Formata o timestamp
        self.time_str = self._format_timestamp(message.created_at)

        # Usa cores do tema
        cs = page.theme.color_scheme
        text_color = cs.on_surface
        time_color = ft.Colors.with_opacity(0.6, cs.on_surface)

        # Referências para controles dinâmicos
        self.message_text_ref = ft.Ref[ft.Markdown]()
        self.time_display_ref = ft.Ref[ft.Text]()


        self.message_text = ft.Markdown(
            ref=self.message_text_ref,
            value=message.text,
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            on_tap_link=lambda e: page.launch_url(e.data),
            opacity=1,  # Alterado de 0 para 1
            animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_IN),
        )
        self.opacity = 1  # Alterado de 0 para 1
        self.offset = ft.Offset(0, 0)  # Alterado de (0.2 if self.is_user else -0.2, 0)
        # Configura o timestamp
        self.time_display = ft.Text(
            ref=self.time_display_ref,
            value=self.time_str,
            size=10,
            color=time_color,
            text_align=ft.TextAlign.RIGHT,
        )

        # Configura o ListTile
        list_tile = ft.ListTile(
            leading=avatar,
            title=ft.Text(
                message.user_name,
                size=14,
                weight=ft.FontWeight.W_500,
                color=text_color,
            ),
            subtitle=ft.Column(
                [
                    self.message_text,
                    self.time_display,
                ],
                tight=True,
                spacing=4,
            ),
            bgcolor=(
                ft.Colors.with_opacity(0.05, cs.on_surface) if self.is_user else None
            ),
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            dense=True,
            min_leading_width=32,
        )

        # Configurações do Container
        self.content = list_tile
        self.padding = ft.padding.symmetric(horizontal=8, vertical=4)
        self.border_radius = 16
        self.alignment = (
            ft.alignment.center_right if self.is_user else ft.alignment.center_left
        )
        self.width = min(page.window.width * 0.75, 400)
        self.expand = True
        self.clip_behavior = ft.ClipBehavior.HARD_EDGE
        self.animate_opacity = ft.Animation(400, ft.AnimationCurve.EASE_OUT)
        self.animate_offset = ft.Animation(400, ft.AnimationCurve.EASE_OUT)
        self.offset = ft.Offset(0.2 if self.is_user else -0.2, 0)
        self.opacity = 0

    def did_mount(self):
        """Aplica fade-in e deslize ao montar."""
        self.opacity = 1
        self.offset = self.offset = ft.Offset(0, 0)
        self.update()

    def _format_timestamp(self, created_at: str) -> str:
        """Formata o timestamp para exibição."""
        if created_at:
            try:
                return datetime.fromisoformat(
                    created_at.replace("Z", "+00:00")
                ).strftime("%H:%M")
            except:
                pass
        return "Horário desconhecido"

    def update_text(self, new_text: str):
        """Atualiza o texto com efeito de fade-in."""
        self.message_text_ref.current.opacity = 0
        self.message_text_ref.current.value = new_text
        self.message.text = new_text
        self.message_text_ref.current.opacity = 1
        self.message.created_at = datetime.now().isoformat()
        self.time_display_ref.current.value = self._format_timestamp(
            self.message.created_at
        )
        self.page.update()
