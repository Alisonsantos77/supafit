import os
import json
import httpx
import requests
from supabase import create_client, Client
from dotenv import load_dotenv
import flet as ft
from utils.logger import get_logger

logger = get_logger("supabafit.services")


class AnthropicService:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.base_url = "https://api.anthropic.com/v1/messages"
        logger.info(f"Serviço Anthropic inicializado com base_url: {self.base_url}")

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
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
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
            "model": "claude-3-opus-20240229",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            logger.info("Plano de treino gerado com sucesso pelo Anthropic.")
            return result.get("content", [{}])[0].get("text", "")
        except Exception as e:
            logger.error(f"Erro ao gerar plano de treino com Anthropic: {str(e)}")
            raise e


    async def answer_question(
        self, question: str, history: list, system_prompt: str = None
    ) -> str:
        """Envia a pergunta, histórico e prompt do sistema para a API da Anthropic e retorna a resposta.

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
            logger.info("Enviando pergunta para Anthropic: %s", question)
            messages = []
            for item in history:
                if item.get("role") in ["user", "assistant"] and item.get("content"):
                    messages.append({"role": item["role"], "content": item["content"]})
            messages.append({"role": "user", "content": question})

            payload = {
                "model": "claude-3-5-sonnet-latest",
                "max_tokens": 1000,
                "temperature": 0.7,
                "messages": messages,
            }
            if system_prompt:
                payload["system"] = system_prompt
                logger.debug("Prompt do sistema incluído: %s", system_prompt[:50])

            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    (
                        f"{self.base_url}/v1/messages"
                        if not self.base_url.endswith("/v1/messages")
                        else self.base_url
                    ),
                    json=payload,
                    headers=headers,
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()
                if "content" in data and isinstance(data["content"], list):
                    text = data["content"][0].get("text", "").strip()
                elif "completion" in data:
                    text = data["completion"].strip()
                else:
                    text = str(data)

                logger.info("Resposta recebida de Anthropic: %s", text[:50])
                return text

        except httpx.HTTPStatusError as ex:
            error_text = ex.response.text or str(ex)
            logger.error(
                "API Anthropic retornou status #{ex.response.status_code}: {error_text}"
            )
            raise
        except Exception as ex:
            logger.error(f"Erro inesperado em answer_question: {ex}")
            return "Desculpe, não consegui responder agora."
    
    def is_sensitive_question(self, question: str) -> bool:
        """Verifica se a pergunta contém conteúdo sensível ou inadequado usando o Claude.

        Args:
            question (str): Pergunta a ser verificada.

        Returns:
            bool: True se for sensível, False caso contrário.
        """
        try:
            moderation_prompt = f"""Você é um moderador virtual treinado para filtrar postagens em uma comunidade fitness.  
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
            """
            payload = {
                "model": "claude-3-5-sonnet-latest",
                "max_tokens": 2,
                "messages": [{"role": "user", "content": moderation_prompt}],
            }
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            }
            response = httpx.post(
                self.base_url, json=payload, headers=headers, timeout=10
            )
            response.raise_for_status()
            data = response.json()
            if "content" in data and isinstance(data["content"], list):
                text = data["content"][0].get("text", "").strip()
                return text.lower() == "sensitive"
            logger.warning(f"Resposta inesperada da API Anthropic: {data}")
            return False
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
        """Verifica se o nome contém conteúdo sensível ou inadequado usando o Claude."""
        try:
            moderation_prompt = f"""Você é um verificador de nomes de usuário em uma plataforma fitness.  
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
                "model": "claude-3-5-sonnet-latest",
                "max_tokens": 2,
                "messages": [{"role": "user", "content": moderation_prompt}],
            }
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            }
            response = httpx.post(self.base_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if "content" in data and isinstance(data["content"], list):
                text_response = data["content"][0].get("text", "").strip()
                return text_response.lower() == "sensitive"
            logger.warning(f"Resposta inesperada da API Anthropic: {data}")
            return False
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
        """
        Verifica se o texto contém conteúdo sensível usando a API da Anthropic.

        Args:
            text (str): Texto a ser verificado (restrições do usuário).

        Returns:
            bool: True se o texto contém conteúdo sensível, False caso contrário.
        """
        try:
            moderation_prompt = f"""Você é um assistente que coleta informações de lesões e limitações físicas em uma aplicação fitness.  
            Sua tarefa é analisar o relato do usuário e **retornar única e exclusivamente** uma dessas duas respostas:  
            - "sensitive"  
            - "safe"  

            1) [80% Prevenção] Se o texto contiver qualquer um dos seguintes elementos, retorne "sensitive":  
            - Descrições gráficas de ferimentos (ex.: “ossos expostos”, “sangue em abundância”)  
            - Dados de saúde vinculados a informações pessoais identificáveis (ex.: CPF, data de nascimento)  
            - Ausência de qualquer termo que indique lesão ou dor (ex.: “lesão”, “fratura”, “luxação”, “dor”)  

            2) [20% Ação] Se o texto for um relato objetivo de lesão ou limitação (contiver termos como “lesão”, “fratura”, “dor” sem os elementos acima), retorne "safe".  
            """
            payload = {
                "model": "claude-3-5-sonnet-latest",
                "max_tokens": 2,
                "messages": [{"role": "user", "content": moderation_prompt}],
            }
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            }
            response = httpx.post(
                self.base_url, json=payload, headers=headers, timeout=10
            )
            response.raise_for_status()
            data = response.json()
            if "content" in data and isinstance(data["content"], list):
                text_response = data["content"][0].get("text", "").strip()
                return text_response.lower() == "sensitive"
            logger.warning(f"Resposta inesperada da API Anthropic: {data}")
            return False
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP ao verificar nome sensível: {e.response.text}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Erro de decodificação JSON: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar nome sensível: {str(e)}")
            return False
