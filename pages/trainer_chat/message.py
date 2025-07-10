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

        # Criar avatar com fallback robusto
        avatar = None
        if message.show_avatar:
            if self.is_user:
                avatar = self._create_user_avatar(message)
            else:
                avatar = self._create_trainer_avatar()

        self.time_str = self._format_timestamp(message.created_at)

        cs = page.theme.color_scheme
        text_color = cs.on_surface
        time_color = ft.Colors.with_opacity(0.7, cs.on_surface)

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
            color=time_color,
            text_align=ft.TextAlign.RIGHT,
            weight=ft.FontWeight.W_400,
        )

        list_tile = ft.ListTile(
            leading=avatar,
            title=ft.Text(
                message.user_name,
                size=15,
                weight=ft.FontWeight.W_600,
                color=text_color,
            ),
            subtitle=ft.Column(
                [
                    self.message_text,
                    self.time_display,
                ],
                tight=True,
                spacing=6,
            ),
            bgcolor=(
                ft.Colors.with_opacity(0.04, cs.on_surface) if self.is_user else None
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
        self.width = min(page.window.width * 0.85, 450)
        self.expand = True
        self.clip_behavior = ft.ClipBehavior.HARD_EDGE
        self.animate_opacity = ft.Animation(400, ft.AnimationCurve.EASE_OUT)
        self.animate_offset = ft.Animation(400, ft.AnimationCurve.EASE_OUT)
        self.offset = ft.Offset(0.2 if self.is_user else -0.2, 0)
        self.opacity = 0

    def _create_user_avatar(self, message: Message) -> ft.Container:
        """Cria avatar do usuário com múltiplas opções de fallback"""
        gender = (message.gender or "neutro").lower()
        seed = message.user_id or message.user_name or "anon"

        # Sanitizar o seed para URL
        seed = "".join(c for c in str(seed) if c.isalnum() or c in "-_")[:20]

        # Definir estilo baseado no gênero
        if gender == "masculino":
            style = "adventurer"
        elif gender == "feminino":
            style = "avataaars"
        else:
            style = "identicon"

        # URL principal da DiceBear (atualizada para v8)
        primary_url = f"https://api.dicebear.com/8.x/{style}/svg?seed={seed}"

        # Debug: imprimir URL gerada
        print(f"DEBUG: Avatar URL gerada: {primary_url}")
        print(f"DEBUG: Seed: {seed}, Gender: {gender}, Style: {style}")

        # Criar avatar com fallback robusto
        avatar_image = ft.Image(
            src=primary_url,
            width=36,
            height=36,
            fit=ft.ImageFit.COVER,
            error_content=ft.Container(
                content=ft.Text(
                    self._get_initials(message.user_name),
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                    text_align=ft.TextAlign.CENTER,
                ),
                width=36,
                height=36,
                bgcolor=self._get_avatar_color(seed),
                border_radius=50,
                alignment=ft.alignment.center,
            ),
        )

        # Container principal do avatar
        avatar_container = ft.Container(
            content=avatar_image,
            width=36,
            height=36,
            border_radius=50,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

        return avatar_container

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

    def _get_avatar_color(self, seed: str) -> str:
        """Gera cor consistente baseada no seed"""
        colors = [
            ft.Colors.BLUE_600,
            ft.Colors.GREEN_600,
            ft.Colors.PURPLE_600,
            ft.Colors.ORANGE_600,
            ft.Colors.RED_600,
            ft.Colors.TEAL_600,
            ft.Colors.INDIGO_600,
            ft.Colors.PINK_600,
        ]
        # Usar hash do seed para selecionar cor consistente
        hash_value = hash(str(seed)) % len(colors)
        return colors[hash_value]

    def _get_initials(self, name: str) -> str:
        """Extrai iniciais do nome"""
        if not name:
            return "?"

        # Remover espaços extras e dividir por espaços
        parts = name.strip().split()

        if len(parts) == 1:
            # Uma palavra: primeira letra
            return parts[0][0].upper()
        elif len(parts) >= 2:
            # Duas ou mais palavras: primeira letra de cada
            return (parts[0][0] + parts[1][0]).upper()
        else:
            return "?"

    def _handle_link_tap(self, e):
        if self.haptic_feedback:
            self.haptic_feedback.light_impact()
        self.page.launch_url(e.data)

    def did_mount(self):
        self.opacity = 1
        self.offset = ft.Offset(0, 0)
        self.update()

    def _format_timestamp(self, created_at: str) -> str:
        if created_at:
            try:
                return datetime.fromisoformat(
                    created_at.replace("Z", "+00:00")
                ).strftime("%H:%M")
            except:
                pass
        return "Horário desconhecido"

    def update_text(self, new_text: str):
        self.message_text_ref.current.opacity = 0
        self.message_text_ref.current.value = new_text
        self.message.text = new_text
        self.message_text_ref.current.opacity = 1
        self.message.created_at = datetime.now().isoformat()
        self.time_display_ref.current.value = self._format_timestamp(
            self.message.created_at
        )
        self.page.update()
