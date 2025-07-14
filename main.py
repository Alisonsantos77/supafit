import flet as ft
import asyncio
from dotenv import load_dotenv
from core.healthcheck import check_supabase_connection, check_openai_key
from core.startup import initialize_services
from routes import setup_routes
import traceback


class AppInitializer:
    """Classe responsável pela inicialização segura da aplicação."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.supabase = None
        self.openai = None
        self.initialization_complete = False

    def setup_page_config(self):
        """Configura as propriedades básicas da página."""
        self.page.title = "SupaFit"
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.theme_mode = ft.ThemeMode.SYSTEM

        # Carregar fontes
        self.page.fonts = {
            "Roboto": "assets/fonts/Roboto-VariableFont_wdth,wght.ttf",
            "Open Sans": "assets/fonts/OpenSans-VariableFont_wdth,wght.ttf",
            "Barlow": "assets/fonts/Barlow-Regular.ttf",
            "Manrope": "assets/fonts/Manrope-VariableFont_wght.ttf",
        }

        print("[APP] Configurações de página aplicadas")

    def show_loading_screen(self, message: str = "Carregando SupaFit..."):
        """Exibe tela de carregamento."""
        loading_content = ft.Column(
            [
                ft.ProgressRing(width=50, height=50),
                ft.Text(message, size=16, text_align=ft.TextAlign.CENTER),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        )

        self.page.controls.clear()
        self.page.add(loading_content)
        self.page.update()

    def show_error_screen(self, error_message: str, detailed_error: str = None):
        """Exibe tela de erro com opção de tentar novamente."""

        def retry_click(e):
            print("[APP] Tentando reinicializar...")
            self.initialize_app()

        error_content = ft.Column(
            [
                ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED, size=50),
                ft.Text(
                    "Erro na Inicialização",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.RED,
                ),
                ft.Text(error_message, size=14, text_align=ft.TextAlign.CENTER),
                ft.ElevatedButton(
                    "Tentar Novamente", on_click=retry_click, icon=ft.Icons.REFRESH
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        )

        if detailed_error:
            error_content.controls.insert(
                -1,
                ft.Text(
                    f"Detalhes: {detailed_error}", size=12, color=ft.Colors.GREY_600
                ),
            )

        self.page.controls.clear()
        self.page.add(error_content)
        self.page.update()

    def perform_healthchecks(self) -> bool:
        """Executa verificações de saúde da aplicação."""
        print("[APP] Iniciando healthchecks...")

        # Verificar Supabase
        if not check_supabase_connection():
            self.show_error_screen(
                "Falha ao conectar com o banco de dados",
                "Verifique sua conexão com a internet e tente novamente",
            )
            return False

        # Verificar OpenAI
        if not check_openai_key():
            self.show_error_screen(
                "Configuração da IA indisponível",
                "Serviço de chat temporariamente indisponível",
            )
            return False

        print("[APP] Healthchecks concluídos com sucesso")
        return True

    def initialize_services(self) -> bool:
        """Inicializa os serviços principais."""
        try:
            print("[APP] Inicializando serviços...")
            self.supabase, self.openai = initialize_services(self.page)

            if not self.supabase or not self.openai:
                raise Exception("Falha na inicialização dos serviços")

            print("[APP] Serviços inicializados com sucesso")
            return True

        except Exception as e:
            print(f"[APP] Erro na inicialização dos serviços: {e}")
            self.show_error_screen("Erro na inicialização dos serviços", str(e))
            return False


    def handle_authentication(self) -> str:
        """Gerencia a autenticação e direcionamento do usuário."""
        try:
            print("[APP] Verificando autenticação...")

            # tokens serão lidos do client_storage e usados
            self.supabase._restore_session()

            if self.supabase.is_authenticated():
                user = self.supabase.get_current_user()
                if user:
                    user_id = user.id
                    print(f"[APP] Usuário autenticado: {user_id}")

                    profile_response = self.supabase.get_profile(user_id)
                    if profile_response.data and len(profile_response.data) > 0:
                        profile = profile_response.data[0]
                        print(f"[APP] Perfil encontrado: {profile.get('name', 'Usuário')}")
                        self.page.client_storage.set("supafit.user_id", user_id)
                        self.page.client_storage.set("supafit.profile_created", True)
                        self.page.client_storage.set(
                            "supafit.level", profile.get("level", "iniciante")
                        )
                        return "/home"
                    else:
                        print("[APP] Perfil não encontrado, redirecionando para criação")
                        self.page.client_storage.set("supafit.user_id", user_id)
                        self.page.client_storage.set("supafit.profile_created", False)
                        return "/create_profile"

            print("[APP] Usuário não autenticado, redirecionando para login")
            return "/login"

        except Exception as e:
            print(f"[APP] Erro na verificação de autenticação: {e}")
            try:
                self.supabase._clear_session()
            except:
                pass
            return "/login"

    def setup_routes(self):
        """Configura as rotas da aplicação."""
        try:
            print("[APP] Configurando rotas...")
            setup_routes(self.page, self.supabase, self.openai)
            print("[APP] Rotas configuradas com sucesso")

        except Exception as e:
            print(f"[APP] Erro na configuração das rotas: {e}")
            self.show_error_screen("Erro na configuração da aplicação", str(e))

    def initialize_app(self):
        """Método principal de inicialização da aplicação."""
        try:
            print("[APP] Iniciando SupaFit...")

            # Configurar página
            self.setup_page_config()

            # Mostrar tela de carregamento
            self.show_loading_screen("Verificando sistemas...")

            # Executar healthchecks
            if not self.perform_healthchecks():
                return

            # Atualizar mensagem de carregamento
            self.show_loading_screen("Inicializando serviços...")

            # Inicializar serviços
            if not self.initialize_services():
                return

            # Atualizar mensagem de carregamento
            self.show_loading_screen("Verificando autenticação...")

            # Lidar com autenticação
            target_route = self.handle_authentication()

            # Configurar rotas
            self.setup_routes()

            # Navegar para a rota apropriada
            print(f"[APP] Navegando para: {target_route}")
            self.page.go(target_route)

            # Marcar inicialização como completa
            self.initialization_complete = True
            print("[APP] Inicialização concluída com sucesso")

        except Exception as e:
            print(f"[APP] Erro crítico na inicialização: {e}")
            print(f"[APP] Traceback: {traceback.format_exc()}")
            self.show_error_screen(
                "Erro crítico na inicialização",
                "A aplicação não pode ser inicializada. Tente novamente.",
            )


def main(page: ft.Page):
    """
    Função principal do SupaFit melhorada.
    Utiliza a classe AppInitializer para uma inicialização mais robusta.
    """
    # Carregar variáveis de ambiente
    load_dotenv()

    # Criar e executar inicializador
    initializer = AppInitializer(page)
    initializer.initialize_app()


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
