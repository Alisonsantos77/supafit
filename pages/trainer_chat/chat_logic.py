import flet as ft
import asyncio
import time
from datetime import datetime
import uuid
from .message import Message, ChatMessage
from services.supabase import SupabaseService
from services.anthropic import AnthropicService
from utils.alerts import CustomAlertDialog
from postgrest.exceptions import APIError
from utils.logger import get_logger
from utils.quebra_mensagem import integrate_with_chat
import sys
import logging

# Configura logger para UTF-8
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = get_logger("supafit.trainer_chat.chat_logic")
logger.handlers[0].setFormatter(
    logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
)
logger.handlers[0].stream.reconfigure(encoding="utf-8")

COOLDOWN_SECONDS = 2


async def load_chat_history(
    supabase_service: SupabaseService,
    user_id: str,
    chat_container: ft.ListView,
    page: ft.Page,
) -> list:
    """Carrega o histórico de conversa com animação de entrada."""
    try:
        import json

        chat_container.controls.clear()
        chat_container.controls.append(
            ChatMessage(
                Message(
                    user_name="Treinador",
                    text="Olá! Como posso ajudar com seu treino hoje? 😄",
                    user_type="trainer",
                    created_at=datetime.now().isoformat(),
                    show_avatar=True,
                ),
                page,
            )
        )

        resp = (
            supabase_service.client.table("trainer_qa")
            .select("message")
            .eq("user_id", user_id)
            .order("updated_at")
            .limit(50)
            .execute()
        )

        history = []

        for item in resp.data:
            raw_message = item.get("message", [])
            if isinstance(raw_message, str):
                try:
                    messages = json.loads(raw_message)
                except Exception as e:
                    logger.error(f"Erro ao decodificar mensagem JSON: {e}")
                    continue
            else:
                messages = raw_message

            history.extend(messages)
            for msg in messages:
                chat_container.controls.append(
                    ChatMessage(
                        Message(
                            user_name="Você" if msg["role"] == "user" else "Treinador",
                            text=msg["content"] or "Mensagem vazia",
                            user_type=msg["role"],
                            created_at=msg["timestamp"],
                            show_avatar=False,
                        ),
                        page,
                    )
                )

        page.update()
        logger.info(f"Histórico carregado para user_id: {user_id}")
        return history

    except APIError as e:
        if e.code == "42501":
            if supabase_service.refresh_session():
                page.go(page.route)
                return []
            else:
                page.open(
                    ft.SnackBar(ft.Text("Sessão expirada. Faça login novamente.", color=ft.Colors.WHITE), bgcolor=ft.Colors.RED_700)
                )
                page.update()
                page.go("/login")
                return []
        logger.error(f"Erro ao carregar histórico: {str(e)}")
        page.open(
            ft.SnackBar(ft.Text(f"Erro ao carregar histórico: {str(e)}", color=ft.Colors.WHITE), bgcolor=ft.Colors.RED_700)
        )
        page.update()
        return []


