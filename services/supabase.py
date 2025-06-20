import os
import flet as ft 
from supabase import create_client, Client
from dotenv import load_dotenv
from utils.logger import get_logger

logger = get_logger("services.supabase")

class SupabaseService:
    """Versão melhorada do serviço Supabase com autenticação simplificada."""

    def __init__(self, page: ft.Page = None):
        load_dotenv()
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        self.client: Client = create_client(self.url, self.key)
        self.page = page
        logger.info("Cliente Supabase inicializado com sucesso.")

        # Tentar restaurar sessão automaticamente
        self._restore_session()

    def _restore_session(self):
        """Restaura sessão do client_storage se disponível."""
        if not self.page:
            return

        try:
            access_token = self.page.client_storage.get("supafit.access_token")
            refresh_token = self.page.client_storage.get("supafit.refresh_token")

            if access_token and refresh_token:
                response = self.client.auth.set_session(access_token, refresh_token)
                if response.session:
                    logger.info("Sessão restaurada com sucesso.")
                    self._update_client_storage(response)
                else:
                    logger.warning("Falha ao restaurar sessão.")
                    self._clear_session()
        except Exception as e:
            logger.error(f"Erro ao restaurar sessão: {e}")
            self._clear_session()

    def _update_client_storage(self, auth_response):
        """Atualiza dados de autenticação no client_storage."""
        if not self.page or not auth_response.session:
            return

        try:
            session = auth_response.session
            user = auth_response.user

            # Salvar dados essenciais
            self.page.client_storage.set("supafit.access_token", session.access_token)
            self.page.client_storage.set("supafit.refresh_token", session.refresh_token)
            self.page.client_storage.set("supafit.user_id", user.id)
            self.page.client_storage.set("supafit.email", user.email)

            # Verificar e salvar perfil
            self._check_and_save_profile(user.id)

            logger.info(f"Client storage atualizado para user: {user.email}")
        except Exception as e:
            logger.error(f"Erro ao atualizar client storage: {e}")

    def _check_and_save_profile(self, user_id: str):
        """Verifica e salva informações do perfil no client_storage."""
        try:
            profile_response = self.get_profile(user_id)
            profile_exists = bool(
                profile_response.data and len(profile_response.data) > 0
            )

            self.page.client_storage.set("supafit.profile_created", profile_exists)

            if profile_exists:
                level = profile_response.data[0].get("level", "iniciante")
                self.page.client_storage.set("supafit.level", level)
                logger.info(f"Perfil encontrado - Nível: {level}")
            else:
                logger.info("Perfil não encontrado - redirecionamento necessário")

        except Exception as e:
            logger.error(f"Erro ao verificar perfil: {e}")

    def _clear_session(self):
        """Limpa dados de sessão."""
        try:
            self.client.auth.sign_out()
            if self.page:
                # Limpar apenas dados relacionados à autenticação
                auth_keys = [
                    "supafit.access_token",
                    "supafit.refresh_token",
                    "supafit.user_id",
                    "supafit.email",
                    "supafit.profile_created",
                    "supafit.level",
                ]
                for key in auth_keys:
                    self.page.client_storage.remove(key)
            logger.info("Sessão limpa com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao limpar sessão: {e}")

    def get_current_user(self):
        """Retorna o usuário atual autenticado."""
        try:
            user = self.client.auth.get_user()
            return user.user if user else None
        except Exception as e:
            logger.error(f"Erro ao obter usuário atual: {e}")
            return None

    def is_authenticated(self) -> bool:
        """Verifica se há uma sessão válida."""
        try:
            user = self.get_current_user()
            if user:
                stored_user_id = (
                    self.page.client_storage.get("supafit.user_id")
                    if self.page
                    else None
                )
                return stored_user_id == user.id
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar autenticação: {e}")
            return False

    def login(self, email: str, password: str):
        """Login simplificado."""
        logger.info(f"Tentando login para: {email}")

        try:
            self._clear_session()

            # Fazer login
            response = self.client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            if response.user and response.session:
                self._update_client_storage(response)
                logger.info("Login realizado com sucesso.")
                return response
            else:
                raise Exception("Falha no login: resposta inválida")

        except Exception as e:
            logger.error(f"Erro no login: {e}")
            raise

    def refresh_session(self) -> bool:
        """Renova a sessão atual."""
        try:
            session = self.client.auth.refresh_session()
            if session and session.session:
                self._update_client_storage(session)
                logger.info("Sessão renovada com sucesso.")
                return True
            else:
                logger.warning("Falha ao renovar sessão.")
                self._clear_session()
                return False
        except Exception as e:
            logger.error(f"Erro ao renovar sessão: {e}")
            self._clear_session()
            return False

    def logout(self):
        """Logout simplificado."""
        try:
            self._clear_session()

            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Logout realizado com sucesso!"),
                    bgcolor=ft.Colors.GREEN_700,
                )
                self.page.snack_bar.open = True
                self.page.go("/login")
                self.page.update()

            logger.info("Logout concluído com sucesso.")
        except Exception as e:
            logger.error(f"Erro no logout: {e}")
            raise

    def create_profile(self, user_id: str, profile_data: dict):
        """Cria perfil do usuário."""
        logger.info(f"Criando perfil para user_id: {user_id}")
        try:
            # Garantir que user_id está nos dados
            profile_data["user_id"] = user_id

            response = self.client.table("user_profiles").insert(profile_data).execute()

            # Atualizar client_storage após criar perfil
            if self.page:
                self.page.client_storage.set("supafit.profile_created", True)
                self.page.client_storage.set(
                    "supafit.level", profile_data.get("level", "iniciante")
                )

            logger.info("Perfil criado com sucesso.")
            return response.data
        except Exception as e:
            logger.error(f"Erro ao criar perfil: {e}")
            raise

    def get_profile(self, user_id: str):
        """Recupera perfil do usuário."""
        logger.info(f"Recuperando perfil para user_id: {user_id}")
        try:
            response = (
                self.client.table("user_profiles")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )
            return response
        except Exception as e:
            logger.error(f"Erro ao recuperar perfil: {e}")
            raise

    def get_workouts(self, user_id: str):
        """Recupera treinos do usuário."""
        logger.info(f"Recuperando treinos para user_id: {user_id}")
        try:
            response = (
                self.client.table("daily_workouts")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )
            return response
        except Exception as e:
            logger.error(f"Erro ao recuperar treinos: {e}")
            raise
