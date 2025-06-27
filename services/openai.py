import os
import json
import httpx
import openai
from dotenv import load_dotenv
from utils.logger import get_logger

logger = get_logger("supafit.services")


class OpenAIService:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1/chat/completions"
        openai.api_key = self.api_key
        logger.info(f"Serviço OpenAI inicializado com base_url: {self.base_url}")

    def get_workout_plan(self, user_data: dict):
        """Gera um plano de treino personalizado com base nos dados do usuário.

        Args:
            user_data (dict): Dados do usuário (nível, objetivo, peso, altura, idade).

        Returns:
            str: Plano de treino gerado.

        Raises:
            Exception: Se a geração do plano falhar.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        prompt = f"""
        Crie um plano de treino personalizado com base nos seguintes dados do usuário:
        - Nível: {user_data.get('level', '')}
        - Objetivo: {user_data.get('goal', '')}
        - Peso: {user_data.get('weight', '')} kg
        - Altura: {user_data.get('height', '')} cm
        - Idade: {user_data.get('age', '')} anos

        Forneça um plano de treino semanal, com exercícios, séries, repetições e dias da semana.
        """
        data = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.7,
        }
        try:
            response = httpx.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            logger.info("Plano de treino gerado com sucesso pelo OpenAI.")
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Erro ao gerar plano de treino com OpenAI: {str(e)}")
            raise e

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
            logger.info("Enviando pergunta para OpenAI: %s", question)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
                logger.debug("Prompt do sistema incluído: %s", system_prompt[:50])
            for item in history:
                if item.get("role") in ["user", "assistant"] and item.get("content"):
                    messages.append({"role": item["role"], "content": item["content"]})
            messages.append({"role": "user", "content": question})

            payload = {
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
                logger.info("Resposta recebida de OpenAI: %s", text[:50])
                return text
        except httpx.HTTPStatusError as ex:
            error_text = ex.response.text or str(ex)
            logger.error(
                f"API OpenAI retornou status #{ex.response.status_code}: {error_text}"
            )
            raise
        except Exception as ex:
            logger.error(f"Erro inesperado em answer_question: {ex}")
            return "Desculpe, não consegui responder agora."

    def is_sensitive_question(self, question: str) -> bool:
        """Verifica se a pergunta contém conteúdo sensível ou inadequado usando a API da OpenAI.

        Args:
            question (str): Pergunta a ser verificada.

        Returns:
            bool: True se for sensível, False caso contrário.
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
            response = httpx.post(
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
            logger.error(f"Erro HTTP ao verificar pergunta sensível: {e.response.text}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Erro de decodificação JSON: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar pergunta sensível: {str(e)}")
            return False

    def is_sensitive_name(self, name: str) -> bool:
        """Verifica se o nome contém conteúdo sensível ou inadequado usando a API da OpenAI."""
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
            response = httpx.post(
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
            logger.error(f"Erro HTTP ao verificar nome sensível: {e.response.text}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Erro de decodificação JSON: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar nome sensível: {str(e)}")
            return False

    def is_sensitive_restrictions(self, text: str) -> bool:
        """Verifica se o texto contém conteúdo sensível usando a API da OpenAI.

        Args:
            text (str): Texto a ser verificado (restrições do usuário).

        Returns:
            bool: True se o texto contém conteúdo sensível, False caso contrário.
        """
        try:
            moderation_prompt = f"""
            Você é um assistente que coleta informações de lesões e limitações físicas em uma aplicação fitness.
            Sua tarefa é analisar o relato do usuário e **retornar única e exclusivamente** uma dessas duas respostas:
            - "sensitive"
            - "safe"

            1) [80% Prevenção] Se o texto contiver qualquer um dos seguintes elementos, retorne "sensitive":
            - Descrições gráficas de ferimentos (ex.: “ossos expostos”, “sangue em abundância”)
            - Dados de saúde vinculados a informações pessoais identificáveis (ex.: CPF, data de nascimento)
            - Ausência de qualquer termo que indique lesão ou dor (ex.: “lesão”, “fratura”, “luxação”, “dor”)

            2) [20% Ação] Se o texto for um relato objetivo de lesão ou limitação (contiver termos como “lesão”, “fratura”, “dor” sem os elementos acima), retorne "safe".

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
            response = httpx.post(
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
            logger.error(
                f"Erro HTTP ao verificar restrições sensíveis: {e.response.text}"
            )
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Erro de decodificação JSON: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar restrições sensíveis: {str(e)}")
            return False
