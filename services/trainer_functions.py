import os
import json
import uuid
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
                    "user_id": {"type": "string", "description": "UUID do usuário."},
                    "supabase": {"type": "object", "description": "Cliente Supabase"},
                },
                "required": ["user_id", "supabase"],
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
                    "user_id": {"type": "string", "description": "UUID do usuário."},
                    "supabase": {"type": "object", "description": "Cliente Supabase"},
                },
                "required": ["user_id", "supabase"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_substitutes",
            "description": "Sugere exercícios alternativos com base em grupo muscular e restrições do usuário.",
            "parameters": {
                "type": "object",
                "properties": {
                    "exercise_id": {
                        "type": "string",
                        "description": "ID do exercício.",
                    },
                    "pain_location": {
                        "type": "string",
                        "description": "Local da dor (opcional).",
                        "default": "",
                    },
                    "restrictions": {
                        "type": "string",
                        "description": "Restrições do usuário.",
                        "default": "",
                    },
                    "supabase": {"type": "object", "description": "Cliente Supabase"},
                },
                "required": ["exercise_id", "supabase"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_plan_exercise",
            "description": "Atualiza um exercício no plano do usuário com base no nome do exercício.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan_exercise_id": {
                        "type": "string",
                        "description": "ID da linha em plan_exercises.",
                    },
                    "new_exercise_name": {
                        "type": "string",
                        "description": "Nome do exercício substituto.",
                    },
                    "supabase": {"type": "object", "description": "Cliente Supabase"},
                },
                "required": ["plan_exercise_id", "new_exercise_name", "supabase"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_exercise_details",
            "description": "Busca detalhes de um exercício por ID ou nome.",
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
                        "description": "Nome do exercício.",
                        "default": "",
                    },
                    "supabase": {"type": "object", "description": "Cliente Supabase"},
                },
                "required": ["supabase"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "process_numeric_selection",
            "description": "Processa seleções numéricas do usuário e retorna o exercise_id correspondente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_selection": {
                        "type": "string",
                        "description": "Seleção numérica do usuário.",
                    },
                    "context_type": {
                        "type": "string",
                        "description": "Tipo de contexto.",
                    },
                    "supabase": {"type": "object", "description": "Cliente Supabase"},
                },
                "required": ["user_selection", "context_type", "supabase"],
            },
        },
    },
]

# -------------------------------------------------------------------
# FUNCTION IMPLEMENTATIONS
# -------------------------------------------------------------------
def is_valid_uuid(value: str) -> bool:
    """Valida se o valor é um UUID válido."""
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        print(f"ERROR: ID inválido: {value}")
        return False


