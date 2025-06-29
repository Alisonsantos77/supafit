import os
from supabase import Client
from typing import List, Dict, Any

# -------------------------------------------------------------------
# FUNCTION SCHEMAS DEFINITIONS
# -------------------------------------------------------------------
FUNCTIONS = [
    {
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
    {
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
    {
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
                    "description": "Local da dor (ex: 'posterior').",
                },
                "restrictions": {
                    "type": "string",
                    "description": "Campo restrictions do perfil.",
                },
            },
            "required": ["exercise_id", "pain_location"],
        },
    },
    {
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
]

# -------------------------------------------------------------------
# FUNCTION IMPLEMENTATIONS
# -------------------------------------------------------------------


def get_user_profile(supabase: Client, user_id: str) -> Dict[str, Any]:
    response = (
        supabase.table("user_profiles")
        .select("*")
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if response.error:
        raise RuntimeError(f"Erro ao buscar perfil: {response.error.message}")
    return response.data


def get_user_plan(supabase: Client, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
    response = (
        supabase.table("user_plans")
        .select("day, plan_exercises(order, sets, reps, exercise_id)")
        .eq("user_id", user_id)
        .execute()
    )
    if response.error:
        raise RuntimeError(f"Erro ao buscar plano: {response.error.message}")
    return {item["day"]: item["plan_exercises"] for item in response.data}


def find_substitutes(
    supabase: Client, exercise_id: str, pain_location: str, restrictions: str = None
) -> List[Dict[str, Any]]:
    resp = (
        supabase.table("exercicios")
        .select("grupo_muscular, equipamento, tipo_movimento")
        .eq("id", exercise_id)
        .single()
        .execute()
    )
    if resp.error:
        raise RuntimeError(f"Erro ao buscar exercício: {resp.error.message}")
    gm = resp.data.get("grupo_muscular")
    result = (
        supabase.table("exercicios")
        .select("id, nome")
        .ilike("grupo_muscular", f"%{gm}%")
        .execute()
    )
    if result.error:
        raise RuntimeError(f"Erro ao buscar substitutos: {result.error.message}")
    return result.data


def update_plan_exercise(
    supabase: Client, plan_exercise_id: str, new_exercise_id: str
) -> Dict[str, Any]:
    resp = (
        supabase.table("plan_exercises")
        .update({"exercise_id": new_exercise_id})
        .eq("plan_exercise_id", plan_exercise_id)
        .execute()
    )
    if resp.error:
        return {"success": False, "error": resp.error.message}
    return {"success": True, "message": "Exercício atualizado com sucesso."}


FUNCTION_MAP = {
    "get_user_profile": get_user_profile,
    "get_user_plan": get_user_plan,
    "find_substitutes": find_substitutes,
    "update_plan_exercise": update_plan_exercise,
}
