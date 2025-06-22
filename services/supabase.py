import os
import flet as ft
from supabase import create_client, Client
from dotenv import load_dotenv
from utils.logger import get_logger
from utils.alerts import CustomSnackBar, CustomAlertDialog

logger = get_logger("services.supabase")


class SupabaseService:
    """Versão melhorada do serviço Supabase com autenticação simplificada."""

    _instance = None

    @classmethod
    def get_instance(cls, page: ft.Page = None):
        if cls._instance is None:
            cls._instance = cls(page)
        elif page is not None:
            cls._instance.page = page
        return cls._instance

    def __init__(self, page: ft.Page = None):
        if self._instance is not None:
            raise Exception(
                "Use get_instance() para obter a instância do SupabaseService"
            )
        load_dotenv()
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        self.client: Client = create_client(self.url, self.key)
        self.page = page
        logger.info("Cliente Supabase inicializado com sucesso.")
        if page:
            self._restore_session()

    def _restore_session(self) -> None:
        """Restaura a sessão do Supabase a partir do client_storage."""
        if not self.page:
            logger.warning("Página não fornecida. Ignorando restauração de sessão.")
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
                    logger.warning("Sessão inválida ou expirada. Tentando renovar.")
                    if self.refresh_session():
                        logger.info("Sessão renovada com sucesso.")
                    else:
                        self._clear_session()
                        self._safe_show_snackbar(
                            "Sessão expirada. Faça login novamente."
                        )
            else:
                logger.info("Nenhum token de sessão encontrado.")
                self._clear_session()
        except Exception as e:
            if "Invalid Refresh Token" in str(e):
                logger.warning("Token de atualização inválido. Limpando sessão.")
                self._clear_session()
                self._safe_show_snackbar("Sessão expirada. Faça login novamente.")
            else:
                logger.error(f"Erro ao restaurar sessão: {str(e)}")
                self._clear_session()
                self._safe_show_snackbar(f"Erro ao restaurar sessão: {str(e)}")

    def _safe_show_snackbar(self, message: str) -> None:
        """Exibe snackbar apenas se a página estiver pronta."""
        if (
            self.page
            and hasattr(self.page, "overlay")
            and self.page.overlay is not None
        ):
            try:
                snackbar = CustomSnackBar(message=message, bgcolor=ft.Colors.RED_700)
                snackbar.show(self.page)
            except Exception as e:
                logger.error(f"Erro ao exibir snackbar: {str(e)}")
        else:
            logger.warning("Página não pronta para exibir snackbar.")

    def _update_client_storage(self, response) -> None:
        """Atualiza dados de autenticação no client_storage."""
        if not self.page or not response.session:
            return
        try:
            session = response.session
            user = response.user
            self.page.client_storage.set("supafit.access_token", session.access_token)
            self.page.client_storage.set("supafit.refresh_token", session.refresh_token)
            self.page.client_storage.set("supafit.user_id", user.id)
            self.page.client_storage.set("supafit.email", user.email)
            self._check_and_save_user(user.id)
            logger.info(f"Client storage atualizado para user: {user.email}")
        except Exception as e:
            logger.error(f"Erro ao atualizar client_storage: {str(e)}")
            self._safe_show_snackbar(f"Erro ao atualizar armazenamento: {str(e)}")

    def _check_and_save_user(self, user_id: str) -> None:
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
                logger.info(f"Perfil encontrado - nível: {level}")
            else:
                logger.info("Perfil não encontrado - necessário criar perfil")
        except Exception as e:
            logger.error(f"Erro ao verificar perfil: {str(e)}")
            self._safe_show_snackbar(f"Erro ao verificar perfil: {str(e)}")

    def _clear_session(self) -> None:
        """Limpa dados de sessão no Supabase."""
        try:
            self.client.auth.sign_out()
            if self.page:
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
            logger.info("Sessão concluída com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao concluir sessão: {str(e)}")
            self._safe_show_snackbar(f"Erro ao limpar sessão: {str(e)}")

    def get_current_user(self) -> str:
        """Retorna o usuário atual autenticado."""
        try:
            user = self.client.auth.get_user()
            return user.user if user else None
        except Exception as e:
            logger.error(f"Erro ao obter usuário atual: {str(e)}")
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
                if stored_user_id == user.id:
                    return True
                self._restore_session()
                user = self.get_current_user()
                return stored_user_id == user.id if user else False
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar autenticação: {str(e)}")
            self._safe_show_snackbar(f"Erro ao verificar autenticação: {str(e)}")
            return False

    def login(self, email: str, password: str):
        """Realiza login com email e senha."""
        logger.info(f"Tentando login para: {email}")
        try:
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
            logger.error(f"Erro no login: {str(e)}")
            self._safe_show_snackbar(f"Erro no login: {str(e)}")
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
                self._safe_show_snackbar("Falha ao renovar sessão.")
                return False
        except Exception as e:
            logger.error(f"Erro ao renovar sessão: {str(e)}")
            self._clear_session()
            self._safe_show_snackbar(f"Erro ao renovar sessão: {str(e)}")
            return False

    def logout(self):
        """Realiza logout do usuário."""
        try:
            self._clear_session()
            if self.page:
                snackbar = CustomSnackBar(
                    message="Logout realizado com sucesso!", bgcolor=ft.Colors.GREEN_700
                )
                snackbar.show(self.page)
                self.page.go("/login")
            logger.info("Logout concluído com sucesso.")
        except Exception as e:
            logger.error(f"Erro no logout: {str(e)}")
            self._safe_show_snackbar(f"Erro ao realizar logout: {str(e)}")
            raise

    def create_profile(self, user_id: str, profile_data: dict):
        """Cria perfil do usuário."""
        logger.info(f"Criando perfil para user_id: {user_id}")
        try:
            profile_data["user_id"] = user_id
            response = self.client.table("user_profiles").insert(profile_data).execute()
            if self.page:
                self.page.client_storage.set("supafit.profile_created", True)
                self.page.client_storage.set(
                    "supafit.level", profile_data.get("level", "iniciante")
                )
            logger.info("Perfil criado com sucesso.")
            return response.data
        except Exception as e:
            logger.error(f"Erro ao criar perfil: {str(e)}")
            self._safe_show_snackbar(f"Erro ao criar perfil: {str(e)}")
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
            logger.error(f"Erro ao recuperar perfil: {str(e)}")
            self._safe_show_snackbar(f"Erro ao recuperar perfil: {str(e)}")
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
            logger.error(f"Erro ao recuperar treinos: {str(e)}")
            self._safe_show_snackbar(f"Erro ao recuperar treinos: {str(e)}")
            raise
