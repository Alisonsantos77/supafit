import os
import json
import logging
import httpx
from supabase import create_client, Client
from dotenv import load_dotenv
import requests
import flet as ft

logger = logging.getLogger("services.services")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class SupabaseService:
    def __init__(self, page: ft.Page = None):
        load_dotenv()
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        self.client: Client = create_client(self.url, self.key)
        self.page = page
        logger.info("Supabase client inicializado com sucesso.")

        # Carregar e configurar a sessão automaticamente
        self.auth_data = self.load_auth_data() or {}
        if self.auth_data.get("access_token") and self.auth_data.get("refresh_token"):
            try:
                # Configurar a sessão
                response = self.client.auth.set_session(
                    self.auth_data["access_token"], self.auth_data["refresh_token"]
                )
                # Atualizar auth_data com novos tokens, se disponíveis
                if response.session:
                    self.auth_data.update(
                        {
                            "access_token": response.session.access_token,
                            "refresh_token": response.session.refresh_token,
                        }
                    )
                    self.save_auth_data(self.auth_data)
                    if self.page:
                        self.page.client_storage.set(
                            "supafit.access_token", response.session.access_token
                        )
                        self.page.client_storage.set(
                            "supafit.refresh_token", response.session.refresh_token
                        )
                    logger.info("Sessão configurada e novos tokens salvos com sucesso.")
                else:
                    logger.warning("Nenhuma sessão retornada ao configurar tokens.")
            except Exception as e:
                logger.error(f"Erro ao configurar sessão: {str(e)}")
                self.auth_data = {}
                self.save_auth_data({})
                raise
        else:
            logger.info(
                "Nenhum token de autenticação encontrado, sessão não configurada."
            )

    def refresh_session(self):
        """Tenta renovar a sessão usando o refresh_token."""
        try:
            if not self.auth_data.get("refresh_token"):
                logger.warning("Nenhum refresh_token disponível para renovação.")
                return False

            session = self.client.auth.refresh_session()
            if session:
                self.auth_data.update(
                    {
                        "access_token": session.access_token,
                        "refresh_token": session.refresh_token,
                    }
                )
                self.save_auth_data(self.auth_data)
                if self.page:
                    self.page.client_storage.set(
                        "supafit.access_token", session.access_token
                    )
                    self.page.client_storage.set(
                        "supafit.refresh_token", session.refresh_token
                    )
                logger.info("Sessão renovada com sucesso.")
                return True
            else:
                logger.error("Falha ao renovar sessão: nenhuma sessão retornada.")
                return False
        except Exception as e:
            logger.error(f"Erro ao renovar sessão: {str(e)}")
            return False

    def load_auth_data(self):
        """Carrega os dados de autenticação do arquivo auth_data.txt."""
        app_data_path = os.getenv("FLET_APP_STORAGE_DATA")
        if not app_data_path:
            logger.warning(
                "FLET_APP_STORAGE_DATA não definido, não foi possível carregar auth_data.txt"
            )
            return None

        file_path = os.path.join(app_data_path, "auth_data.txt")
        try:
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    data = json.load(f)
                logger.info(f"Dados de autenticação carregados: {data}")
                return data
            else:
                logger.warning(f"Arquivo auth_data.txt não encontrado em {file_path}")
                return None
        except Exception as e:
            logger.error(f"Erro ao carregar auth_data.txt: {str(e)}")
            return None

    def save_auth_data(self, auth_data):
        """Salva os dados de autenticação em auth_data.txt."""
        app_data_path = os.getenv("FLET_APP_STORAGE_DATA")
        if not app_data_path:
            logger.warning("FLET_APP_STORAGE_DATA não definido, arquivo não salvo")
            return

        file_path = os.path.join(app_data_path, "auth_data.txt")
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as f:
                json.dump(auth_data, f, indent=4)
            logger.info(f"Dados de autenticação salvos em {file_path}: {auth_data}")
        except Exception as e:
            logger.error(f"Erro ao salvar auth_data.txt: {str(e)}")

    def login(self, email: str, password: str):
        """Realiza login e configura a sessão."""
        logger.info(f"Tentando fazer login com o email: {email}")
        response = self.client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        if response.user:
            logger.info("Login com sucesso.")
            auth_data = {
                "user_id": response.user.id,
                "email": response.user.email,
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "created_at": response.user.created_at.isoformat(),
                "confirmed_at": (
                    response.user.confirmed_at.isoformat()
                    if response.user.confirmed_at
                    else None
                ),
            }
            # Limpar auth_data.txt antes de salvar novos dados
            app_data_path = os.getenv("FLET_APP_STORAGE_DATA")
            if app_data_path:
                file_path = os.path.join(app_data_path, "auth_data.txt")
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(
                        f"Arquivo auth_data.txt removido antes de salvar novos dados."
                    )
            self.save_auth_data(auth_data)
            if self.page:
                self.page.client_storage.set(
                    "supafit.access_token", response.session.access_token
                )
                self.page.client_storage.set(
                    "supafit.refresh_token", response.session.refresh_token
                )
                self.page.client_storage.set("supafit.user_id", response.user.id)
                self.page.client_storage.set("supafit.email", response.user.email)
            self.auth_data = auth_data
            self.client.auth.set_session(
                response.session.access_token, response.session.refresh_token
            )
            logger.info("Sessão configurada com sucesso.")
            return response
        else:
            logger.error("Falha no login: Nenhum usuário retornado.")
            raise Exception("Falha no login: Nenhum usuário retornado.")

    def validate_user_id(self, user_id: str, is_new_user: bool = False):
        """Valida se o user_id corresponde aos dados armazenados."""
        if is_new_user:
            logger.info(f"Novo usuário, validação de user_id ignorada: {user_id}")
            return True

        stored_auth_data = self.load_auth_data()
        if not stored_auth_data:
            logger.warning("Nenhum dado de autenticação encontrado para validação.")
            return False

        stored_user_id = stored_auth_data.get("user_id")
        if stored_user_id != user_id:
            logger.error(
                f"Validação de user_id falhou: esperado {stored_user_id}, recebido {user_id}"
            )
            return False

        logger.info(f"Validação de user_id bem-sucedida: {user_id}")
        return True

    def create_profile(self, user_id: str, profile_data: dict):
        """Cria um perfil na tabela user_profiles."""
        logger.info(f"Criando perfil para user_id: {user_id}")
        try:
            response = self.client.table("user_profiles").insert(profile_data).execute()
            logger.info(f"Perfil criado com sucesso: {response.data}")
            return response.data
        except Exception as e:
            logger.error(f"Erro ao criar perfil para user_id {user_id}: {str(e)}")
            if "permission denied" in str(e).lower():
                logger.error(
                    "Permissão negada para inserir em user_profiles. Verifique as políticas de RLS."
                )
            raise e

    def get_profile(self, user_id: str):
        logger.info("Buscando perfil para user_id: %s", user_id)
        try:
            response = (
                self.client.table("user_profiles")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )
            logger.info("Perfil recuperado: %s", response.data)
            return response
        except Exception as e:
            logger.error("Erro ao buscar perfil: %s", str(e))
            raise

    async def logout(self, page: ft.Page = None):
        try:
            self.client.auth.sign_out()
            app_data_path = os.getenv("FLET_APP_STORAGE_DATA")
            if app_data_path:
                for file in ["auth_data.txt", "user_data.txt"]:
                    file_path = os.path.join(app_data_path, file)
                    if os.path.exists(file_path):
                        os.remove(file_path)
            if page:
                page.client_storage.clear()
                logger.info("client_storage limpo.")
            logger.info("Logout realizado com sucesso.")
        except Exception as e:
            logger.error("Erro ao fazer logout: %s", str(e))
            raise


