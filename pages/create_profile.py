import flet as ft
import logging
import time

logger = logging.getLogger("supafit.create_profile")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def CreateProfilePage(page: ft.Page, supabase_service):
    last_event_time = 0  # Para debounce
    current_step = [0]  # Rastrear etapa atual
    profile_data = {}  # Armazenar dados do perfil

    name_input = ft.TextField(
        label="Nome",
        width=320,
        border="underline",
        filled=True,
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE_GREY),
        border_color=ft.Colors.BLUE_600,
        focused_border_color=ft.Colors.BLUE_400,
        cursor_color=ft.Colors.BLUE_400,
        text_size=16,
    )
    age_input = ft.TextField(
        label="Idade",
        width=320,
        border="underline",
        filled=True,
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE_GREY),
        border_color=ft.Colors.BLUE_600,
        focused_border_color=ft.Colors.BLUE_400,
        cursor_color=ft.Colors.BLUE_400,
        text_size=16,
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    weight_input = ft.TextField(
        label="Peso (kg)",
        width=320,
        border="underline",
        filled=True,
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE_GREY),
        border_color=ft.Colors.BLUE_600,
        focused_border_color=ft.Colors.BLUE_400,
        cursor_color=ft.Colors.BLUE_400,
        text_size=16,
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    height_input = ft.TextField(
        label="Altura (cm)",
        width=320,
        border="underline",
        filled=True,
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE_GREY),
        border_color=ft.Colors.BLUE_600,
        focused_border_color=ft.Colors.BLUE_400,
        cursor_color=ft.Colors.BLUE_400,
        text_size=16,
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    goal_radio_group = ft.RadioGroup(
        content=ft.Row(
            [
                ft.Radio(value="Perder peso", label="Perder peso"),
                ft.Radio(value="Ganhar massa", label="Ganhar massa"),
                ft.Radio(value="Manter forma", label="Manter forma"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        value="Manter forma",
    )
    review_text = ft.Markdown("")

    def validate_current_step():
        if current_step[0] == 0:
            name = name_input.value.strip()
            if not name:
                name_input.error_text = "Por favor, insira seu nome."
                name_input.update()
                logger.warning("Nome não preenchido.")
                return False
            name_input.error_text = None
            profile_data["name"] = name
            logger.info(f"Nome coletado: {name}")
            return True
        elif current_step[0] == 1:
            age = age_input.value.strip()
            if not age or not age.isdigit() or int(age) < 10 or int(age) > 100:
                age_input.error_text = "Insira uma idade válida (10-100)."
                age_input.update()
                logger.warning("Idade inválida.")
                return False
            age_input.error_text = None
            profile_data["age"] = int(age)
            logger.info(f"Idade coletada: {age}")
            return True
        elif current_step[0] == 2:
            weight = weight_input.value.strip()
            try:
                weight = float(weight)
                if weight < 30 or weight > 300:
                    weight_input.error_text = "Insira um peso válido (30-300 kg)."
                    weight_input.update()
                    logger.warning("Peso inválido.")
                    return False
            except ValueError:
                weight_input.error_text = "Insira um número válido."
                weight_input.update()
                logger.warning("Peso não é um número.")
                return False
            weight_input.error_text = None
            profile_data["weight"] = weight
            logger.info(f"Peso coletado: {weight}")
            return True
        elif current_step[0] == 3:
            height = height_input.value.strip()
            try:
                height = float(height)
                if height < 100 or height > 250:
                    height_input.error_text = "Insira uma altura válida (100-250 cm)."
                    height_input.update()
                    logger.warning("Altura inválida.")
                    return False
            except ValueError:
                height_input.error_text = "Insira um número válido."
                height_input.update()
                logger.warning("Altura não é um número.")
                return False
            height_input.error_text = None
            profile_data["height"] = int(height)
            logger.info(f"Altura coletada: {height}")
            return True
        elif current_step[0] == 4:
            profile_data["goal"] = goal_radio_group.value
            logger.info(f"Objetivo coletado: {profile_data['goal']}")
            return True
        return True

    def update_review():
        review_content = f"""
        **Revise seus dados:**  
        **Nome:** {profile_data.get("name", "")}  
        **Idade:** {profile_data.get("age", "")}  
        **Peso:** {profile_data.get("weight", "")} kg  
        **Altura:** {profile_data.get("height", "")} cm  
        **Objetivo:** {profile_data.get("goal", "")}
        """
        review_text.value = review_content
        review_text.update()
        logger.info("Conteúdo de revisão atualizado.")

    def reset_form():
        name_input.value = ""
        age_input.value = ""
        weight_input.value = ""
        height_input.value = ""
        goal_radio_group.value = "Manter forma"
        name_input.error_text = None
        age_input.error_text = None
        weight_input.error_text = None
        height_input.error_text = None
        review_text.value = ""
        profile_data.clear()
        current_step[0] = 0
        logger.info("Formulário de perfil reiniciado.")

    def show_loading():
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
        if dialog and dialog.open:
            page.close(dialog)
            page.dialog = None
            logger.info("Diálogo de carregamento fechado")

    def next_step(e):
        nonlocal last_event_time
        current_time = time.time()
        if current_time - last_event_time < 0.5:
            logger.info("Debounce: Evento ignorado por 500ms")
            return
        last_event_time = current_time
        logger.info(f"Tentando avançar da etapa {current_step[0]}")
        if validate_current_step():
            current_step[0] += 1
            if current_step[0] == 5:  # Última etapa: revisão
                update_review()
            update_view()
            logger.info(f"Avançou para a etapa {current_step[0]}")
        else:
            logger.warning("Validação falhou na etapa atual.")

    def previous_step(e):
        nonlocal last_event_time
        current_time = time.time()
        if current_time - last_event_time < 0.5:
            logger.info("Debounce: Evento ignorado por 500ms")
            return
        last_event_time = current_time
        logger.info(f"Tentando voltar da etapa {current_step[0]}")
        if current_step[0] > 0:
            current_step[0] -= 1
            update_view()
            logger.info(f"Retrocedeu para a etapa {current_step[0]}")

    def create_profile(e):
        nonlocal last_event_time
        current_time = time.time()
        if current_time - last_event_time < 0.5:
            logger.info("Debounce: Evento ignorado por 500ms")
            return
        last_event_time = current_time
        logger.info("Enviando dados do perfil...")
        user_id = page.client_storage.get(
            "supafit.user_id"
        ) 
        level = page.client_storage.get("supafit.level")

        if not user_id:
            logger.warning("Tentativa de criar perfil sem user_id")
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
            hide_loading(loading_dialog)
            logger.info(f"Perfil criado para user_id: {user_id}")
            reset_form()
            page.go("/home")
            page.update()
        except Exception as ex:
            hide_loading(loading_dialog)
            logger.error(f"Erro ao criar perfil: {str(ex)}")
            page.update()

    def update_view():
        for index, view in enumerate(steps_views):
            view.visible = index == current_step[0]
        page.update()
        logger.info(f"View atualizada para a etapa {current_step[0]}")

    # Etapas do formulário
    step1 = ft.Column(
        [
            ft.Text("Etapa 1 de 5: Nome", size=20, weight=ft.FontWeight.BOLD),
            name_input,
            ft.Row(
                [ft.ElevatedButton("Próximo", on_click=next_step)],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        visible=True,
    )
    step2 = ft.Column(
        [
            ft.Text("Etapa 2 de 5: Idade", size=20, weight=ft.FontWeight.BOLD),
            age_input,
            ft.Row(
                [
                    ft.ElevatedButton("Voltar", on_click=previous_step),
                    ft.ElevatedButton("Próximo", on_click=next_step),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        visible=False,
    )
    step3 = ft.Column(
        [
            ft.Text("Etapa 3 de 5: Peso", size=20, weight=ft.FontWeight.BOLD),
            weight_input,
            ft.Row(
                [
                    ft.ElevatedButton("Voltar", on_click=previous_step),
                    ft.ElevatedButton("Próximo", on_click=next_step),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        visible=False,
    )
    step4 = ft.Column(
        [
            ft.Text("Etapa 4 de 5: Altura", size=20, weight=ft.FontWeight.BOLD),
            height_input,
            ft.Row(
                [
                    ft.ElevatedButton("Voltar", on_click=previous_step),
                    ft.ElevatedButton("Próximo", on_click=next_step),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        visible=False,
    )
    step5 = ft.Column(
        [
            ft.Text("Etapa 5 de 5: Objetivo", size=20, weight=ft.FontWeight.BOLD),
            goal_radio_group,
            ft.Row(
                [
                    ft.ElevatedButton("Voltar", on_click=previous_step),
                    ft.ElevatedButton("Próximo", on_click=next_step),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        visible=False,
    )
    step6 = ft.Column(
        [
            ft.Text("Revisão", size=20, weight=ft.FontWeight.BOLD),
            review_text,
            ft.Row(
                [
                    ft.ElevatedButton("Voltar", on_click=previous_step),
                    ft.ElevatedButton("Criar Perfil", on_click=create_profile),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        visible=False,
    )

    steps_views = [step1, step2, step3, step4, step5, step6]

    container_steps = ft.Container(
        content=ft.Column(
            steps_views,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
        animate=ft.Animation(500, ft.AnimationCurve.EASE_IN_OUT),
    )

    update_view()
    return container_steps