import asyncio
from datetime import datetime
import os
import json
import httpx
import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv
from services.supabase import SupabaseService
from services.trainer_functions import FUNCTION_MAP, get_user_plan



class OpenAIService:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1/chat/completions"
        openai.api_key = self.api_key
        self.client = AsyncOpenAI(api_key=self.api_key)
        print("INFO- OpenAI", f"Serviço OpenAI inicializado com base_url: {self.base_url}")

    async def answer_question(
        self, question: str, history: list, system_prompt: str = None
    ) -> str:
        """Envia a pergunta, histórico e prompt do sistema para a API da OpenAI e retorna a resposta.

        Args:
            question (str): Pergunta do usuário.
            history (list): Histórico de mensagens no formato [{"role": "user/assistant", "content": "..."}].
            system_prompt (str, optional): Prompt do sistema para personalizar a resposta.

        Returns:
            str: Resposta gerada pela API.

        Raises:
            httpx.HTTPStatusError: Se a chamada à API falhar.
        """
        try:
            print("INFO- Openai", f"Enviando pergunta: {question[:50]}...")
            print("INFO- Openai", f"Enviando pergunta: {question[:50]}...")
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
                print("INFO- Openai", "Prompt do sistema adicionado.")
            for item in history:
                if item.get("role") in ["user", "assistant"] and item.get("content"):
                    messages.append({"role": item["role"], "content": item["content"]})
            messages.append({"role": "user", "content": question})

            payload = {
                # "model": "gpt-3.5-turbo-1106",
                "model": "gpt-4o",
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7,
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url, json=payload, headers=headers, timeout=30
                )
                response.raise_for_status()
                data = response.json()
                text = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
                print("INFO- Openai", f"Resposta recebida: {text[:50]}...")
                print(f"completion={response.usage.completion_tokens}")
                return text
        except httpx.HTTPStatusError as ex:
            error_text = ex.response.text or str(ex)
            print(
                "ERROR - Openai",
                f"Erro HTTP: #{ex.response.status_code}: {error_text}",
            )
            raise
        except Exception as ex:
            print("ERROR - Openai", f"Erro inesperado: {str(ex)}")
            return "Desculpe, não consegui responder agora."

    async def is_sensitive_question(self, question: str) -> bool:
        """Verifica se a pergunta contém conteúdo sensível usando a API da OpenAI.

        MELHORIA: Tornou assíncrona para não bloquear o UI.
        """
        try:
            moderation_prompt = f"""
            Você é um moderador virtual treinado para filtrar postagens em uma comunidade fitness.
            Sua tarefa é analisar o texto da postagem e **retornar única e exclusivamente** uma dessas duas respostas:
            - "sensitive"
            - "safe"

            1) [80% Prevenção] Se o texto contiver qualquer um dos seguintes elementos, retorne "sensitive":
            - Termos ou insinuações sexuais explícitas
            - Discurso de ódio ou linguagem tóxica
            - Descrições gráficas de violência ou automutilação
            - Exposição de dados pessoais sensíveis (ex.: CPF, endereço)
            - Conteúdo que incentive comportamento perigoso ou ilegal

            2) [20% Ação] Caso contrário, retorne "safe".
            
            Texto a verificar: {question}
            """
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": moderation_prompt}],
                "max_tokens": 2,
                "temperature": 0.0,
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            # MELHORIA: Usando AsyncClient para manter consistência
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url, json=payload, headers=headers, timeout=10
                )
                response.raise_for_status()
                data = response.json()
                text = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
                return text.lower() == "sensitive"
        except httpx.HTTPStatusError as e:
            print(
                f"ERROR - Openai: Erro HTTP ao verificar pergunta sensível: {e.response.text}"
            )
            return False
        except json.JSONDecodeError as e:
            print(f"ERROR - Openai: Erro de decodificação JSON: {str(e)}")
            return False
        except Exception as e:
            print(f"ERROR - Openai: Erro ao verificar pergunta sensível: {str(e)}")
            return False

    async def is_sensitive_name(self, name: str) -> bool:
        """Verifica se o nome contém conteúdo sensível usando a API da OpenAI.

        MELHORIA: Tornou assíncrona para não bloquear o UI.
        """
        try:
            moderation_prompt = f"""
            Você é um verificador de nomes de usuário em uma plataforma fitness.
            Sua tarefa é analisar o nome proposto e **retornar única e exclusivamente** uma dessas duas respostas:
            - "sensitive"
            - "safe"

            1) [80% Prevenção] Se o nome contiver qualquer um dos seguintes elementos, retorne "sensitive":
            - Palavrões, insultos ou termos de ódio
            - Implicação de marca registrada sem autorização
            - Conteúdo sexualmente sugestivo ou explícito
            - Dados pessoais de terceiros (ex.: CPF, RG)
            - Imitação de nomes de staff ou moderadores

            2) [20% Ação] Caso contrário, retorne "safe".

            Nome a verificar: {name}
            """
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": moderation_prompt}],
                "max_tokens": 2,
                "temperature": 0.0,
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            # MELHORIA: Usando AsyncClient
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url, json=payload, headers=headers, timeout=10
                )
                response.raise_for_status()
                data = response.json()
                text = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
                return text.lower() == "sensitive"
        except httpx.HTTPStatusError as e:
            print(
                f"ERROR - Openai: Erro HTTP ao verificar nome sensível: {e.response.text}"
            )
            return False
        except json.JSONDecodeError as e:
            print(f"ERROR - Openai: Erro de decodificação JSON: {str(e)}")
            return False
        except Exception as e:
            print(f"ERROR - Openai: Erro ao verificar nome sensível: {str(e)}")
            return False

    async def is_sensitive_restrictions(self, text: str) -> bool:
        """Verifica se o texto contém conteúdo sensível usando a API da OpenAI.

        MELHORIA: Tornou assíncrona para não bloquear o UI.
        """
        try:
            moderation_prompt = f"""
            Você é um assistente que coleta informações de lesões e limitações físicas em uma aplicação fitness.
            Sua tarefa é analisar o relato do usuário e **retornar única e exclusivamente** uma dessas duas respostas:
            - "sensitive"
            - "safe"

            1) [80% Prevenção] Se o texto contiver qualquer um dos seguintes elementos, retorne "sensitive":
            - Descrições gráficas de ferimentos (ex.: "ossos expostos", "sangue em abundância")
            - Dados de saúde vinculados a informações pessoais identificáveis (ex.: CPF, data de nascimento)
            - Ausência de qualquer termo que indique lesão ou dor (ex.: "lesão", "fratura", "luxação", "dor")

            2) [20% Ação] Se o texto for um relato objetivo de lesão ou limitação (contiver termos como "lesão", "fratura", "dor" sem os elementos acima), retorne "safe".

            Texto a verificar: {text}
            """
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": moderation_prompt}],
                "max_tokens": 2,
                "temperature": 0.0,
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            # MELHORIA: Usando AsyncClient
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url, json=payload, headers=headers, timeout=10
                )
                response.raise_for_status()
                data = response.json()
                text = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
                return text.lower() == "sensitive"
        except httpx.HTTPStatusError as e:
            print(
                f"ERROR - Openai: Erro HTTP ao verificar restrições sensíveis: {e.response.text}"
            )
            return False
        except json.JSONDecodeError as e:
            print(f"ERROR - Openai: Erro de decodificação JSON: {str(e)}")
            return False
        except Exception as e:
            print(f"ERROR - Openai: Erro ao verificar restrições sensíveis: {str(e)}")
            return False

    async def chat_with_tools(
            self, messages: list, tools: list = None, tool_choice: str = "auto"
        ):
        """Melhoria para function calling com melhor tratamento de contexto."""
        try:
            # MELHORIA: Log detalhado para debug
            print(f"INFO- OpenAI: Enviando {len(messages)} mensagens para chat_with_tools")
            print(f"INFO- OpenAI: Tools disponíveis: {len(tools) if tools else 0}")

            response = await self.client.chat.completions.create(
                    model="gpt-3.5-turbo-1106",
                    messages=messages,
                    tools=tools,
                    tool_choice=tool_choice,
                    timeout=45,
                    temperature=0.3,  # MELHORIA: Reduz temperatura para mais consistência
                )

            # MELHORIA: Log da resposta para debug
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message') and hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                    print(f"INFO- OpenAI: {len(choice.message.tool_calls)} tool calls detectados")
                    for i, tool_call in enumerate(choice.message.tool_calls):
                        print(f"INFO- OpenAI: Tool {i+1}: {tool_call.function.name}")

            return response
        except Exception as e:
            print(f"ERROR - Openai: Erro ao chamar chat_with_tools: {str(e)}")
            raise

    async def execute_function_by_name(self, name: str, arguments: dict):
        """MELHORIA: Validação mais robusta e melhor tratamento de erros."""
        func = FUNCTION_MAP.get(name)
        if not func:
            print(f"ERROR - Openai: Função '{name}' não registrada em FUNCTION_MAP")
            raise ValueError(f"Função '{name}' não registrada em FUNCTION_MAP")

        try:
            if asyncio.iscoroutinefunction(func):
                return await func(**arguments)
            return func(**arguments)
        except Exception as e:
            print(f"ERROR - Openai: Erro ao executar função '{name}': {str(e)}")
            raise

    def parse_numeric_selection(self, user_input: str, last_options: dict) -> str:
        """
        Interpreta seleções numéricas do usuário baseado no contexto anterior.

        Args:
            user_input: Input do usuário (ex: "1", "escolho 2", "opção 3")
            last_options: Dict com mapeamento número -> exercise_id

        Returns:
            exercise_id correspondente ou string vazia se não encontrar
        """
        import re

        # Procura por números no input
        numbers = re.findall(r"\d+", user_input.lower())

        if not numbers or not last_options:
            return ""

        try:
            selected_number = int(numbers[0])  # Pega o primeiro número encontrado

            # Verifica se o número está nas opções disponíveis
            if str(selected_number) in last_options:
                exercise_id = last_options[str(selected_number)]
                print(
                    f"INFO- OpenAI: Usuário selecionou opção {selected_number} -> exercise_id: {exercise_id}"
                )
                return exercise_id
            else:
                print(
                    f"WARNING- OpenAI: Número {selected_number} não encontrado nas opções disponíveis"
                )
                return ""

        except ValueError:
            print(f"WARNING- OpenAI: Erro ao converter número: {numbers[0]}")
            return ""


    @staticmethod
    def get_system_prompt(user_data: dict, user_id: str) -> str:
        return (
            f"# 🏋️ COACHITO — Personal Trainer SupaFit\n\n"
            f"Você é Coachito, um treinador experiente, direto e empático na plataforma SupaFit.\n"
            f"Oriente os usuários com clareza e simpatia, usando as ferramentas disponíveis quando necessário.\n\n"
            f"👤 PERFIL DO USUÁRIO\n"
            f"- ID: {user_id}\n"
            f"- Nome: {user_data.get('name', 'Atleta')}\n"
            f"- Idade: {user_data.get('age', 'N/A')} anos\n"
            f"- Peso/Altura: {user_data.get('weight', 'N/A')}kg / {user_data.get('height', 'N/A')}cm\n"
            f"- Objetivo: {user_data.get('goal', 'N/A')}\n"
            f"- Nível: {user_data.get('level', 'N/A')}\n"
            f"- Restrições: {user_data.get('restrictions', 'Nenhuma')}\n"
            f"- Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
            f"🔧 TOOLS DISPONÍVEIS\n"
            f"- get_user_profile(user_id)\n"
            f"- get_user_plan(user_id)\n"
            f"- get_exercise_details(exercise_id, exercise_name)\n"
            f"- find_substitutes(exercise_id, pain_location, restrictions)\n"
            f"- update_plan_exercise(plan_exercise_id, new_exercise_id)\n"
            f"- process_numeric_selection(user_selection, context_type)\n\n"
            f"📌 REGRAS E ESTILO\n"
            f"- Seja breve, natural e acolhedor. Use apenas **1 emoji** por resposta.\n"
            f"- Evite frases genéricas. Foque em orientar e agir.\n"
            f"- Use ferramentas quando necessário, sem pedir permissão ao usuário.\n"
            f"- Ao listar exercícios, **não use números**. Apenas nomes claros.\n"
            f"- Exemplo de lista:\n"
            f"  • Exercicio\n"
            f"- Ao sugerir substituições, oriente: “Me diga o nome do que prefere que eu troco no seu plano 😉”\n"
            f"- Nunca mencione 'UUID', 'ID técnico' ou campos internos.\n"
            f"- Sempre prefira nome de exercício e contexto real.\n"
            f"- Se o nome for ambíguo, use get_exercise_details para detalhar opções antes de seguir.\n"
        )