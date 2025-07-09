import flet as ft
import time
from .step_personal_data import StepPersonalData
from .step_physical_data import StepPhysicalData
from .step_goal_restrictions import StepGoalRestrictions
from .step_review import StepReview
from utils.logger import get_logger
from services.workout_generator import (
    WorkoutGenerator,
    generate_and_store_workout,
    save_workout_to_database,
)
import os
from dotenv import load_dotenv

load_dotenv()
logger = get_logger("supafit.profile_user.create_profile")


def CreateProfilePage(page: ft.Page, supabase_service):
    groq_api_key = os.getenv("GROQ_API_KEY")
    last_event_time = [0]
    current_step = [0]
    profile_data = {}

    def show_loading(message="Carregando..."):
        if hasattr(page, "dialog") and page.dialog and page.dialog.open:
            logger.info("Diálogo de carregamento já exibido, ignorando")
            return page.dialog

        loading_dialog = ft.AlertDialog(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.ProgressRing(color=ft.Colors.BLUE_400),
                        ft.Text(message, size=16, text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                width=200,
                height=100,
            ),
            bgcolor=ft.Colors.TRANSPARENT,
            modal=True,
            disabled=True,
        )
        page.dialog = loading_dialog
        page.open(loading_dialog)
        logger.info(f"Diálogo de carregamento exibido: {message}")
        return loading_dialog

    def hide_loading(dialog):
        if dialog and dialog.open:
            page.close(dialog)
            page.dialog = None
            logger.info("Diálogo de carregamento fechado")

    def reset_form():
        logger.info(f"Antes de resetar profile_data: {profile_data}")
        profile_data.clear()
        current_step[0] = 0
        for step in steps:
            # limpa inputs e erros de cada etapa
            for attr in (
                "name_input",
                "weight_input",
                "height_input",
                "restrictions_input",
            ):
                control = getattr(step, attr, None)
                if control:
                    control.value = ""
                    control.error_text = None
            # reset sliders e dropdowns
            if hasattr(step, "weight_slider"):
                step.weight_slider.value = 70
            if hasattr(step, "height_slider"):
                step.height_slider.value = 170
            if hasattr(step, "goal_dropdown"):
                step.goal_dropdown.value = "Manter forma física"
            if hasattr(step, "gender_dropdown"):
                step.gender_dropdown.value = "Masculino"
        update_view()
        logger.info("Formulário de perfil reiniciado.")

    async def next_step(e):
        nonlocal last_event_time
        current_time = time.time()
        if current_time - last_event_time[0] < 0.5:
            logger.info("Debounce: Evento ignorado por 500ms")
            return
        last_event_time[0] = current_time
        logger.info(
            f"Tentando avançar da etapa {current_step[0]}, profile_data: {profile_data}"
        )
        valid = await steps[current_step[0]].validate()
        logger.info(
            f"Resultado da validação da etapa {current_step[0]}: {valid} | profile_data agora: {profile_data}"
        )
        if valid:
            current_step[0] += 1
            update_view()
            logger.info(
                f"Avançou para a etapa {current_step[0]}, profile_data: {profile_data}"
            )
        else:
            logger.warning("Validação falhou na etapa atual.")

    def previous_step(e, step=None):
        nonlocal last_event_time
        current_time = time.time()
        if current_time - last_event_time[0] < 0.5:
            logger.info("Debounce: Evento ignorado por 500ms")
            return
        last_event_time[0] = current_time
        if step is not None:
            current_step[0] = step
        elif current_step[0] > 0:
            current_step[0] -= 1
        update_view()
        logger.info(
            f"Retrocedeu para a etapa {current_step[0]}, profile_data: {profile_data}"
        )

    def generate_workout_plan():
        """Gera o plano de treino baseado nos dados coletados - VERSÃO SÍNCRONA"""
        try:
            if not groq_api_key:
                logger.error("Chave API Groq não encontrada")
                return False

            # Preparar dados do usuário para geração do treino
            user_data = {
                "name": profile_data.get("name", "Usuário"),
                "age": profile_data.get("age", 25),
                "weight": profile_data.get("weight", 70.0),
                "height": profile_data.get("height", 170),
                "goal": profile_data.get("goal", "Manter forma física"),
                "gender": profile_data.get("gender", "Masculino"),
                "restrictions": profile_data.get("restrictions", "Nenhuma"),
                "level": page.client_storage.get("supafit.level") or "iniciante",
            }

            logger.info(f"Gerando treino para usuário: {user_data}")

            # Gerar e armazenar treino temporariamente
            success = generate_and_store_workout(
                page, supabase_service, user_data, groq_api_key
            )

            if success:
                logger.info("Treino gerado e armazenado temporariamente com sucesso")
                return True
            else:
                logger.error("Falha ao gerar treino")
                return False

        except Exception as e:
            logger.error(f"Erro ao gerar plano de treino: {str(e)}")
            return False

    def create_profile(e):
        nonlocal last_event_time
        current_time = time.time()
        if current_time - last_event_time[0] < 0.5:
            logger.info("Debounce: Evento ignorado por 500ms")
            return
        last_event_time[0] = current_time

        logger.info(f"Iniciando criação de perfil com dados: {profile_data}")
        user_id = page.client_storage.get("supafit.user_id")
        level = page.client_storage.get("supafit.level") or "iniciante"
        if not user_id:
            logger.error("user_id não encontrado no armazenamento do cliente.")
            page.open(
                ft.SnackBar(
                    content=ft.Text(
                        "Erro: usuário não autenticado.", color=ft.Colors.WHITE
                    ),
                    bgcolor=ft.Colors.RED_600,
                    duration=3000,
                )
            )
            return

        # Preparar dados completos do perfil
        profile_data.update(
            {
                "user_id": user_id,
                "name": profile_data.get("name", "Usuário Desconhecido"),
                "age": profile_data.get("age", 18),
                "weight": float(profile_data.get("weight", "70.0")),
                "height": profile_data.get("height", 170),
                "goal": profile_data.get("goal", "Manter forma física"),
                "terms_accepted": profile_data.get("terms_accepted", True),
                "level": level,
                "first_workout": profile_data.get("first_workout", True),
                "rest_duration": 60,
                "theme": "dark",
                "primary_color": "BLUE",
                "font_family": "Barlow",
                "gender": profile_data.get("gender", "Masculino"),
                "restrictions": profile_data.get("restrictions", "Nenhuma"),
            }
        )

        # Etapa 1: Gerar plano de treino
        loading_dialog = show_loading("Gerando seu plano de treino personalizado...")
        page.update()

        try:
            workout_generated = generate_workout_plan()

            if not workout_generated:
                hide_loading(loading_dialog)
                page.open(
                    ft.SnackBar(
                        content=ft.Text(
                            "Erro ao gerar plano de treino. Tente novamente.",
                            color=ft.Colors.WHITE,
                        ),
                        bgcolor=ft.Colors.RED_600,
                        duration=3000,
                    )
                )
                return

            # Etapa 2: Criar perfil no banco
            hide_loading(loading_dialog)
            loading_dialog = show_loading("Criando seu perfil...")
            page.update()

            supabase_service.create_profile(user_id, profile_data)
            page.client_storage.set("supafit.profile_created", True)
            logger.info(f"Perfil criado para user_id: {user_id}")

            # Etapa 3: Salvar treino no banco
            hide_loading(loading_dialog)
            loading_dialog = show_loading("Salvando seu plano de treino...")
            page.update()

            workout_saved = save_workout_to_database(
                page, supabase_service, user_id
            )

            if not workout_saved:
                logger.warning("Perfil criado, mas falha ao salvar treino")
                hide_loading(loading_dialog)
                page.open(
                    ft.SnackBar(
                        content=ft.Text(
                            "Perfil criado, mas erro ao salvar treino. Você pode gerar um novo treino depois.",
                            color=ft.Colors.WHITE,
                        ),
                        bgcolor=ft.Colors.ORANGE_600,
                        duration=4000,
                    )
                )
            else:
                logger.info(f"Treino salvo no banco para user_id: {user_id}")
                hide_loading(loading_dialog)
                page.open(
                    ft.SnackBar(
                        content=ft.Text(
                            "Perfil e plano de treino criados com sucesso!",
                            color=ft.Colors.WHITE,
                        ),
                        bgcolor=ft.Colors.GREEN_600,
                        duration=3000,
                    )
                )

            # Finalizar processo
            reset_form()
            page.go("/home")
            page.update()

        except Exception as ex:
            hide_loading(loading_dialog)
            page.open(
                ft.SnackBar(
                    content=ft.Text(
                        "Erro ao criar perfil. Tente novamente mais tarde.",
                        color=ft.Colors.WHITE,
                    ),
                    bgcolor=ft.Colors.RED_600,
                    duration=3000,
                )
            )
            logger.error(f"Erro ao criar perfil: {ex}")
            page.update()

    def update_view():
        for idx, step in enumerate(steps):
            step.view.visible = idx == current_step[0]
            if isinstance(step, StepReview) and step.view.visible:
                step.update_review_data()
        page.update()
        logger.info(f"View atualizada para a etapa {current_step[0]}")

    steps = [
        StepPersonalData(page, profile_data, current_step, next_step, previous_step),
        StepPhysicalData(page, profile_data, current_step, next_step, previous_step),
        StepGoalRestrictions(
            page, profile_data, current_step, next_step, previous_step
        ),
        StepReview(
            page,
            profile_data,
            current_step,
            next_step,
            previous_step,
            supabase_service,
            create_profile,  # Agora é uma função async
        ),
    ]

    container_steps = ft.Container(
        content=ft.Column(
            [step.view for step in steps],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
        animate=ft.Animation(500, ft.AnimationCurve.EASE_IN_OUT),
    )

    update_view()
    return container_steps
