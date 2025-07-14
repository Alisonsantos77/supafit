from services.supabase import SupabaseService
from services.openai import OpenAIService


def initialize_services(page):
    """
    Inicializa os serviços principais da aplicação: Supabase e OpenAI.
    Recebe a página Flet para passar para SupabaseService.
    """
    print("[STARTUP] Inicializando serviços...")
    supabase = SupabaseService.get_instance(page)
    openai = OpenAIService()
    print("[STARTUP] Serviços inicializados com sucesso.")
    return supabase, openai
