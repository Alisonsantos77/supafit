import os
import json
import httpx
import requests
from supabase import create_client, Client
from dotenv import load_dotenv
import flet as ft
from utils.logger import get_logger

logger = get_logger("supabafit.services")


class SupabaseService:
    """Classe de serviço para gerenciar autenticação e operações de dados com Supabase."""

    def __init__(self, page: ft.Page = None):
        """Inicializa o cliente Supabase com gerenciamento de autenticação e sessão.

        Args:
            page (ft.Page, optional): Instância da página Flet para acesso ao armazenamento do cliente.
        """
        load_dotenv()
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        self.client: Client = create_client(self.url, self.key)
        self.page = page
        logger.info("Cliente Supabase inicializado com sucesso.")

        # Carrega e configura a sessão automaticamente
        self.auth_data = self.load_auth_data() or {}
        if self.auth_data.get("access_token") and self.auth_data.get("refresh_token"):
            try:
                response = self.client.auth.set_session(
                    self.auth_data["access_token"], self.auth_data["refresh_token"]
                )
                if response.session:
                    self.auth_data.update(
                        {
                            "access_token": response.session.access_token,
                            "refresh_token": response.session.refresh_token,
                            "user_id": response.user.id,
                            "email": response.user.email,
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
                        self.page.client_storage.set(
                            "supafit.user_id", response.user.id
                        )
                        self.page.client_storage.set(
                            "supafit.email", response.user.email
                        )
                        # Verificar perfil no banco
                        profile_response = self.get_profile(response.user.id)
                        profile_created = bool(
                            profile_response.data and len(profile_response.data) > 0
                        )
                        self.page.client_storage.set(
                            "supafit.profile_created", profile_created
                        )
                        if profile_created:
                            self.page.client_storage.set(
                                "supafit.level",
                                profile_response.data[0].get("level", "iniciante"),
                            )
                        logger.info(
                            f"Perfil {'encontrado' if profile_created else 'não encontrado'} para user_id: {response.user.id}, definido profile_created como {profile_created}."
                        )
                    logger.info("Sessão configurada e tokens atualizados com sucesso.")
                else:
                    logger.warning(
                        "Nenhuma sessão retornada durante configuração de tokens."
                    )
                    self.handle_invalid_token()
            except Exception as e:
                logger.error(f"Falha ao configurar sessão: {str(e)}")
                if "Invalid Refresh Token" in str(e):
                    self.handle_invalid_token()
                else:
                    self.auth_data = {}
                    self.save_auth_data({})
                    if self.page:
                        self.page.client_storage.clear()
                        self.page.go("/login")
                    raise
        else:
            logger.info(
                "Nenhum token de autenticação encontrado; sessão não configurada."
            )

    def handle_invalid_token(self):
        """Trata tokens inválidos limpando dados de autenticação e redirecionando para login."""
        logger.warning("Token de atualização inválido detectado. Limpando sessão.")
        try:
            self.client.auth.sign_out()
            app_data_path = os.getenv("FLET_APP_STORAGE_DATA")
            if app_data_path:
                for file in ["auth_data.txt", "user_data.txt"]:
                    file_path = os.path.join(app_data_path, file)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(
                            f"Arquivo {file} removido durante limpeza de sessão."
                        )
            if self.page:
                self.page.client_storage.clear()
                logger.info("Armazenamento do cliente limpo durante limpeza de sessão.")
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Sessão inválida. Faça login novamente."),
                    bgcolor=ft.Colors.RED_700,
                )
                self.page.snack_bar.open = True
                self.page.go("/login")
                self.page.update()
        except Exception as e:
            logger.error(f"Falha ao limpar sessão: {str(e)}")

    def refresh_session(self) -> bool:
        """Tenta renovar a sessão do Supabase usando o token de atualização.

        Returns:
            bool: True se a renovação da sessão for bem-sucedida, False caso contrário.
        """
        try:
            if not self.auth_data.get("refresh_token"):
                logger.warning(
                    "Nenhum token de atualização disponível para renovação de sessão."
                )
                self.handle_invalid_token()
                return False

            session = self.client.auth.refresh_session()
            if session and hasattr(session, "session") and session.session:
                self.auth_data.update(
                    {
                        "access_token": session.session.access_token,
                        "refresh_token": session.session.refresh_token,
                        "user_id": session.user.id,
                        "email": session.user.email,
                    }
                )
                self.save_auth_data(self.auth_data)
                if self.page:
                    self.page.client_storage.set(
                        "supafit.access_token", session.session.access_token
                    )
                    self.page.client_storage.set(
                        "supafit.refresh_token", session.session.refresh_token
                    )
                    self.page.client_storage.set("supafit.user_id", session.user.id)
                    self.page.client_storage.set("supafit.email", session.user.email)
                logger.info("Sessão renovada com sucesso.")
                return True
            else:
                logger.error(
                    "Falha na renovação da sessão: sessão inválida ou incompleta."
                )
                self.handle_invalid_token()
                return False
        except Exception as e:
            logger.error(f"Falha na renovação da sessão: {str(e)}")
            if "Invalid Refresh Token" in str(e):
                self.handle_invalid_token()
            return False

    def load_auth_data(self) -> dict:
        """Carrega dados de autenticação do arquivo auth_data.txt.

        Returns:
            dict: Dados de autenticação se carregados com sucesso, None caso contrário.
        """
        app_data_path = os.getenv("FLET_APP_STORAGE_DATA")
        if not app_data_path:
            logger.warning(
                "FLET_APP_STORAGE_DATA não definido; incapaz de carregar auth_data.txt."
            )
            return None

        file_path = os.path.join(app_data_path, "auth_data.txt")
        try:
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    data = json.load(f)
                logger.info(
                    "Dados de autenticação carregados com sucesso de auth_data.txt."
                )
                return data
            else:
                logger.warning(f"auth_data.txt não encontrado em {file_path}.")
                return None
        except Exception as e:
            logger.error(f"Falha ao carregar auth_data.txt: {str(e)}")
            return None

    def save_auth_data(self, auth_data: dict):
        """Salva dados de autenticação no arquivo auth_data.txt.

        Args:
            auth_data (dict): Dados de autenticação a serem salvos.
        """
        app_data_path = os.getenv("FLET_APP_STORAGE_DATA")
        if not app_data_path:
            logger.warning(
                "FLET_APP_STORAGE_DATA não definido; incapaz de salvar auth_data.txt."
            )
            return

        file_path = os.path.join(app_data_path, "auth_data.txt")
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(
                    "auth_data.txt anterior removido antes de salvar novos dados."
                )
            with open(file_path, "w") as f:
                json.dump(auth_data, f, indent=4)
            logger.info(f"Dados de autenticação salvos com sucesso em {file_path}.")
        except Exception as e:
            logger.error(f"Falha ao salvar auth_data.txt: {str(e)}")

    def login(self, email: str, password: str):
        """Realiza login do usuário e configura a sessão.

        Args:
            email (str): Email do usuário.
            password (str): Senha do usuário.

        Returns:
            Objeto de resposta do Supabase Auth.

        Raises:
            Exception: Se o login falhar ou nenhum usuário for retornado.
        """
        logger.info(f"Tentando login para o email: {email}")
        try:
            # Limpa dados residuais antes do login
            app_data_path = os.getenv("FLET_APP_STORAGE_DATA")
            if app_data_path:
                for file in ["auth_data.txt", "user_data.txt"]:
                    file_path = os.path.join(app_data_path, file)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"Arquivo {file} removido antes do login.")
            if self.page:
                self.page.client_storage.clear()
                logger.info("Armazenamento do cliente limpo antes do login.")

            response = self.client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            if response.user:
                logger.info("Login bem-sucedido.")
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
                if self.page:
                    self.page.client_storage.set(
                        "supafit.access_token", response.session.access_token
                    )
                    self.page.client_storage.set(
                        "supafit.refresh_token", response.session.refresh_token
                    )
                    self.page.client_storage.set("supafit.user_id", response.user.id)
                    self.page.client_storage.set("supafit.email", response.user.email)
                    profile_response = self.get_profile(response.user.id)
                    profile_exists = bool(
                        profile_response.data and len(profile_response.data) > 0
                    )
                    self.page.client_storage.set(
                        "supafit.profile_created", profile_exists
                    )
                    if profile_exists:
                        self.page.client_storage.set(
                            "supafit.level",
                            profile_response.data[0].get("level", "iniciante"),
                        )
                    logger.info(
                        f"Perfil {'encontrado' if profile_exists else 'não encontrado'} para user_id: {response.user.id}, definido profile_created como {profile_exists}."
                    )
                self.auth_data = auth_data
                self.client.auth.set_session(
                    response.session.access_token, response.session.refresh_token
                )
                logger.info("Sessão configurada com sucesso após login.")
                return response
            else:
                logger.error("Falha no login: nenhum usuário retornado.")
                raise Exception("Falha no login: nenhum usuário retornado.")
        except Exception as e:
            logger.error(f"Falha no login: {str(e)}")
            raise

    def validate_user_id(self, user_id: str, is_new_user: bool = False) -> None:
        """Valida se o user_id corresponde aos dados de autenticação armazenados.

        Args:
            user_id (str): ID do usuário a validar.
            is_new_user (bool, optional): Se True, ignora validação para novos usuários.

        Raises:
            ValueError: Se a validação do user_id falhar.
        """
        if is_new_user:
            logger.info(
                f"Usuário novo detectado; ignorando validação de user_id para {user_id}."
            )
            return

        try:
            user = self.client.auth.get_user()
            if not user or not user.user or user.user.id != user_id:
                logger.error(
                    f"Validação de user_id falhou: esperado {user_id}, recebido {user.user.id if user and user.user else 'Nenhum'}."
                )
                raise ValueError(
                    "ID do usuário inválido ou não corresponde aos dados do Supabase."
                )
            logger.info(f"Validação de user_id bem-sucedida para {user_id}.")
        except Exception as e:
            logger.error(f"Erro ao validar user_id: {str(e)}")
            self.handle_invalid_token()
            raise ValueError("ID do usuário inválido ou sessão expirada.")

    def create_profile(self, user_id: str, profile_data: dict):
        """Cria um perfil de usuário na tabela user_profiles.

        Args:
            user_id (str): ID do usuário.
            profile_data (dict): Dados do perfil a inserir.

        Returns:
            Dados de resposta do Supabase.

        Raises:
            Exception: Se a criação do perfil falhar.
        """
        logger.info(f"Criando perfil para user_id: {user_id}")
        try:
            response = self.client.table("user_profiles").insert(profile_data).execute()
            logger.info("Perfil criado com sucesso.")
            return response.data
        except Exception as e:
            logger.error(f"Falha ao criar perfil para user_id {user_id}: {str(e)}")
            if "permission denied" in str(e).lower():
                logger.error(
                    "Permissão negada para inserção em user_profiles. Verifique políticas RLS."
                )
            raise e

    def get_profile(self, user_id: str):
        """Recupera o perfil do usuário da tabela user_profiles.

        Args:
            user_id (str): ID do usuário.

        Returns:
            Objeto de resposta do Supabase.

        Raises:
            Exception: Se a recuperação do perfil falhar.
        """
        logger.info(f"Recuperando perfil para user_id: {user_id}")
        try:
            response = (
                self.client.table("user_profiles")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )
            logger.info("Perfil recuperado com sucesso.")
            return response
        except Exception as e:
            logger.error(f"Falha ao recuperar perfil para user_id {user_id}: {str(e)}")
            raise

    def get_workouts(self, user_id: str):
        """Recupera treinos do usuário da tabela daily_workouts.

        Args:
            user_id (str): ID do usuário.

        Returns:
            Objeto de resposta do Supabase.

        Raises:
            Exception: Se a recuperação dos treinos falhar.
        """
        logger.info(f"Recuperando treinos para user_id: {user_id}")
        try:
            response = (
                self.client.table("daily_workouts")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )
            if response.data:
                logger.info("Treinos recuperados com sucesso.")
            else:
                logger.info(f"Nenhum treino encontrado para user_id: {user_id}.")
            return response
        except Exception as e:
            logger.error(f"Falha ao recuperar treinos para user_id {user_id}: {str(e)}")
            raise

    async def logout(self, page: ft.Page = None):
        """Realiza logout do usuário e limpa dados de autenticação.

        Args:
            page (ft.Page, optional): Instância da página Flet para acesso ao sistema.

        Raises:
            Exception: Se o logout falhar.
        """
        try:
            self.client.auth.sign_out()
            logger.info("Sign-out realizado no Supabase.")
            app_data_path = os.getenv("FLET_APP_STORAGE_DATA")
            if app_data_path:
                for file in ["auth_data.txt", "user_data.txt"]:
                    file_path = os.path.join(app_data_path, file)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"Arquivo {file} removido durante o logout.")
            if page:
                page.client_storage.clear()
                logger.info("Armazenamento do cliente limpo durante o logout.")
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Logout realizado com sucesso!"),
                    bgcolor=ft.Colors.GREEN_700,
                )
                page.snack_bar.open = True
                page.go("/login")
                page.update()
            self.auth_data = {}
            logger.info("Logout concluído com sucesso.")
        except Exception as e:
            logger.error(f"Falha no logout: {str(e)}")
            if page:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Erro ao fazer logout. Tente novamente."),
                    bgcolor=ft.Colors.RED_700,
                )
                page.snack_bar.open = True
                page.update()
            raise


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

    def answer_question(
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
            # Monta o payload com histórico + nova pergunta
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
            response = httpx.post(
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
            moderation_prompt = f"""Determine se a seguinte pergunta é sensível ou inadequada.
                Se for, responda com 'sensitive', caso contrário, responda com 'safe'.

                Pergunta: {question}

                Resposta:"""
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