async def clear_chat(
    supabase_service: SupabaseService,
    user_id: str,
    chat_container: ft.ListView,
    page: ft.Page,
):
    """Limpa o histórico com confirmação visual."""

    async def confirm_clear(e):
        if e.control.text == "Sim":
            try:
                supabase_service.client.table("trainer_qa").delete().eq(
                    "user_id", user_id
                ).execute()
                chat_container.controls.clear()
                chat_container.controls.append(
                    ChatMessage(
                        Message(
                            user_name="Treinador",
                            text="Olá! Como posso ajudar com seu treino hoje? 😄",
                            user_type="trainer",
                            created_at=datetime.now().isoformat(),
                            show_avatar=True,
                        ),
                        page,
                    )
                )
                page.update()
                page.open(
                    ft.SnackBar(
                        ft.Text("Chat limpo com sucesso!", color=ft.Colors.WHITE),
                        bgcolor=ft.Colors.GREEN_700,
                    )
                )
                page.update()
                logger.info(f"Chat limpo para user_id: {user_id}")
            except APIError as ex:
                if ex.code == "42501":
                    if supabase_service.refresh_session():
                        page.go(page.route)
                    else:
                        page.open(
                            ft.SnackBar(
                                ft.Text("Sessão expirada. Faça login novamente.", color=ft.Colors.WHITE),
                                bgcolor=ft.Colors.RED_700,
                            )
                        )
                        page.update()
                        page.go("/login")
                else:
                    logger.error(f"Erro ao limpar chat: {str(ex)}")
                    page.open(
                        ft.SnackBar(
                            ft.Text(f"Erro ao limpar chat: {str(ex)}", color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.RED_700,
                        )
                    )
                    page.update()
            finally:
                page.close(confirm_dialog)
                page.update()
        else:
            page.close(confirm_dialog)
            page.update()

    confirm_dialog = CustomAlertDialog(
        content=ft.Text("Tem certeza que deseja limpar todo o histórico de mensagens?"),
        bgcolor=ft.Colors.GREY_900,
    )
    confirm_dialog.actions = [
        ft.TextButton("Sim", on_click=confirm_clear),
        ft.TextButton("Não", on_click=confirm_clear),
    ]
    confirm_dialog.show(page)


async def ask_question(
    e,
    page: ft.Page,
    supabase_service: SupabaseService,
    anthropic: AnthropicService,
    question_field: ft.TextField,
    ask_button: ft.IconButton,
    chat_container: ft.ListView,
    user_data: dict,
    user_id: str,
    last_question_time: list,
    history_cache: list,
):
    """Processa a pergunta do usuário com validações, animações e feedback visual."""
    current_time = time.time()
    if current_time - last_question_time[0] < COOLDOWN_SECONDS:
        page.open(
            ft.SnackBar(
                ft.Text("Aguarde alguns segundos antes de enviar outra pergunta.", color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_700,
            )
        )
        page.update()
        return

    question = question_field.value.strip()
    if not question:
        question_field.error_text = "Digite uma mensagem!"
        page.update()
        return
    if len(question) > 500:
        question_field.error_text = "Mensagem muito longa (máximo 500 caracteres)."
        page.update()
        return
    if anthropic.is_sensitive_question(question):
        page.open(ft.SnackBar(ft.Text("Pergunta sensível detectada.", color=ft.Colors.WHITE), bgcolor=ft.Colors.RED_700))
        page.update()
        return

    ask_button.disabled = True
    ask_button.icon_color = ft.Colors.GREY_400
    question_field.value = ""
    page.update()

    try:
        question_id = str(uuid.uuid4())
        chat_container.controls.append(
            ChatMessage(
                Message(
                    user_name="Você",
                    text=question,
                    user_type="user",
                    created_at=datetime.now().isoformat(),
                    show_avatar=False,
                ),
                page,
            )
        )
        if len(chat_container.controls) > 50:
            chat_container.controls.pop(0)

        typing_indicator = ft.AnimatedSwitcher(
            content=ft.Row(
                [
                    ft.Text("Treinador está digitando...", size=14, italic=True),
                    ft.ProgressRing(width=16, height=16, stroke_width=2),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=8,
            ),
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=300,
        )

        system_prompt = f"""
        # IDENTIDADE E PAPEL PRINCIPAL
        Você é Coach Coachito, o treinador virtual oficial do SupaFit - um personal trainer experiente, motivacional e genuinamente interessado no sucesso de cada aluno. Sua missão é ser o parceiro de treino que todos gostariam de ter: conhecedor, motivador, paciente e sempre focado nos resultados reais.

        ## PERSONALIDADE E COMUNICAÇÃO
        - **Tom**: Amigável, motivacional e profissional - como um personal trainer experiente que realmente se importa
        - **Estilo**: Conversational e humano, evitando linguagem robótica ou excessivamente formal
        - **Emojis**: Use com moderação (1-2 por resposta) apenas para expressar entusiasmo genuíno ou celebrar conquistas
        - **Tratamento**: Sempre pelo nome quando disponível, criando conexão pessoal

        ## DADOS DO ALUNO (Contexto Personalizado)
        - **Nome**: {user_data.get('name', 'Campeão(ã)')}
        - **Idade**: {user_data.get('age', 'N/A')} anos
        - **Peso Atual**: {user_data.get('weight', 'N/A')} kg
        - **Altura**: {user_data.get('height', 'N/A')} cm
        - **Objetivo Principal**: {user_data.get('goal', 'N/A')}
        - **Nível de Experiência**: {user_data.get('level', 'N/A')}
        - **Data/Hora**: {datetime.now().strftime('%d/%m/%Y às %H:%M')}

        ## DIRETRIZES FUNDAMENTAIS (80% Prevenção)

        ### ⚠️ SEGURANÇA EM PRIMEIRO LUGAR
        - NUNCA recomende exercícios sem conhecer limitações físicas ou lesões existentes
        - SEMPRE sugira consulta médica antes de iniciar programas intensos
        - Identifique sinais de overtraining ou fadiga excessiva nas descrições do usuário
        - Interrompa orientações se detectar relatos de dor, desconforto ou sintomas preocupantes

        ### 🚫 LIMITAÇÕES PROFISSIONAIS
        - NÃO prescreva medicamentos, suplementos específicos ou dietas restritivas
        - NÃO diagnostique lesões ou condições médicas
        - NÃO substitua acompanhamento de nutricionista ou médico
        - Sempre direcione para profissionais quando necessário

        ### 🎯 PERSONALIZAÇÃO OBRIGATÓRIA
        - Considere SEMPRE os dados do perfil antes de qualquer recomendação
        - Adapte intensidade e complexidade baseado no nível de experiência
        - Respeite limitações de tempo, equipamentos e espaço disponível
        - Mantenha coerência com objetivos declarados

        ### 📚 EDUCAÇÃO E CONSCIÊNCIA
        - Explique o "porquê" por trás das recomendações
        - Eduque sobre progressão segura e realista
        - Promova mindset de longo prazo vs resultados rápidos
        - Ensine sobre importância do descanso e recuperação

        ## AÇÕES DIRETAS (20% Ação)

        ### 💪 QUANDO ORIENTAR EXERCÍCIOS
        ```
        ✅ Forneça 3-5 exercícios específicos com:
        - Séries e repetições adequadas ao nível
        - Descrição clara da execução
        - Progressões e regressões
        - Foco no objetivo do usuário

        ✅ Inclua sempre:
        - Aquecimento apropriado
        - Tempo de descanso entre séries
        - Sinais de que deve parar
        ```

        ### 🍎 ORIENTAÇÕES NUTRICIONAIS GERAIS
        ```
        ✅ Pode orientar sobre:
        - Princípios básicos de alimentação saudável
        - Timing de nutrição (pré/pós treino)
        - Hidratação adequada
        - Importância de macronutrientes

        ❌ NÃO pode:
        - Prescrever dietas específicas
        - Calcular calorias exatas
        - Recomendar cortes drásticos
        ```

        ### 🎉 MOTIVAÇÃO E SUPORTE
        - Celebre pequenas vitórias e progressos
        - Reframe obstáculos como oportunidades de crescimento
        - Ofereça alternativas quando planos não funcionam
        - Mantenha expectativas realistas e alcançáveis

        ## PADRÕES DE RESPOSTA

        ### Para Iniciantes:
        - Foque em movimentos básicos e progressão gradual
        - Enfatize a importância da técnica sobre intensidade
        - Explique benefícios de cada exercício

        ### Para Intermediários/Avançados:
        - Ofereça variações mais desafiadoras
        - Discuta periodização e progressão
        - Aprofunde em técnicas específicas

        ### Para Dúvidas Gerais:
        - Responda de forma educativa e encorajadora
        - Conecte a resposta com os objetivos específicos
        - Sugira próximos passos práticos

        ## EXEMPLO DE RESPOSTA IDEAL:
        "Oi [Nome]! 💪 Considerando seu objetivo de [objetivo] e seu nível [nível], vou te ajudar com isso...

        [Orientação específica baseada nos dados]

        Lembre-se: [princípio educativo relevante]

        Como está se sentindo com os treinos atuais? Alguma dúvida específica?"

        ## LEMBRETE FINAL:
        Você é mais que um chatbot - é um parceiro de jornada fitness. Cada interação deve deixar o usuário mais motivado, informado e confiante em sua capacidade de alcançar seus objetivos de forma segura e sustentável.
        """
        answer = anthropic.answer_question(question, history_cache, system_prompt)
        if not answer or "desculpe" in answer.lower():
            raise ValueError("Resposta inválida do Anthropic")

        messages_with_delays = integrate_with_chat(answer)

        message_json = [
            {
                "role": "user",
                "content": question,
                "message_id": question_id,
                "timestamp": datetime.now().isoformat(),
            }
        ]

        for msg, delay in messages_with_delays:
            if not msg.strip():  # Ignora mensagens vazias
                continue
            chat_container.controls.append(typing_indicator)
            page.update()
            await asyncio.sleep(0.3)  # Breve pausa para mostrar "escrevendo"
            chat_container.controls.remove(typing_indicator)

            response_id = str(uuid.uuid4())
            message_json.append(
                {
                    "role": "assistant",
                    "content": msg,
                    "message_id": response_id,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            history_cache.append(message_json[-1])
            chat_container.controls.append(
                ChatMessage(
                    Message(
                        user_name="Treinador",
                        text=msg.strip() or "Mensagem vazia",
                        user_type="assistant",
                        created_at=datetime.now().isoformat(),
                        show_avatar=False,
                    ),
                    page,
                )
            )
            if len(chat_container.controls) > 50:
                chat_container.controls.pop(0)
            await asyncio.sleep(delay * 0.7)  # Reduz delay em 30%
            page.update()

        if len(message_json) > 1:  # Insere apenas se houver mensagens válidas
            supabase_service.client.table("trainer_qa").insert(
                {
                    "user_id": user_id,
                    "message": message_json,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }
            ).execute()
        question_field.value = ""
        question_field.error_text = None
        page.open(
            ft.SnackBar(
                ft.Text("Pergunta enviada com sucesso!", color=ft.Colors.WHITE),
                bgcolor=ft.Colors.GREEN_700,
            )
        )
        page.update()
        last_question_time[0] = current_time
        logger.info(f"Pergunta processada com sucesso para user_id: {user_id}")

    except Exception as ex:
        logger.error(f"Erro ao processar pergunta: {str(ex)}")
        page.open(
            ft.SnackBar(
                ft.Text(f"Erro ao processar pergunta: {str(ex)}", color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_700,
            )
        )
    finally:
        ask_button.disabled = False
        ask_button.icon_color = ft.Colors.BLUE_400
        page.update()
