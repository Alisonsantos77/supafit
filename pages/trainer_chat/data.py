import flet as ft
from services.supabase import SupabaseService
from utils.alerts import CustomSnackBar
import sys


def get_user_profile(supabase_service: SupabaseService, user_id: str) -> dict:
    """Carrega os dados do perfil do usuário do Supabase com cache."""
    try:
        user_profile = (
            supabase_service.client.table("user_profiles")
            .select("name, age, weight, height, goal, level")
            .eq("user_id", user_id)
            .execute()
            .data
        )
        profile = (
            user_profile[0]
            if user_profile
            else {
                "name": "Usuário",
                "age": "N/A",
                "weight": "N/A",
                "height": "N/A",
                "goal": "N/A",
                "level": "N/A",
                "user_id": user_id,
            }
        )
        print(f"INFO: Perfil carregado para user_id: {user_id}")
        return profile
    except Exception as e:
        print(f"ERROR: Falha ao carregar perfil do usuário {user_id}: {str(e)}", file=sys.stderr)
        return {
            "name": "Usuário",
            "age": "N/A",
            "weight": "N/A",
            "height": "N/A",
            "goal": "N/A",
            "level": "N/A",
            "user_id": user_id,
        }


async def validate_user_session(
    page: ft.Page, supabase_service: SupabaseService, user_id: str
) -> bool:
    """Valida a sessão do usuário e redireciona se necessário."""
    if not user_id or user_id == "default_user":
        print("Usuário não autenticado. Redirecionando para a página de login.")
        CustomSnackBar(
            message="Você precisa estar logado para acessar o chat.",
            bgcolor=ft.Colors.RED_700,
        ).show(page)
        page.go("/login")
        return False
    return True
