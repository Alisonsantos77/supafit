import os
import flet as ft
from supabase import create_client, Client
from dotenv import load_dotenv
from utils.alerts import CustomSnackBar, CustomAlertDialog


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
        print("INFO: Cliente Supabase inicializado com sucesso.")
        if page:
            self._restore_session()

    def _restore_session(self) -> None:
        """Restaura a sessão do Supabase a partir do client_storage."""
        if not self.page:
            print("WARNING: Página não fornecida. Ignorando restauração de sessão.")
            return
        try:
            access_token = self.page.client_storage.get("supafit.access_token")
            refresh_token = self.page.client_storage.get("supafit.refresh_token")
            if access_token and refresh_token:
                response = self.client.auth.set_session(access_token, refresh_token)
                if response.session:
                    print("INFO: Sessão restaurada com sucesso.")
                    self._update_client_storage(response)
                else:
                    print("WARNING: Sessão inválida ou expirada. Tentando renovar.")
                    if self.refresh_session():
                        print("INFO: Sessão renovada com sucesso.")
                    else:
                        self._clear_session()
                        self._safe_show_snackbar(
                            "Sessão expirada. Faça login novamente."
                        )
            else:
                print("INFO: Nenhum token de sessão encontrado.")
                self._clear_session()
        except Exception as e:
            if "Invalid Refresh Token" in str(e):
                print("WARNING: Token de atualização inválido. Limpando sessão.")
                self._clear_session()
                self._safe_show_snackbar("Sessão expirada. Faça login novamente.")
            else:
                print(f"ERROR: Erro ao restaurar sessão: {str(e)}")
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
                print(f"ERROR: Erro ao exibir snackbar: {str(e)}")
        else:
            print("WARNING: Página não pronta para exibir snackbar.")

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
            print(f"INFO: Client storage atualizado para user: {user.email}")
        except Exception as e:
            print(f"ERROR: Erro ao atualizar client_storage: {str(e)}")
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
                print(f"INFO: Perfil encontrado - nível: {level}")
            else:
                print("INFO: Perfil não encontrado - necessário criar perfil")
        except Exception as e:
            print(f"ERROR: Erro ao verificar perfil: {str(e)}")
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
            print("INFO: Sessão concluída com sucesso.")
        except Exception as e:
            print(f"ERROR: Erro ao concluir sessão: {str(e)}")

    def get_current_user(self) -> str:
        """Retorna o usuário atual autenticado."""
        try:
            user = self.client.auth.get_user()
            return user.user if user else None
        except Exception as e:
            print(f"ERROR: Erro ao obter usuário atual: {str(e)}")
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
            print(f"ERROR: Erro ao verificar autenticação: {str(e)}")
            self._safe_show_snackbar(f"Erro ao verificar autenticação: {str(e)}")
            return False

    def login(self, email: str, password: str):
        """Realiza login com email e senha."""
        print(f"INFO: Tentando login para: {email}")
        try:
            response = self.client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            if response.user and response.session:
                self._update_client_storage(response)
                print("INFO: Login realizado com sucesso.")
                return response
            else:
                raise Exception("Falha no login: resposta inválida")
        except Exception as e:
            print(f"ERROR: Erro no login: {str(e)}")
            self._safe_show_snackbar(f"Erro no login: {str(e)}")
            raise

    def refresh_session(self) -> bool:
        """Renova a sessão atual."""
        try:
            session = self.client.auth.refresh_session()
            if session and session.session:
                self._update_client_storage(session)
                print("INFO: Sessão renovada com sucesso.")
                return True
            else:
                print("WARNING: Falha ao renovar sessão.")
                self._clear_session()
                self._safe_show_snackbar("Falha ao renovar sessão.")
                return False
        except Exception as e:
            print(f"ERROR: Erro ao renovar sessão: {str(e)}")
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
            print("INFO: Logout concluído com sucesso.")
        except Exception as e:
            print(f"ERROR: Erro no logout: {str(e)}")
            self._safe_show_snackbar(f"Erro ao realizar logout: {str(e)}")
            raise

    def create_profile(self, user_id: str, profile_data: dict):
        """Cria perfil do usuário."""
        print(f"INFO: Criando perfil para user_id: {user_id}")
        try:
            profile_data["user_id"] = user_id
            response = self.client.table("user_profiles").insert(profile_data).execute()
            if self.page:
                self.page.client_storage.set("supafit.profile_created", True)
                self.page.client_storage.set(
                    "supafit.level", profile_data.get("level", "iniciante")
                )
            print("INFO: Perfil criado com sucesso.")
            return response.data
        except Exception as e:
            print(f"ERROR: Erro ao criar perfil: {str(e)}")
            self._safe_show_snackbar(f"Erro ao criar perfil: {str(e)}")
            raise

    def get_profile(self, user_id: str):
        """Recupera perfil do usuário."""
        print(f"INFO: Recuperando perfil para user_id: {user_id}")
        try:
            response = (
                self.client.table("user_profiles")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )
            return response
        except Exception as e:
            print(f"ERROR: Erro ao recuperar perfil: {str(e)}")
            self._safe_show_snackbar(f"Erro ao recuperar perfil: {str(e)}")
            raise

    def get_workouts(self, user_id: str):
        """Recupera treinos do usuário."""
        print(f"INFO: Recuperando treinos para user_id: {user_id}")
        try:
            response = (
                self.client.table("daily_workouts")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )
            return response
        except Exception as e:
            print(f"ERROR: Erro ao recuperar treinos: {str(e)}")
            self._safe_show_snackbar(f"Erro ao recuperar treinos: {str(e)}")
            raise

    def get_all_exercises(self):
        """Recupera todos os exercícios disponíveis."""
        print("INFO: Recuperando todos os exercícios")
        try:
            response = self.client.table("exercicios").select("*").execute()
            print(f"INFO: {len(response.data)} exercícios recuperados")
            return response.data
        except Exception as e:
            print(f"ERROR: Erro ao recuperar exercícios: {str(e)}")
            self._safe_show_snackbar(f"Erro ao recuperar exercícios: {str(e)}")
            raise

    def create_user_plan(self, plan_data: dict):
        """Cria um plano de treino do usuário."""
        print(f"INFO: Criando plano de treino: {plan_data.get('title', 'Sem título')}")
        try:
            response = self.client.table("user_plans").insert(plan_data).execute()
            print("INFO: Plano de treino criado com sucesso.")
            return response.data
        except Exception as e:
            print(f"ERROR: Erro ao criar plano de treino: {str(e)}")
            self._safe_show_snackbar(f"Erro ao criar plano de treino: {str(e)}")
            raise

    def create_plan_exercise(self, exercise_data: dict):
        """Cria um exercício do plano."""
        print(f"INFO: Criando exercício do plano: {exercise_data.get('exercise_id')}")
        try:
            response = (
                self.client.table("plan_exercises").insert(exercise_data).execute()
            )
            print("INFO: Exercício do plano criado com sucesso.")
            return response.data
        except Exception as e:
            print(f"ERROR: Erro ao criar exercício do plano: {str(e)}")
            self._safe_show_snackbar(f"Erro ao criar exercício do plano: {str(e)}")
            raise

    def get_user_plans(self, user_id: str):
        """Recupera planos de treino do usuário."""
        print(f"INFO: Recuperando planos de treino para user_id: {user_id}")
        try:
            response = (
                self.client.table("user_plans")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )
            return response
        except Exception as e:
            print(f"ERROR: Erro ao recuperar planos de treino: {str(e)}")
            self._safe_show_snackbar(f"Erro ao recuperar planos de treino: {str(e)}")
            raise

    def get_plan_exercises(self, plan_id: str):
        """Recupera exercícios de um plano específico."""
        print(f"INFO: Recuperando exercícios do plano: {plan_id}")
        try:
            response = (
                self.client.table("plan_exercises")
                .select("*, exercicios(*)")
                .eq("plan_id", plan_id)
                .order("order")
                .execute()
            )
            return response
        except Exception as e:
            print(f"ERROR: Erro ao recuperar exercícios do plano: {str(e)}")
            self._safe_show_snackbar(f"Erro ao recuperar exercícios do plano: {str(e)}")
            raise

    def save_exercise_progress(
        self, user_id: str, plan_id: str, exercise_id: str, load: float
    ):
        """Salva ou atualiza o progresso de carga de um exercício."""
        print(
            f"INFO: Salvando progresso - user_id: {user_id}, plan_id: {plan_id}, exercise_id: {exercise_id}, load: {load}kg"
        )
        try:
            # Validação dos parâmetros
            if not user_id:
                raise ValueError("user_id é obrigatório")
            if not exercise_id:
                raise ValueError("exercise_id é obrigatório")
            if load < 0:
                raise ValueError("load não pode ser negativo")

            # Primeiro, verifica se já existe um registro para este exercício
            existing_response = (
                self.client.table("progress")
                .select("id")
                .eq("user_id", user_id)
                .eq("exercise_id", exercise_id)
                .order("recorded_at", desc=True)
                .limit(1)
                .execute()
            )

            progress_data = {
                "user_id": user_id,
                "exercise_id": exercise_id,
                "load": float(load),
            }

            # Adiciona plan_id apenas se fornecido
            if plan_id:
                progress_data["plan_id"] = plan_id

            print(f"INFO: Dados a serem processados: {progress_data}")

            # Se existe um registro, atualiza. Senão, insere novo
            if existing_response.data and len(existing_response.data) > 0:
                # Atualiza o registro mais recente
                existing_id = existing_response.data[0]["id"]
                print(f"INFO: Atualizando registro existente: {existing_id}")

                response = (
                self.client.table("progress")
                .update({"load": float(load)})
                .eq("id", existing_id)
                .execute()
            )
            else:
                # Insere novo registro
                print("INFO: Inserindo novo registro")
                response = self.client.table("progress").insert(progress_data).execute()

            if response.data:
                print(f"INFO: Progresso salvo com sucesso: {response.data}")
                return response.data
            else:
                print("WARNING: Resposta vazia do banco de dados")
                return None

        except Exception as e:
            print(f"ERROR: Erro ao salvar progresso: {str(e)}")
            print(f"ERROR: Tipo do erro: {type(e)}")
            if hasattr(e, "details"):
                print(f"ERROR: Detalhes do erro: {e.details}")
            self._safe_show_snackbar(f"Erro ao salvar progresso: {str(e)}")
            raise

    def get_latest_exercise_load(self, user_id: str, exercise_id: str):
        """Recupera a última carga registrada para um exercício."""
        print(
            f"INFO: Recuperando última carga para user_id: {user_id}, exercise_id: {exercise_id}"
        )
        try:
            response = (
                self.client.table("progress")
                .select("load, recorded_at")
                .eq("user_id", user_id)
                .eq("exercise_id", exercise_id)
                .order("recorded_at", desc=True)
                .limit(1)
                .execute()
            )

            if response.data and len(response.data) > 0:
                load = response.data[0]["load"]
                print(f"INFO: Última carga encontrada: {load}kg")
                return load
            else:
                print("INFO: Nenhuma carga anterior encontrada")
                return 0.0
        except Exception as e:
            print(f"ERROR: Erro ao recuperar carga: {str(e)}")
            return 0.0

    def get_exercise_progress_history(
        self, user_id: str, exercise_id: str, limit: int = 10
    ):
        """Recupera histórico de progresso de um exercício."""
        print(
            f"INFO: Recuperando histórico de progresso para user_id: {user_id}, exercise_id: {exercise_id}"
        )
        try:
            response = (
                self.client.table("progress")
                .select("load, recorded_at")
                .eq("user_id", user_id)
                .eq("exercise_id", exercise_id)
                .order("recorded_at", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data
        except Exception as e:
            print(f"ERROR: Erro ao recuperar histórico: {str(e)}")
            self._safe_show_snackbar(f"Erro ao recuperar histórico: {str(e)}")
            raise

    def get_user_progress_summary(self, user_id: str):
        """Recupera resumo do progresso do usuário."""
        print(f"INFO: Recuperando resumo de progresso para user_id: {user_id}")
        try:
            response = (
                self.client.table("progress")
                .select("exercise_id, load, recorded_at, exercicios(nome)")
                .eq("user_id", user_id)
                .order("recorded_at", desc=True)
                .execute()
            )
            return response.data
        except Exception as e:
            print(f"ERROR: Erro ao recuperar resumo de progresso: {str(e)}")
            self._safe_show_snackbar(f"Erro ao recuperar resumo de progresso: {str(e)}")
            raise
