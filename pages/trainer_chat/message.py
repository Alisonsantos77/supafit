import flet as ft
from datetime import datetime


class Message:
    def __init__(
        self,
        user_name: str,
        text: str,
        user_type: str = "user",
        created_at: str = None,
        show_avatar: bool = False,
        gender: str = "neutro",
        user_id: str = None,
    ):
        self.user_name = user_name
        self.text = text
        self.user_type = user_type
        self.created_at = created_at
        self.show_avatar = show_avatar
        self.gender = gender
        self.user_id = user_id


class ChatMessage(ft.Container):
    def __init__(
        self, message: Message, page: ft.Page, haptic_feedback: ft.HapticFeedback = None
    ):
        super().__init__()
        self.message = message
        self.page = page
        self.haptic_feedback = haptic_feedback
        self.is_user = message.user_type == "user"

        # Criar avatar com fallback
        avatar = None
        if message.show_avatar:
            if self.is_user:
                avatar = self._create_user_avatar(message)
            else:
                avatar = self._create_trainer_avatar()

        self.time_str = self._format_timestamp(message.created_at)

        self.message_text_ref = ft.Ref[ft.Markdown]()
        self.time_display_ref = ft.Ref[ft.Text]()

        self.message_text = ft.Markdown(
            ref=self.message_text_ref,
            value=message.text,
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            on_tap_link=self._handle_link_tap,
            opacity=1,
            animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_IN),
        )
        self.opacity = 1
        self.offset = ft.Offset(0, 0)

        self.time_display = ft.Text(
            ref=self.time_display_ref,
            value=self.time_str,
            size=11,
            text_align=ft.TextAlign.RIGHT,
            weight=ft.FontWeight.W_400,
        )

        list_tile = ft.ListTile(
            leading=avatar,
            title=ft.Text(
                message.user_name,
                size=15,
                weight=ft.FontWeight.W_600,
            ),
            subtitle=ft.Column(
                [
                    self.message_text,
                    self.time_display,
                ],
                tight=True,
                spacing=6,
            ),
            content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
            dense=False,
            min_leading_width=40,
        )

        self.content = list_tile
        self.padding = ft.padding.symmetric(horizontal=4, vertical=2)
        self.border_radius = 12
        self.alignment = (
            ft.alignment.center_right if self.is_user else ft.alignment.center_left
        )

        window_width = 800  # Valor padrão
        if page.window and hasattr(page.window, "width") and page.window.width:
            window_width = page.window.width

        self.width = min(window_width * 0.85, 450)
        self.expand = True
        self.clip_behavior = ft.ClipBehavior.HARD_EDGE
        self.animate_opacity = ft.Animation(400, ft.AnimationCurve.EASE_OUT)
        self.animate_offset = ft.Animation(400, ft.AnimationCurve.EASE_OUT)
        self.offset = ft.Offset(0.2 if self.is_user else -0.2, 0)
        self.opacity = 0



    def _create_user_avatar(self, message: Message) -> ft.CircleAvatar:
        """Cria avatar do usuário usando a API thumbs da DiceBear"""
        seed = message.user_id or message.user_name or "anon"
        seed = "".join(c for c in str(seed) if c.isalnum() or c in "-_")[:36]
        
        avatar_url = f"https://api.dicebear.com/8.x/thumbs/png?seed={seed}"

        avatar = ft.CircleAvatar(
            foreground_image_src=avatar_url,
            content=ft.Text(
                message.user_name[:2].upper() if message.user_name else "AN",
                size=14,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.WHITE,
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor=ft.Colors.BLUE_600,
            radius=18,
            on_image_error=lambda e: print(f"ERROR: Falha ao carregar avatar: {e.data}"),
        )
        return avatar    
    
    def _create_trainer_avatar(self) -> ft.Container:
        """Cria avatar do treinador com fallback"""
        return ft.Container(
            content=ft.Image(
                src="mascote_supafit/coachito.png",
                width=36,
                height=36,
                fit=ft.ImageFit.COVER,
                error_content=ft.Container(
                    content=ft.Icon(
                        ft.Icons.FITNESS_CENTER,
                        size=24,
                        color=ft.Colors.WHITE,
                    ),
                    width=36,
                    height=36,
                    bgcolor=ft.Colors.BLUE_600,
                    border_radius=50,
                    alignment=ft.alignment.center,
                ),
            ),
            width=36,
            height=36,
            border_radius=50,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

    def _handle_link_tap(self, e):
        if self.haptic_feedback:
            self.haptic_feedback.light_impact()
        self.page.launch_url(e.data)

    def did_mount(self):
        self.opacity = 1
        self.offset = ft.Offset(0, 0)
        self.update()

    def _format_timestamp(self, created_at: str) -> str:
        """Formata timestamp com fuso horário local ou UTC"""
        if not created_at:
            return datetime.now().strftime("%H:%M")

        try:
            # diferentes formatos de data
            if created_at.endswith("Z"):
                # Formato ISO com Z (UTC)
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            elif "+" in created_at or created_at.endswith("00"):
                # Formato ISO com timezone
                dt = datetime.fromisoformat(created_at)
            else:
                # Formato ISO simples, assume UTC
                dt = datetime.fromisoformat(created_at)

            # Retorna hora formatada no fuso local
            return dt.strftime("%H:%M")

        except (ValueError, TypeError) as e:
            print(f"WARNING: Erro ao formatar timestamp '{created_at}': {e}")
            # Fallback para horário atual local
            return datetime.now().strftime("%H:%M")    
        
    def update_text(self, new_text: str):
        """Atualiza o texto da mensagem com verificações de segurança"""
        if not new_text:
            print("WARNING: Tentativa de atualizar com texto vazio")
            return

        try:
            if self.message_text_ref.current:
                self.message_text_ref.current.opacity = 0
                self.message_text_ref.current.value = new_text
                self.message.text = new_text
                self.message_text_ref.current.opacity = 1

            # Atualizar timestamp usando datetime
            self.message.created_at = datetime.now().isoformat()

            if self.time_display_ref.current:
                self.time_display_ref.current.value = self._format_timestamp(
                    self.message.created_at
                )

            if self.page:
                self.page.update()
        except Exception as e:
            print(f"ERROR: Falha ao atualizar texto da mensagem: {e}")