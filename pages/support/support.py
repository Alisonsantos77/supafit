import flet as ft
import logging
import asyncio
import threading
from .support_components import (
    AnimatedCard,
    BuddyAvatar,
    PixKeyCard,
    AnimatedSnackBar,
)
from .support_handlers import SupportHandlers
from .support_sections import SupportSections

logger = logging.getLogger("supafit.support")


def SupportPageView(page: ft.Page, supabase, openai=None):
    pix_key = "alisondev77@hotmail.com"

    buddy_avatar = BuddyAvatar()
    pix_card_ref = []

    handlers = SupportHandlers(page, pix_key, buddy_avatar)

    buddy_avatar.on_click = handlers.animate_buddy_click

    hero_section = SupportSections.create_hero_section(
        buddy_avatar, handlers.animate_buddy_click
    )

    story_section = SupportSections.create_story_section()

    pix_section = SupportSections.create_pix_section(
        pix_key, handlers.copy_pix_key, pix_card_ref
    )

    if pix_card_ref:
        handlers.pix_card = pix_card_ref[0]

    impact_section = SupportSections.create_impact_section()

    gratitude_section = SupportSections.create_gratitude_section()

    main_content = ft.Column(
        [
            hero_section,
            story_section,
            pix_section,
            impact_section,
            gratitude_section,
        ],
        spacing=24,
        scroll=ft.ScrollMode.AUTO,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    def show_welcome_safely():
        try:

            def delayed_welcome():
                try:
                    handlers.show_welcome_message()
                except Exception as e:
                    logger.error(f"Erro ao mostrar boas-vindas: {e}")

            timer = threading.Timer(0.8, delayed_welcome)
            timer.start()

        except Exception as e:
            logger.error(f"Erro ao configurar boas-vindas: {e}")

    show_welcome_safely()

    return ft.Container(
        content=main_content,
        padding=20,
        expand=True,
    )


def SupportPageViewAlternative(page: ft.Page, supabase, openai=None):
    pix_key = "alisondev77@hotmail.com"

    buddy_avatar = BuddyAvatar()
    pix_card_ref = []

    handlers = SupportHandlers(page, pix_key, buddy_avatar)

    buddy_avatar.on_click = handlers.animate_buddy_click

    sections = SupportSections()

    hero_section = sections.create_hero_section(
        buddy_avatar, handlers.animate_buddy_click
    )
    story_section = sections.create_story_section()
    pix_section = sections.create_pix_section(
        pix_key, handlers.copy_pix_key, pix_card_ref
    )

    if pix_card_ref:
        handlers.pix_card = pix_card_ref[0]

    impact_section = sections.create_impact_section()
    gratitude_section = sections.create_gratitude_section()

    main_content = ft.Column(
        [
            hero_section,
            story_section,
            pix_section,
            impact_section,
            gratitude_section,
        ],
        spacing=24,
        scroll=ft.ScrollMode.AUTO,
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    container = ft.Container(
        content=main_content,
        padding=20,
        expand=True,
    )

    def on_page_ready():
        try:
            page.run_task(delayed_welcome_async)
        except:
            try:
                handlers.show_welcome_message()
            except Exception as e:
                logger.error(f"Erro ao mostrar boas-vindas: {e}")

    async def delayed_welcome_async():
        try:
            await asyncio.sleep(0.8)
            handlers.show_welcome_message()
        except Exception as e:
            logger.error(f"Erro em boas-vindas assíncronas: {e}")

    def on_container_mount():
        page.run_thread(lambda: page.after(800, on_page_ready))

    try:
        on_container_mount()
    except:
        pass

    return container
