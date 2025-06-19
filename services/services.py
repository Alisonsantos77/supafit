import os
import json
import logging
import httpx
import requests
from supabase import create_client, Client
from dotenv import load_dotenv
import flet as ft

logger = logging.getLogger("services.supabase")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class SupabaseService:
    """Classe de serviço para gerenciar autenticação e operações de dados com Supabase."""

    def __init__(self, page: ft.Page = None):
        """
        Inicializa o cliente Supabase com gerenciamento de autenticação e sessão.

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
                    logger.info("Sessão configurada e tokens atualizados com sucesso.")
                else:
                    logger.warning("Nenhuma sessão retornada durante configuração de tokens.")
                    self.handle_invalid_token()
            except Exception as e:
                logger.error(f"Falha ao configurar sessão: {str(e)}")
                if "Invalid Refresh Token" in str(e):
                    self.handle_invalid_token()
                else:
                    self.auth_data = {}
                    self.save_auth_data({})
                    raise
        else:
            logger.info("Nenhum token de autenticação encontrado; sessão não configurada.")

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
                        logger.info(f"Arquivo {file} removido durante limpeza de sessão.")
            if self.page:
                self.page.client_storage.clear()
                logger.info("Armazenamento do cliente limpo durante limpeza de sessão.")
                self.page.go("/login")
        except Exception as e:
            logger.error(f"Falha ao limpar sessão: {str(e)}")

    def refresh_session(self) -> bool:
        """
        Tenta renovar a sessão do Supabase usando o token de atualização.

        Returns:
            bool: True se a renovação da sessão for bem-sucedida, False caso contrário.
        """
        try:
            if not self.auth_data.get("refresh_token"):
                logger.warning("Nenhum token de atualização disponível para renovação de sessão.")
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
                logger.error("Falha na renovação da sessão: nenhuma sessão retornada.")
                return False
        except Exception as e:
            logger.error(f"Falha na renovação da sessão: {str(e)}")
            if "Invalid Refresh Token" in str(e):
                self.handle_invalid_token()
            return False

    def load_auth_data(self) -> dict:
        """
        Carrega dados de autenticação do arquivo auth_data.txt.

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
        """
        Salva dados de autenticação no arquivo auth_data.txt.

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
            with open(file_path, "w") as f:
                json.dump(auth_data, f, indent=4)
            logger.info(f"Dados de autenticação salvos com sucesso em {file_path}.")
        except Exception as e:
            logger.error(f"Falha ao salvar auth_data.txt: {str(e)}")

    def login(self, email: str, password: str):
        """
        Realiza login do usuário e configura a sessão.

        Args:
            email (str): Email do usuário.
            password (str): Senha do usuário.

        Returns:
            Objeto de resposta do Supabase Auth.

        Raises:
            Exception: Se o login falhar ou nenhum usuário for retornado.
        """
        logger.info(f"Tentando login para o email: {email}")
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
            app_data_path = os.getenv("FLET_APP_STORAGE_DATA")
            if app_data_path:
                file_path = os.path.join(app_data_path, "auth_data.txt")
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(
                        "auth_data.txt anterior removido antes de salvar novos dados."
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
                # Verificar se o perfil existe no banco
                profile_response = self.get_profile(response.user.id)
                if profile_response.data and len(profile_response.data) > 0: 
                    self.page.client_storage.set("supafit.profile_created", True)
                    logger.info(
                        f"Perfil encontrado para user_id: {response.user.id}, definido profile_created como True."
                    )
                else:
                    self.page.client_storage.set("supafit.profile_created", False)
                    logger.info(
                        f"Nenhum perfil encontrado para user_id: {response.user.id}, definido profile_created como False."
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

    def validate_user_id(self, user_id: str, is_new_user: bool = False) -> bool:
        """
        Valida se o user_id corresponde aos dados de autenticação armazenados.

        Args:
            user_id (str): ID do usuário a validar.
            is_new_user (bool, optional): Se True, ignora validação para novos usuários.

        Returns:
            bool: True se a validação passar, False caso contrário.
        """
        if is_new_user:
            logger.info(
                f"Usuário novo detectado; ignorando validação de user_id para {user_id}."
            )
            return True

        stored_auth_data = self.load_auth_data()
        if not stored_auth_data:
            logger.warning("Nenhum dado de autenticação encontrado para validação de user_id.")
            return False

        stored_user_id = stored_auth_data.get("user_id")
        if stored_user_id != user_id:
            logger.error(
                f"Validação de user_id falhou: esperado {stored_user_id}, recebido {user_id}."
            )
            return False

        logger.info(f"Validação de user_id bem-sucedida para {user_id}.")
        return True

    def create_profile(self, user_id: str, profile_data: dict):
        """
        Cria um perfil de usuário na tabela user_profiles.

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
        """
        Recupera o perfil do usuário da tabela user_profiles.

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

    async def logout(self, page: ft.Page = None):
            """
            Realiza logout do usuário e limpa dados de autenticação.

            Args:
                page (ft.Page, optional): Instância da página Flet para acesso ao armazenamento do cliente.

            Raises:
                Exception: Se o logout falhar.
            """
            try:
                await self.client.auth.sign_out()  # Alterado para await
                app_data_path = os.getenv("FLET_APP_STORAGE_DATA")
                if app_data_path:
                    for file in ["auth_data.txt", "user_data.txt"]:
                        file_path = os.path.join(app_data_path, file)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            logger.info(f"Arquivo {file} removido durante logout.")
                if page:
                    page.client_storage.clear()
                    logger.info("Armazenamento do cliente limpo durante logout.")
                logger.info("Logout concluído com sucesso.")
            except Exception as e:
                logger.error(f"Falha no logout: {str(e)}")
                raise

class AnthropicService:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.base_url = "https://api.anthropic.com/v1/messages"
        logger.info(f"Serviço Anthropic inicializado com base_url: {self.base_url}")

    def get_workout_plan(self, user_data: dict):
        """
        Gera um plano de treino personalizado com base nos dados do usuário.

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
        Envia a pergunta e o histórico para a API da Anthropic e retorna o texto da resposta.
        Usa modelo 'claude-3-5-sonnet-latest' para maior qualidade.

        Args:
            question (str): Pergunta do usuário.
            history (list): Histórico de perguntas e respostas.

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
                messages.append({"role": "user", "content": item.get("question", "")})
                messages.append({"role": "assistant", "content": item.get("answer", "")})
            messages.append({"role": "user", "content": question})

            payload = {
                "model": "claude-3-5-sonnet-latest",
                "max_tokens": 1000,
                "temperature": 0.7,
                "messages": messages,
            }
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
                "API Anthropic retornou status %s: %s",
                ex.response.status_code,
                error_text,
            )
            raise
        except Exception as ex:
            logger.error(f"Erro inesperado em answer_question: {ex}")
            return "Desculpe, não consegui responder agora."


    def is_sensitive_question(self, question: str) -> bool:
        """
        Verifica se a pergunta contém conteúdo sensível ou inadequado usando o Claude.

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
            response = httpx.post(self.base_url, json=payload, headers=headers, timeout=30)
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