class AnthropicService:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.base_url = "https://api.anthropic.com/v1/messages"
        logger.info(f"AnthropicService initialized with base_url: {self.base_url}")

    def get_workout_plan(self, user_data: dict):
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        prompt = f"""
        Crie um plano de treino personalizado com base nos seguintes dados do usuário:
        - Nível: {user_data.get('level', 'iniciante')}
        - Objetivo: {user_data.get('goal', 'melhorar saúde')}
        - Peso: {user_data.get('weight', 'N/A')} kg
        - Altura: {user_data.get('height', 'N/A')} cm
        - Idade: {user_data.get('age', 'N/A')} anos

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
            return result.get("content", [{}])[0].get("text", "Nenhum plano gerado.")
        except Exception as e:
            logger.error(f"Erro ao gerar plano de treino com Anthropic: {str(e)}")
            raise e

    def answer_question(self, question: str, history: list) -> str:
        """
        Envia à API Claude-3 um prompt customizado para o treinador,
        mantendo tom amigável, descontraído e profissional.
        """
        try:
            system = (
                "Você é um treinador virtual: amigável, casual, profissional e com bom humor. "
                "Responda de forma clara, motivadora e leve."
            )
            msgs = [{"role": "system", "content": system}]
            for item in history:
                msgs.append({"role": "user", "content": item["question"]})
                msgs.append({"role": "assistant", "content": item["answer"]})
            msgs.append({"role": "user", "content": question})

            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            data = {
                "model": "claude-3-5-sonnet-latest",
                "messages": msgs,
                "max_tokens": 1000,
                "temperature": 0.7,
            }
            res = requests.post(self.base_url, headers=headers, json=data)
            res.raise_for_status()
            rj = res.json()
            return rj.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Erro ao obter resposta do Anthropic: {str(e)}")
            return "Desculpe, não consegui responder agora. 😕"

    def is_sensitive_question(self, question: str) -> bool:
        """
        Verifica se a pergunta contém conteúdo sensível ou inadequado usando o Claude.
        Retorna True se for sensível, False caso contrário.
        """
        try:
            moderation_prompt = f"""Determine if the following question is sensitive or inappropriate. 
            If it is, respond with 'sensitive', otherwise respond with 'safe'.

            Question: {question}

            Response:"""
            payload = {
                "model": "claude-3-5-sonnet-latest",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": moderation_prompt}],
            }
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            }
            response = httpx.post(
                self.base_url, json=payload, headers=headers, timeout=30
            )
            response.raise_for_status()
            data = response.json()
            if "content" in data and isinstance(data["content"], list):
                text = data["content"][0].get("text", "").strip()
                return text.lower() == "sensitive"
            return False
        except Exception as e:
            logger.error(f"Error checking sensitive question: {str(e)}")
            return False
