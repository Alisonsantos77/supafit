from services.supabase import SupabaseService
from services.openai import OpenAIService


def check_supabase_connection() -> bool:
    """
    Tenta criar uma instância do SupabaseService e recuperar o usuário atual.
    Retorna True se conseguir conectar sem exceções, False caso contrário.
    """
    try:
        print("[HEALTHCHECK] Verificando Supabase...")
        supabase = SupabaseService.get_instance()
        user = supabase.get_current_user()
        print("[HEALTHCHECK] Supabase conectado com sucesso.")
        return True
    except Exception as e:
        print(f"[HEALTHCHECK] Erro ao conectar ao Supabase: {e}")
        return False


def check_openai_key() -> bool:
    """
    Tenta instanciar o OpenAIService e verificar se a chave está configurada.
    """
    try:
        print("[HEALTHCHECK] Verificando OpenAI...")
        openai = OpenAIService()
        if openai.api_key:
            print("[HEALTHCHECK] Chave OpenAI carregada com sucesso.")
            return True
        print("[HEALTHCHECK] Chave OpenAI ausente.")
        return False
    except Exception as e:
        print(f"[HEALTHCHECK] Erro ao verificar OpenAI: {e}")
        return False