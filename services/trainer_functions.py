import os
import json
from supabase import Client
from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger("supafit.trainer_functions")

# -------------------------------------------------------------------
# TOOL SCHEMAS DEFINITIONS (antes: FUNCTIONS)
# -------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_user_profile",
            "description": "Retorna os dados do perfil do usuário, incluindo restrições e objetivo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "UUID do usuário."}
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_plan",
            "description": "Retorna o plano de treino do usuário, com lista de exercícios para cada dia.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "UUID do usuário."}
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_substitutes",
            "description": "Dada uma queixa de dor e exercício problemático, sugere exercícios alternativos com base em grupo muscular e restrições do usuário.",
            "parameters": {
                "type": "object",
                "properties": {
                    "exercise_id": {
                        "type": "string",
                        "description": "ID do exercício que causa dor.",
                    },
                    "pain_location": {
                        "type": "string",
                        "description": "Local da dor (ex: 'ombro', 'joelho', 'costas').",
                    },
                    "restrictions": {
                        "type": "string",
                        "description": "Campo restrictions do perfil do usuário.",
                        "default": "",
                    },
                },
                "required": ["exercise_id", "pain_location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_plan_exercise",
            "description": "Atualiza um registro de plan_exercises para trocar o exercício pelo novo escolhido.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan_exercise_id": {
                        "type": "string",
                        "description": "ID da linha em plan_exercises.",
                    },
                    "new_exercise_id": {
                        "type": "string",
                        "description": "ID do exercício substituto.",
                    },
                },
                "required": ["plan_exercise_id", "new_exercise_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_exercise_details",
            "description": "Busca detalhes de um exercício específico pelo ID ou nome.",
            "parameters": {
                "type": "object",
                "properties": {
                    "exercise_id": {
                        "type": "string",
                        "description": "ID do exercício.",
                        "default": "",
                    },
                    "exercise_name": {
                        "type": "string",
                        "description": "Nome do exercício para buscar.",
                        "default": "",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "process_numeric_selection",
            "description": "Processa seleções numéricas do usuário (ex: '1', '2') e retorna o exercise_id correspondente baseado no contexto anterior.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_selection": {
                        "type": "string",
                        "description": "Seleção numérica do usuário (ex: '1', 'escolho 2')",
                    },
                    "context_type": {
                        "type": "string",
                        "description": "Tipo de contexto: 'exercise_substitutes', 'exercise_search', etc.",
                    },
                },
                "required": ["user_selection", "context_type"],
            },
        },
    },
]


