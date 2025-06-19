import flet as ft
from datetime import datetime
from components.components import AvatarComponent


class Message:
    def __init__(
        self, user_name: str, text: str, user_type: str = "user", created_at: str = None
    ):
        self.user_name = user_name
        self.text = text
        self.user_type = user_type
        self.created_at = created_at


class ChatMessage(ft.Container):
    def __init__(self, message: Message, page: ft.Page):
        super().__init__()
        self.message = message
        self.page = page

        # Determina se é mensagem do treinador
        is_trainer = message.user_type == "trainer"
        avatar = AvatarComponent(message.user_name, radius=20, is_trainer=is_trainer)

        # Formata o timestamp inicial
        self.time_str = self._format_timestamp(message.created_at)

        # Usa cores do tema da página
        cs = page.theme.color_scheme
        bgcolor = cs.primary if is_trainer else cs.secondary
        text_color = cs.on_primary if is_trainer else cs.on_secondary
        time_color = ft.Colors.WHITE54

        # Referências para controles dinâmicos
        self.message_text_ref = ft.Ref[ft.Markdown]()
        self.time_display_ref = ft.Ref[ft.Text]()

        # Configura o Markdown para o texto da mensagem
        self.message_text = ft.Markdown(
            ref=self.message_text_ref,
            value=message.text,
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            on_tap_link=lambda e: page.launch_url(e.data),
            opacity=0,  # Inicia invisível para fade-in
            animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_IN),
        )

        # Configura o Text para o timestamp
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
                weight=ft.FontWeight.BOLD,
                color=text_color,
            ),
            subtitle=ft.Column(
                [
                    self.message_text,
                    self.time_display,
                ],
                tight=True,
                spacing=5,
            ),
            bgcolor=bgcolor,
            content_padding=ft.padding.symmetric(horizontal=10, vertical=5),
            dense=False,
            min_leading_width=40,
        )

        # Configurações do Container
        self.content = list_tile
        self.padding = ft.padding.symmetric(horizontal=10, vertical=5)
        self.border_radius = 10
        self.alignment = (
            ft.alignment.center_left if is_trainer else ft.alignment.center_right
        )
        self.width = min(page.window.width * 0.7, 400)
        self.expand = True
        self.clip_behavior = ft.ClipBehavior.HARD_EDGE
        self.shadow = ft.BoxShadow(blur_radius=1, offset=ft.Offset(0, 2))

    def did_mount(self):
        """Chamado quando o controle é montado na página."""
        # Aplica o efeito de fade-in inicial
        self.message_text_ref.current.opacity = 1
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
        """Atualiza o texto da mensagem dinamicamente com efeito de fade-in."""
        # Atualiza o texto com efeito de fade
        self.message_text_ref.current.opacity = 0  # Torna invisível antes de atualizar
        self.message_text_ref.current.value = new_text
        self.message.text = new_text  # Atualiza o texto no objeto Message
        self.message_text_ref.current.opacity = 1  # Fade-in para o novo texto

        # Atualiza o timestamp
        self.message.created_at = datetime.now().isoformat()
        self.time_display_ref.current.value = self._format_timestamp(
            self.message.created_at
        )

        # Atualiza a UI
        self.page.update()
