import flet as ft
import logging
import time
from .step1_name import Step1Name
from .step2_age import Step2Age
from .step3_weight import Step3Weight
from .step4_height import Step4Height
from .step5_goal import Step5Goal
from .step6_review import Step6Review

logger = logging.getLogger("supafit.profile_user.create_profile")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def CreateProfilePage(page: ft.Page, supabase_service):
    """Página principal para criação de perfil do usuário.

    Orquestra as etapas de criação de perfil, gerenciando navegação e dados.

    Args:
        page (ft.Page): Página Flet para interação com o usuário.
        supabase_service: Serviço Supabase para operações de banco de dados.

    Returns:
        ft.Container: Contêiner com as etapas do formulário.
    """
    last_event_time = [0]  # Para debounce
    current_step = [0]  # Rastrear etapa atual
    profile_data = {}  # Armazenar dados do perfil

    def show_loading():
        """Exibe um diálogo de carregamento."""
        if hasattr(page, "dialog") and page.dialog and page.dialog.open:
            logger.info("Diálogo de carregamento já exibido, ignorando")
            return page.dialog
        loading_dialog = ft.AlertDialog(
            content=ft.Container(
                content=ft.ProgressRing(color=ft.Colors.BLUE_400),
                alignment=ft.alignment.center,
            ),
            bgcolor=ft.Colors.TRANSPARENT,
            modal=True,
            disabled=True,
        )
        page.dialog = loading_dialog
        page.open(loading_dialog)
        logger.info("Diálogo de carregamento exibido")
        return loading_dialog

    def hide_loading(dialog):
        """Fecha o diálogo de carregamento."""
        if dialog and dialog.open:
            page.close(dialog)
            page.dialog = None
            logger.info("Diálogo de carregamento fechado")

    def show_snackbar(message: str, color: str = ft.Colors.RED):
        """Exibe uma SnackBar com feedback para o usuário.

        Args:
            message (str): Mensagem a ser exibida.
            color (str): Cor da SnackBar (padrão: vermelho para erros).
        """
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=color,
            duration=3000,
        )
        page.snack_bar.open = True
        page.update()
        logger.info(f"SnackBar exibida: {message}")

    def reset_form():
        """Reinicia o formulário e os dados do perfil."""
        profile_data.clear()
        current_step[0] = 0
        for step in steps:
            if hasattr(step, "name_input") and step.name_input:
                step.name_input.value = ""
                step.name_input.error_text = None
            if hasattr(step, "age_input") and step.age_input:
                step.age_input.value = ""
                step.age_input.error_text = None
            if hasattr(step, "weight_input") and step.weight_input:
                step.weight_input.value = ""
                step.weight_input.error_text = None
            if hasattr(step, "height_input") and step.height_input:
                step.height_input.value = ""
                step.height_input.error_text = None
            if hasattr(step, "goal_radio_group") and step.goal_radio_group:
                step.goal_radio_group.value = "Manter forma"
            if hasattr(step, "review_text") and step.review_text:
                step.review_text.value = ""
        update_view()
        logger.info("Formulário de perfil reiniciado.")

    def next_step(e):
        """Avança para a próxima etapa se a validação passar."""
        nonlocal last_event_time
        current_time = time.time()
        if current_time - last_event_time[0] < 0.5:
            logger.info("Debounce: Evento ignorado por 500ms")
            return
        last_event_time[0] = current_time
        logger.info(f"Tentando avançar da etapa {current_step[0]}")
        if steps[current_step[0]].validate():
            current_step[0] += 1
            if current_step[0] == 5:  # Revisão
                steps[5].update_review()
            update_view()
            logger.info(f"Avançou para a etapa {current_step[0]}")
        else:
            logger.warning("Validação falhou na etapa atual.")

    def previous_step(e):
        """Volta para a etapa anterior."""
        nonlocal last_event_time
        current_time = time.time()
        if current_time - last_event_time[0] < 0.5:
            logger.info("Debounce: Evento ignorado por 500ms")
            return
        last_event_time[0] = current_time
        logger.info(f"Tentando voltar da etapa {current_step[0]}")
        if current_step[0] > 0:
            current_step[0] -= 1
            update_view()
            logger.info(f"Retrocedeu para a etapa {current_step[0]}")

    def create_profile(e):
        """Cria o perfil do usuário no Supabase."""
        nonlocal last_event_time
        current_time = time.time()
        if current_time - last_event_time[0] < 0.5:
            logger.info("Debounce: Evento ignorado por 500ms")
            return
        last_event_time[0] = current_time
        logger.info("Enviando dados do perfil...")
        user_id = page.client_storage.get("supafit.user_id")
        level = page.client_storage.get("supafit.level")

        if not user_id:
            logger.warning("Tentativa de criar perfil sem user_id")
            show_snackbar("Erro: Usuário não autenticado.", ft.Colors.RED)
            page.go("/login")
            return

        profile_data["user_id"] = user_id
        profile_data["level"] = level if level else "iniciante"
        profile_data["terms_accepted"] = True
        profile_data["first_workout"] = False

        loading_dialog = show_loading()
        page.update()

        try:
            supabase_service.create_profile(user_id, profile_data)
            page.client_storage.set("supafit.profile_created", True)
            hide_loading(loading_dialog)
            show_snackbar("Perfil criado com sucesso!", ft.Colors.GREEN_400)
            logger.info(f"Perfil criado para user_id: {user_id}")
            reset_form()
            page.go("/home")
            page.update()
        except Exception as ex:
            hide_loading(loading_dialog)
            show_snackbar(f"Erro ao criar perfil: {str(ex)}", ft.Colors.RED)
            logger.error(f"Erro ao criar perfil: {str(ex)}")
            page.update()

    def update_view():
        """Atualiza a visibilidade das etapas."""
        for index, step in enumerate(steps):
            step.view.visible = index == current_step[0]
            # Atualizar revisão apenas quando a etapa 5 for visível
            if index == 5 and step.view.visible:
                step.update_review()
        page.update()
        logger.info(f"View atualizada para a etapa {current_step[0]}")

    # Instancia as etapas com tratamento de erros
    steps = []
    try:
        steps.append(
            Step1Name(page, profile_data, current_step, next_step, previous_step)
        )
        steps.append(
            Step2Age(page, profile_data, current_step, next_step, previous_step)
        )
        steps.append(
            Step3Weight(page, profile_data, current_step, next_step, previous_step)
        )
        steps.append(
            Step4Height(page, profile_data, current_step, next_step, previous_step)
        )
        steps.append(
            Step5Goal(page, profile_data, current_step, next_step, previous_step)
        )
        steps.append(
            Step6Review(
                page,
                profile_data,
                current_step,
                next_step,
                previous_step,
                supabase_service,
                create_profile,
            )
        )
    except Exception as e:
        logger.error(f"Erro ao inicializar etapas: {str(e)}")
        show_snackbar(
            "Erro ao carregar formulário de perfil. Tente novamente mais tarde.",
            ft.Colors.RED,
        )
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Erro ao carregar o formulário",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED,
                    ),
                    ft.Text("Por favor, tente novamente ou faça login novamente."),
                    ft.ElevatedButton(
                        "Voltar para Login", on_click=lambda _: page.go("/login")
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
        )

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
