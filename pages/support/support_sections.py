import flet as ft
from .support_components import (
    AnimatedCard,
    BuddyAvatar,
    PixKeyCard,
    StoryCard,
)


class SupportSections:
    @staticmethod
    def create_hero_section(buddy_avatar, animate_buddy_click):
        return AnimatedCard(
            content=ft.Column(
                [
                    ft.GestureDetector(
                        content=buddy_avatar,
                        on_tap=animate_buddy_click,
                    ),
                    ft.Text(
                        "Olá! Sou Alison, desenvolvedor do SupaFit",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Um sonho que precisa do seu apoio para crescer 🌱",
                        size=16,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(
                        content=ft.Text(
                            "💡 Toque em mim para me animar! 😊",
                            size=12,
                            text_align=ft.TextAlign.CENTER,
                            style=ft.TextStyle(italic=True),
                        ),
                        padding=10,
                        border_radius=12,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
            ),
        )

    @staticmethod
    def create_story_section():
        stories = [
            {
                "icon": "🏠",
                "title": "Projeto Pessoal",
                "description": "Desenvolvido em casa, com muito café e dedicação",
            },
            {
                "icon": "⏰",
                "title": "Noites e Fins de Semana",
                "description": "Cada linha de código feita no tempo livre",
            },
            {
                "icon": "💡",
                "title": "Uma Ideia, Um Sonho",
                "description": "Ajudar pessoas na jornada fitness de forma gratuita",
            },
            {
                "icon": "🤝",
                "title": "Sua Participação",
                "description": "Com seu apoio, posso dedicar mais tempo ao projeto",
            },
        ]

        return AnimatedCard(
            content=ft.Column(
                [
                    ft.Text(
                        "📖 A História do SupaFit",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Cada contribuição me permite investir mais tempo neste sonho",
                        size=14,
                        text_align=ft.TextAlign.CENTER,
                        style=ft.TextStyle(italic=True),
                    ),
                    ft.Column(
                        [
                            StoryCard(
                                story["icon"],
                                story["title"],
                                story["description"],
                                delay=i * 0.2,
                            )
                            for i, story in enumerate(stories)
                        ],
                        spacing=12,
                    ),
                ],
                spacing=20,
            ),
        )

    @staticmethod
    def create_pix_section(pix_key, copy_pix_key, pix_card_ref=None):
        pix_card = PixKeyCard(pix_key, copy_pix_key)
        if pix_card_ref:
            pix_card_ref.append(pix_card)

        return AnimatedCard(
            content=ft.Column(
                [
                    ft.Text(
                        "💝 Faça Parte Desta Jornada",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Qualquer valor faz diferença para um desenvolvedor independente",
                        size=15,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    pix_card,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            ),
        )

    @staticmethod
    def create_impact_section():
        return AnimatedCard(
            content=ft.Column(
                [
                    ft.Text(
                        "🎯 Seu Impacto No Projeto",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Container(
                                        content=ft.Text("☕", size=24),
                                        width=50,
                                        height=50,
                                        border_radius=25,
                                        alignment=ft.alignment.center,
                                    ),
                                    ft.Text(
                                        "Um Café",
                                        size=12,
                                        weight=ft.FontWeight.W_600,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.Text(
                                        "Energia para\nmais código",
                                        size=10,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=6,
                            ),
                            ft.Column(
                                [
                                    ft.Container(
                                        content=ft.Text("🖥️", size=24),
                                        width=50,
                                        height=50,
                                        border_radius=25,
                                        alignment=ft.alignment.center,
                                    ),
                                    ft.Text(
                                        "Servidor",
                                        size=12,
                                        weight=ft.FontWeight.W_600,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.Text(
                                        "Mantem o app\nno ar",
                                        size=10,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=6,
                            ),
                            ft.Column(
                                [
                                    ft.Container(
                                        content=ft.Text("🚀", size=24),
                                        width=50,
                                        height=50,
                                        border_radius=25,
                                        alignment=ft.alignment.center,
                                    ),
                                    ft.Text(
                                        "Evolução",
                                        size=12,
                                        weight=ft.FontWeight.W_600,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.Text(
                                        "Novas\nfuncionalidades",
                                        size=10,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=6,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    ),
                ],
                spacing=20,
            ),
        )

    @staticmethod
    def create_gratitude_section():
        return AnimatedCard(
            content=ft.Column(
                [
                    ft.Text(
                        "🙏 Gratidão Infinita",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Cada PIX recebido é um voto de confiança no meu trabalho.\n"
                        "Prometo usar cada centavo para tornar o SupaFit ainda melhor!",
                        size=14,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(
                                            ft.Icons.SECURITY,
                                            color=ft.Colors.GREEN,
                                            size=20,
                                        ),
                                        ft.Text(
                                            "100% Seguro",
                                            size=12,
                                            color=ft.Colors.GREEN,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=8,
                                ),
                                ft.Row(
                                    [
                                        ft.Icon(
                                            ft.Icons.FLASH_ON,
                                            color=ft.Colors.ORANGE,
                                            size=20,
                                        ),
                                        ft.Text(
                                            "PIX Instantâneo",
                                            size=12,
                                            color=ft.Colors.ORANGE,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=8,
                                ),
                                ft.Row(
                                    [
                                        ft.Icon(
                                            ft.Icons.FAVORITE,
                                            color=ft.Colors.RED,
                                            size=20,
                                        ),
                                        ft.Text(
                                            "Feito com Amor",
                                            size=12,
                                            color=ft.Colors.RED,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=8,
                                ),
                            ],
                            spacing=8,
                        ),
                        padding=16,
                        border_radius=12,
                    ),
                    ft.Text(
                        "💪 SupaFit - Desenvolvido com paixão, alimentado por sonhos!",
                        size=12,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        weight=ft.FontWeight.BOLD,
                        style=ft.TextStyle(italic=True),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
            ),
        )
