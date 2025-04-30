import os
import json
import logging
from supabase import create_client, Client
from dotenv import load_dotenv
import requests

logger = logging.getLogger("services.services")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class SupabaseService:
    def __init__(self):
        load_dotenv()
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        self.client: Client = create_client(self.url, self.key)
        logger.info("Supabase client inicializado com sucesso.")

        # Carregar e configurar a sessão automaticamente
        self.load_auth_data()
        self.auth_data = self.load_auth_data() or {}
        if self.auth_data.get("access_token") and self.auth_data.get("refresh_token"):
            self.client.auth.set_session(
                self.auth_data["access_token"], self.auth_data["refresh_token"]
            )
            logger.info("Sessão configurada automaticamente com base em auth_data.txt.")

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
            self.save_auth_data(auth_data)
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
            logger.error(f"Erro ao criar perfil: {str(e)}")
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

    async def logout(self):
        try:
            self.client.auth.sign_out()
            if os.path.exists(self.auth_data_path):
                os.remove(self.auth_data_path)
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