# -------------------------------------------------------------------
# FUNCTION IMPLEMENTATIONS
# -------------------------------------------------------------------
def process_numeric_selection(
    supabase: Client, user_selection: str, context_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Processa seleção baseada em contexto gerado anteriormente."""
    # context_data deve conter mapeamento 'last_options': {"nome_exercicio": plan_exercise_id}
    name = user_selection.strip()
    options = context_data.get("last_options", {})
    plan_ex_id = options.get(name)
    if not plan_ex_id:
        return {"success": False, "error": "Opção não encontrada no contexto"}
    return {"success": True, "plan_exercise_id": plan_ex_id}


def get_user_profile(supabase: Client, user_id: str) -> Dict[str, Any]:
    """Busca o perfil completo do usuário."""
    try:
        print(f"INFO- trainer_functions: Buscando perfil para user_id: {user_id}")
        response = (
            supabase.table("user_profiles")
            .select("*")
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        if hasattr(response, "data") and response.data:
            print(f"INFO- trainer_functions: Perfil encontrado para user_id: {user_id}")
            return response.data
        else:
            print(f"WARNING: Perfil não encontrado para user_id: {user_id}")
            return {"error": "Perfil não encontrado"}

    except Exception as e:
        print(f"ERROR - trainer_functions: Erro ao buscar perfil: {e}")
        return {"error": f"Erro ao buscar perfil: {str(e)}"}


def get_user_plan(supabase: Client, user_id: str) -> Dict[str, Any]:
    """
    Retorna plano do usuário incluindo plano_exercise_id em cada exercício.
    """
    try:
        response = (
            supabase.table("user_plans")
            .select(
                "plan_id, day, title, plan_exercises(plan_exercise_id, exercise_id, exercicios(id, nome), sets, reps)"
            )
            .eq("user_id", user_id)
            .execute()
        )
        if not getattr(response, "data", None):
            return {"error": "Plano não encontrado"}

        plan_data: Dict[str, Any] = {}
        for plan in response.data:
            day = plan.get("day")
            exercises = []
            for ex in plan.get("plan_exercises", []):
                info = ex.get("exercicios", {})
                exercises.append(
                    {
                        "plan_exercise_id": ex.get("plan_exercise_id"),
                        "exercise_id": ex.get("exercise_id"),
                        "exercise_name": info.get("nome"),
                        "sets": ex.get("sets"),
                        "reps": ex.get("reps"),
                    }
                )
            plan_data[day] = {"title": plan.get("title"), "exercises": exercises}
        return plan_data
    except Exception as e:
        logger.error(f"Erro ao buscar plano: {e}")
        return {"error": str(e)}


def find_substitutes(
    supabase: Client, exercise_id: str, pain_location: str, restrictions: str = ""
) -> Dict[str, Any]:
    """Encontra exercícios substitutos baseado no grupo muscular e restrições."""

    try:
        print(
            f"INFO- trainer_functions: Buscando substitutos para exercise_id: {exercise_id}, dor: {pain_location}"
        )

        # CORREÇÃO: Remover .single() e usar lista para verificar se existe
        check_exercise = (
            supabase.table("exercicios").select("id").eq("id", exercise_id).execute()
        )

        if not (hasattr(check_exercise, "data") and check_exercise.data):
            print(
                f"ERROR - trainer_functions: Exercício com ID {exercise_id} não encontrado"
            )
            return {"error": f"Exercício com ID {exercise_id} não encontrado"}

        # CORREÇÃO: Buscar o exercício original sem .single()
        original_response = (
            supabase.table("exercicios")
            .select("id, nome, grupo_muscular, equipamento, tipo_movimento")
            .eq("id", exercise_id)
            .execute()
        )

        if not (hasattr(original_response, "data") and original_response.data):
            logger.error(f"Exercício original não encontrado para ID: {exercise_id}")
            return {"error": "Exercício original não encontrado"}

        # CORREÇÃO: Pegar o primeiro item da lista
        original_exercise = original_response.data[0]
        muscle_group = original_exercise.get("grupo_muscular", "")

        print(
            f"INFO- trainer_functions: Exercício original encontrado: {original_exercise.get('nome')}"
        )
        # Busca exercícios do mesmo grupo muscular
        substitutes_response = (
            supabase.table("exercicios")
            .select("id, nome, grupo_muscular, equipamento, tipo_movimento, descricao")
            .ilike("grupo_muscular", f"%{muscle_group}%")
            .neq("id", exercise_id)  # Exclui o exercício original
            .limit(10)
            .execute()
        )

        substitutes = []
        if hasattr(substitutes_response, "data") and substitutes_response.data:
            substitutes = substitutes_response.data

        result = {
            "original_exercise": original_exercise,
            "pain_location": pain_location,
            "restrictions": restrictions,
            "substitutes": substitutes,
            "total_found": len(substitutes),
        }

        print(
            f"INFO- trainer_functions: {len(substitutes)} substitutos encontrados para {muscle_group}"
        )
        return result

    except Exception as e:
        print(f"ERROR - trainer_functions: Erro ao buscar substitutos: {e}")
        return {"error": f"Erro ao buscar substitutos: {str(e)}"}


# CORREÇÃO ADICIONAL: Função auxiliar para validar se exercício existe
def exercise_exists(supabase: Client, exercise_id: str) -> bool:
    """Verifica se um exercício existe na base de dados."""
    try:
        response = (
            supabase.table("exercicios")
            .select("id")
            .eq("id", exercise_id)
            .limit(1)
            .execute()
        )
        return bool(hasattr(response, "data") and response.data)
    except Exception as e:
        print(
            f"ERROR - trainer_functions: Erro ao verificar existência do exercício {exercise_id}: {e}"
        )
        return False


# CORREÇÃO ADICIONAL: Melhorar a função get_exercise_details
def get_exercise_details(
    supabase: Client, exercise_id: str = "", exercise_name: str = ""
) -> Dict[str, Any]:
    """Busca detalhes de um exercício por ID ou nome com busca inteligente."""
    try:
        if exercise_id:
            print(f"INFO- trainer_functions: Buscando exercício com ID: {exercise_id}")
            response = (
                supabase.table("exercicios").select("*").eq("id", exercise_id).execute()
            )

            if hasattr(response, "data") and response.data:
                return {"exercises": response.data}
            else:
                return {"error": f"Exercício com ID {exercise_id} não encontrado"}

        elif exercise_name:
            print(
                f"INFO- trainer_functions: Buscando exercício com nome: {exercise_name}"
            )

            # MELHORIA: Busca mais inteligente por nome
            # 1. Busca exata primeiro
            exact_response = (
                supabase.table("exercicios")
                .select("*")
                .ilike("nome", exercise_name)
                .execute()
            )

            # 2. Se não encontrar, busca parcial com palavras-chave
            if not (hasattr(exact_response, "data") and exact_response.data):
                # Extrai palavras-chave do nome (remove artigos e preposições)
                keywords = [
                    word
                    for word in exercise_name.lower().split()
                    if word not in ["com", "de", "no", "na", "em", "o", "a", "e"]
                ]

                # Busca por cada palavra-chave
                partial_results = []
                for keyword in keywords:
                    partial_response = (
                        supabase.table("exercicios")
                        .select("*")
                        .ilike("nome", f"%{keyword}%")
                        .limit(10)
                        .execute()
                    )
                    if hasattr(partial_response, "data") and partial_response.data:
                        partial_results.extend(partial_response.data)

                # Remove duplicatas
                seen_ids = set()
                unique_results = []
                for ex in partial_results:
                    if ex["id"] not in seen_ids:
                        unique_results.append(ex)
                        seen_ids.add(ex["id"])

                if unique_results:
                    return {
                        "exercises": unique_results[:5],  # Limita a 5 resultados
                        "search_type": "partial_match",
                        "original_search": exercise_name,
                    }
            else:
                return {"exercises": exact_response.data, "search_type": "exact_match"}

            return {
                "error": f"Nenhum exercício encontrado com nome '{exercise_name}'",
                "suggestion": "Tente usar palavras-chave como 'rosca', 'supino', 'agachamento'",
            }
        else:
            return {"error": "É necessário fornecer exercise_id ou exercise_name"}

    except Exception as e:
        print(f"ERROR - trainer_functions: Erro ao buscar exercício: {e}")
        return {"error": f"Erro ao buscar exercício: {str(e)}"}


# CORREÇÃO ADICIONAL: Melhorar update_plan_exercise
def update_plan_exercise(
    supabase: Client, plan_exercise_id: str, new_exercise_id: str
) -> Dict[str, Any]:
    """Atualiza exercício no plano usando IDs válidos."""
    try:
        # Atualiza diretamente com UUIDs
        result = (
            supabase.table("plan_exercises")
            .update({"exercise_id": new_exercise_id})
            .eq("plan_exercise_id", plan_exercise_id)
            .execute()
        )
        if getattr(result, "data", None):
            return {"success": True, "message": "Plano atualizado"}
        return {"success": False, "error": "Falha ao atualizar"}
    except Exception as e:
        logger.error(f"Erro ao atualizar exercício: {e}")
        return {"success": False, "error": str(e)}


FUNCTION_MAP = {
    "get_user_profile": get_user_profile,
    "get_user_plan": get_user_plan,
    "find_substitutes": find_substitutes,
    "update_plan_exercise": update_plan_exercise,
    "get_exercise_details": get_exercise_details,
    "process_numeric_selection": process_numeric_selection
}