def get_user_profile(supabase: Client, user_id: str) -> Dict[str, Any]:
    """Busca o perfil do usuário."""
    try:
        if not is_valid_uuid(user_id):
            print(f"ERROR: ID de usuário inválido: {user_id}")
            return {"error": "ID de usuário inválido"}
        response = (
            supabase.table("user_profiles")
            .select("*")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        if response.data:
            print(f"INFO: Perfil encontrado para user_id: {user_id}")
            return response.data
        print(f"WARNING: Perfil não encontrado para user_id: {user_id}")
        return {"error": "Perfil não encontrado"}
    except Exception as e:
        print(f"ERROR: Erro ao buscar perfil para user_id: {user_id} - {e}")
        return {"error": f"Erro ao buscar perfil: {str(e)}"}


def get_user_plan(supabase: Client, user_id: str) -> Dict[str, Any]:
    try:
        if not is_valid_uuid(user_id):
            print(f"ERROR: ID de usuário inválido: {user_id}")
            return {"error": "ID de usuário inválido"}
        response = (
            supabase.table("user_plans")
            .select(
                "plan_id, day, title, plan_exercises(order, sets, reps, plan_exercise_id, exercicios(id, nome, grupo_muscular))"
            )
            .eq("user_id", user_id)
            .order("created_at", desc=True)  # Ordenar por mais recente
            .limit(7)  # Limitar a 7 dias (uma semana)
            .execute()
        )
        plan_data = {}
        for plan in response.data:
            if plan.get("plan_exercises"):
                plan_data[plan["day"]] = {
                    "title": plan["title"],
                    "exercises": [
                        {
                            "plan_exercise_id": ex["plan_exercise_id"],
                            "order": ex["order"],
                            "sets": ex["sets"],
                            "reps": ex["reps"],
                            "exercise": {
                                "id": ex["exercicios"]["id"],
                                "nome": ex["exercicios"]["nome"],
                                "grupo_muscular": ex["exercicios"]["grupo_muscular"],
                            },
                        }
                        for ex in sorted(
                            plan["plan_exercises"], key=lambda x: x["order"]
                        )
                    ],
                }
        if not plan_data:
            print(f"WARNING: Nenhum plano encontrado para user_id: {user_id}")
            return {"error": "Plano não encontrado"}
        print(f"INFO: Plano formatado com sucesso para user_id: {user_id}")
        return plan_data
    except Exception as e:
        print(f"ERROR: Erro ao buscar plano para user_id: {user_id} - {e}")
        return {"error": f"Erro ao buscar plano: {str(e)}"}


def find_substitutes(
    supabase: Client, exercise_id: str, pain_location: str = "", restrictions: str = ""
) -> Dict[str, Any]:
    try:
        if not is_valid_uuid(exercise_id):
            print(f"ERROR: ID de exercício inválido: {exercise_id}")
            return {"error": f"ID de exercício inválido: {exercise_id}"}
        response = (
            supabase.table("exercicios")
            .select("id, nome, grupo_muscular")
            .eq("id", exercise_id)
            .execute()
        )
        if not response.data:
            print(f"ERROR: Exercício não encontrado para id: {exercise_id}")
            return {"error": f"Exercício não encontrado para id: {exercise_id}"}
        original_exercise = response.data[0]
        grupo_muscular = original_exercise["grupo_muscular"]
        query = (
            supabase.table("exercicios")
            .select("id, nome")
            .eq("grupo_muscular", grupo_muscular)
            .neq("id", exercise_id)
            .limit(3)
        )
        substitutes = query.execute()
        if not substitutes.data:
            print(
                f"WARNING: Nenhum substituto encontrado para grupo muscular: {grupo_muscular}"
            )
            return {
                "message": f"Não encontrei substitutos para '{original_exercise['nome']}'."
            }
        print(
            f"INFO: {len(substitutes.data)} substitutos encontrados para grupo muscular: {grupo_muscular}"
        )
        return {
            "original_exercise": {
                "id": original_exercise["id"],
                "nome": original_exercise["nome"],
                "plan_exercise_id": "",
            },
            "substitutes": substitutes.data,
            "total_found": len(substitutes.data),
        }
    except Exception as e:
        print(
            f"ERROR: Erro ao buscar substitutos para exercise_id: {exercise_id} - {e}"
        )
        return {"error": f"Erro ao buscar substitutos: {str(e)}"}


def update_plan_exercise(
    supabase: Client, plan_exercise_id: str, new_exercise_name: str
) -> Dict[str, Any]:
    """
    Atualiza um exercício no plano do usuário com base no nome do exercício.

    Args:
        supabase: Cliente Supabase
        plan_exercise_id: ID da linha em plan_exercises
        new_exercise_name: Nome do exercício substituto

    Returns:
        Dict com resultado da operação
    """
    try:
        if not is_valid_uuid(plan_exercise_id):
            print(f"ERROR: ID de plano de exercício inválido: {plan_exercise_id}")
            return {"error": "ID de plano de exercício inválido"}

        if not new_exercise_name or not new_exercise_name.strip():
            print(f"ERROR: Nome do exercício vazio")
            return {"error": "Nome do exercício é obrigatório"}

        # Verifica se o plano de exercício existe
        plan_check = (
            supabase.table("plan_exercises")
            .select("plan_exercise_id")
            .eq("plan_exercise_id", plan_exercise_id)
            .execute()
        )
        if not plan_check.data:
            print(f"ERROR: Plano de exercício não encontrado: {plan_exercise_id}")
            return {"error": f"Plano de exercício não encontrado: {plan_exercise_id}"}

        # Busca o exercício pelo nome (busca aproximada)
        exercise_search = (
            supabase.table("exercicios")
            .select("id, nome")
            .ilike("nome", f"%{new_exercise_name.strip()}%")
            .limit(1)
            .execute()
        )

        if not exercise_search.data:
            print(f"ERROR: Exercício não encontrado com nome: {new_exercise_name}")
            return {"error": f"Exercício não encontrado com nome '{new_exercise_name}'"}

        new_exercise = exercise_search.data[0]
        new_exercise_id = new_exercise["id"]
        found_exercise_name = new_exercise["nome"]

        print(
            f"INFO: Exercício encontrado: {found_exercise_name} (ID: {new_exercise_id})"
        )

        # Atualiza o plano de exercício
        response = (
            supabase.table("plan_exercises")
            .update({"exercise_id": new_exercise_id})
            .eq("plan_exercise_id", plan_exercise_id)
            .execute()
        )

        if not response.data:
            print(f"ERROR: Falha ao atualizar plano de exercício: {plan_exercise_id}")
            return {
                "error": f"Falha ao atualizar plano de exercício: {plan_exercise_id}"
            }

        print(
            f"INFO: Plano de exercício atualizado: {plan_exercise_id} para exercise_id: {new_exercise_id}"
        )
        return {
            "success": True,
            "message": f"Exercício atualizado com sucesso para '{found_exercise_name}'",
            "old_plan_exercise_id": plan_exercise_id,
            "new_exercise_id": new_exercise_id,
            "new_exercise_name": found_exercise_name,
        }

    except Exception as e:
        print(f"ERROR: Erro ao atualizar plan_exercise_id: {plan_exercise_id} - {e}")
        import traceback

        print(f"ERROR: Traceback: {traceback.format_exc()}")
        return {"error": f"Erro ao atualizar exercício: {str(e)}"}


def get_exercise_details(
    supabase: Client, exercise_id: str = "", exercise_name: str = ""
) -> Dict[str, Any]:
    try:
        if exercise_id:
            if not is_valid_uuid(exercise_id):
                print(f"ERROR: ID de exercício inválido: {exercise_id}")
                return {"error": f"ID de exercício inválido: {exercise_id}"}
            response = (
                supabase.table("exercicios")
                .select("id, nome, grupo_muscular")
                .eq("id", exercise_id)
                .execute()
            )
            if response.data:
                print(f"INFO: Exercício encontrado para id: {exercise_id}")
                return {"exercises": response.data}
            print(f"WARNING: Exercício não encontrado para id: {exercise_id}")
            return {"error": f"Exercício com ID {exercise_id} não encontrado"}
        elif exercise_name:
            response = (
                supabase.table("exercicios")
                .select("id, nome, grupo_muscular")
                .ilike("nome", f"%{exercise_name}%")
                .limit(3)  
                .execute()
            )
            if response.data:
                print(
                    f"INFO: {len(response.data)} exercícios encontrados para nome: {exercise_name}"
                )
                return {
                    "exercises": response.data,
                    "search_type": "partial_match",
                    "original_search": exercise_name,
                }
            print(f"WARNING: Nenhum exercício encontrado para nome: {exercise_name}")
            return {"error": f"Nenhum exercício encontrado com nome '{exercise_name}'"}
        print("ERROR: É necessário fornecer exercise_id ou exercise_name")
        return {"error": "É necessário fornecer exercise_id ou exercise_name"}
    except Exception as e:
        print(f"ERROR: Erro ao buscar exercício - {e}")
        return {"error": f"Erro ao buscar exercício: {str(e)}"}


def process_numeric_selection(
    supabase: Client, user_selection: str, context_type: str
) -> Dict[str, Any]:
    """Processa seleções numéricas do usuário."""
    try:
        print(
            f"INFO: Processando seleção numérica: {user_selection}, contexto: {context_type}"
        )
        return {
            "message": "Função de contexto numérico - implementar com estado da sessão",
            "user_selection": user_selection,
            "context_type": context_type,
        }
    except Exception as e:
        print(f"ERROR: Erro ao processar seleção numérica: {user_selection} - {e}")
        return {"error": f"Erro ao processar seleção: {str(e)}"}


# Mapeamento das funções
FUNCTION_MAP = {
    "get_user_profile": get_user_profile,
    "get_user_plan": get_user_plan,
    "find_substitutes": find_substitutes,
    "update_plan_exercise": update_plan_exercise,
    "get_exercise_details": get_exercise_details,
    "process_numeric_selection": process_numeric_selection,
}
