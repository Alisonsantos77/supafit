import os
import json
import uuid
from datetime import datetime
from openai import OpenAI
from supabase import create_client, Client
from typing import Dict, Any, List

# Configuração de variáveis de ambiente
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or not OPENAI_API_KEY:
    raise RuntimeError(
        "Defina SUPABASE_URL, SUPABASE_KEY e OPENAI_API_KEY nas variáveis de ambiente"
    )

# Inicialização dos clientes
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)

# Ferramentas (adaptadas de trainer_functions.py)
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
            "description": "Sugere exercícios alternativos com base em grupo muscular e restrições do usuário.",
            "parameters": {
                "type": "object",
                "properties": {
                    "exercise_id": {"type": "string", "description": "ID do exercício."},
                    "pain_location": {"type": "string", "description": "Local da dor."},
                    "restrictions": {"type": "string", "description": "Restrições do usuário.", "default": ""},
                },
                "required": ["exercise_id", "pain_location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_plan_exercise",
            "description": "Atualiza um exercício no plano do usuário.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan_exercise_id": {"type": "string", "description": "ID da linha em plan_exercises."},
                    "new_exercise_id": {"type": "string", "description": "ID do exercício substituto."},
                },
                "required": ["plan_exercise_id", "new_exercise_id"],
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
                    "exercise_id": {"type": "string", "description": "ID do exercício.", "default": ""},
                    "exercise_name": {"type": "string", "description": "Nome do exercício.", "default": ""},
                },
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
                    "user_selection": {"type": "string", "description": "Seleção numérica do usuário."},
                    "context_type": {"type": "string", "description": "Tipo de contexto."},
                },
                "required": ["user_selection", "context_type"],
            },
        },
    },
]

# Funções das ferramentas (adaptadas de trainer_functions.py)
def get_user_profile(supabase: Client, user_id: str) -> Dict[str, Any]:
    try:
        response = supabase.table("user_profiles").select("*").eq("user_id", user_id).single().execute()
        if hasattr(response, "data") and response.data:
            return response.data
        return {"error": "Perfil não encontrado"}
    except Exception as e:
        return {"error": f"Erro ao buscar perfil: {str(e)}"}

def get_user_plan(supabase: Client, user_id: str) -> Dict[str, Any]:
    try:
        plans_response = supabase.table("user_plans").select("plan_id, day, title").eq("user_id", user_id).execute()
        if not (hasattr(plans_response, "data") and plans_response.data):
            return {"error": "Nenhum plano encontrado para o usuário"}

        plan_data: Dict[str, Any] = {}
        empty_plans = []

        for plan in plans_response.data:
            plan_id = plan.get("plan_id")
            day = plan.get("day")
            title = plan.get("title", "")
            exercises_response = supabase.table("plan_exercises").select(
                "plan_exercise_id, order, sets, reps, exercise_id, exercicios(id, nome, grupo_muscular, equipamento, tipo_movimento)"
            ).eq("plan_id", plan_id).order("order").execute()

            if not (hasattr(exercises_response, "data") and exercises_response.data):
                empty_plans.append({"plan_id": plan_id, "day": day, "title": title})
                continue

            formatted_exercises: List[Dict[str, Any]] = []
            for ex in exercises_response.data:
                info = ex.get("exercicios", {})
                formatted_exercises.append({
                    "exercise_id": ex.get("exercise_id"),
                    "exercise_name": info.get("nome", "Nome não encontrado"),
                    "sets": ex.get("sets"),
                    "reps": ex.get("reps"),
                })

            plan_data[day] = {"title": title, "exercises": formatted_exercises}

        if empty_plans:
            return {"error": "Alguns planos não possuem exercícios associados", "empty_plans": empty_plans}
        if plan_data:
            return plan_data
        return {"error": "Nenhum exercício encontrado nos planos do usuário"}
    except Exception as e:
        return {"error": f"Erro ao buscar plano: {str(e)}"}

def find_substitutes(supabase: Client, exercise_id: str, pain_location: str, restrictions: str = "") -> Dict[str, Any]:
    try:
        check_exercise = supabase.table("exercicios").select("id").eq("id", exercise_id).execute()
        if not (hasattr(check_exercise, "data") and check_exercise.data):
            return {"error": f"Exercício com ID {exercise_id} não encontrado"}

        original_response = supabase.table("exercicios").select("id, nome, grupo_muscular, equipamento, tipo_movimento").eq("id", exercise_id).execute()
        if not (hasattr(original_response, "data") and original_response.data):
            return {"error": "Exercício original não encontrado"}
        
        original_exercise = original_response.data[0]
        muscle_group = original_exercise.get("grupo_muscular", "")
        
        substitutes_response = supabase.table("exercicios").select("id, nome, grupo_muscular, equipamento, tipo_movimento, descricao").ilike("grupo_muscular", f"%{muscle_group}%").neq("id", exercise_id).limit(10).execute()
        substitutes = substitutes_response.data if hasattr(substitutes_response, "data") else []
        
        return {
            "original_exercise": original_exercise,
            "pain_location": pain_location,
            "restrictions": restrictions,
            "substitutes": substitutes,
            "total_found": len(substitutes),
        }
    except Exception as e:
        return {"error": f"Erro ao buscar substitutos: {str(e)}"}

def exercise_exists(supabase: Client, exercise_id: str) -> bool:
    try:
        response = supabase.table("exercicios").select("id").eq("id", exercise_id).limit(1).execute()
        return bool(hasattr(response, "data") and response.data)
    except Exception as e:
        return False

def update_plan_exercise(supabase: Client, plan_exercise_id: str, new_exercise_id: str) -> Dict[str, Any]:
    try:
        if not exercise_exists(supabase, new_exercise_id):
            return {"success": False, "error": "Novo exercício não encontrado"}
        
        exercise_response = supabase.table("exercicios").select("id, nome").eq("id", new_exercise_id).execute()
        if not (hasattr(exercise_response, "data") and exercise_response.data):
            return {"success": False, "error": "Erro ao buscar detalhes do novo exercício"}
        
        new_exercise_data = exercise_response.data[0]
        update_response = supabase.table("plan_exercises").update({"exercise_id": new_exercise_id}).eq("plan_exercise_id", plan_exercise_id).execute()
        
        if hasattr(update_response, "data") and update_response.data:
            return {
                "success": True,
                "message": f"Exercício substituído por: {new_exercise_data.get('nome')}",
                "new_exercise": new_exercise_data,
            }
        return {"success": False, "error": "Falha ao atualizar o exercício"}
    except Exception as e:
        return {"success": False, "error": f"Erro ao atualizar exercício: {str(e)}"}

def get_exercise_details(supabase: Client, exercise_id: str = "", exercise_name: str = "") -> Dict[str, Any]:
    try:
        if exercise_id:
            response = supabase.table("xercicios").select("*").eq("id", exercise_id).execute()
            if hasattr(response, "data") and response.data:
                return {"exercises": response.data}
            return {"error": f"Exercício com ID {exercise_id} não encontrado"}
        
        elif exercise_name:
            exact_response = supabase.table("exercicios").select("*").ilike("nome", exercise_name).execute()
            if hasattr(exact_response, "data") and exact_response.data:
                return {"exercises": exact_response.data, "search_type": "exact_match"}
            
            keywords = [word for word in exercise_name.lower().split() if word not in ["com", "de", "no", "na", "em", "o", "a", "e"]]
            partial_results = []
            for keyword in keywords:
                partial_response = supabase.table("exercicios").select("*").ilike("nome", f"%{keyword}%").limit(10).execute()
                if hasattr(partial_response, "data") and partial_response.data:
                    partial_results.extend(partial_response.data)
            
            seen_ids = set()
            unique_results = [ex for ex in partial_results if not (ex["id"] in seen_ids or seen_ids.add(ex["id"]))]
            if unique_results:
                return {"exercises": unique_results[:5], "search_type": "partial_match", "original_search": exercise_name}
            
            return {"error": f"Nenhum exercício encontrado com nome '{exercise_name}'"}
        return {"error": "É necessário fornecer exercise_id ou exercise_name"}
    except Exception as e:
        return {"error": f"Erro ao buscar exercício: {str(e)}"}

def process_numeric_selection(supabase: Client, user_selection: str, context_type: str) -> Dict[str, Any]:
    return {
        "message": "Função de contexto numérico - implementar com estado da sessão",
        "user_selection": user_selection,
        "context_type": context_type,
    }

# Mapeamento das funções
FUNCTION_MAP = {
    "get_user_profile": get_user_profile,
    "get_user_plan": get_user_plan,
    "find_substitutes": find_substitutes,
    "update_plan_exercise": update_plan_exercise,
    "get_exercise_details": get_exercise_details,
    "process_numeric_selection": process_numeric_selection,
}

# Sistema de chat interativo simplificado
def chat_with_trainer():
    print("=" * 60)
    print("🏋️ COACHITO — Personal Trainer SupaFit (Versão de Teste)")
    print("=" * 60)
    print("Digite 'sair' para encerrar o programa")
    print("Digite 'limpar' para reiniciar a conversa")
    print("Digite sua pergunta (ex.: 'Quero substituir Rosca Direta com Halteres por dor no cotovelo')")
    print("-" * 60)

    user_id = "d36bfe78-51d3-4435-a04a-982f3b17e64a"  # ID fixo para testes
    user_data = get_user_profile(supabase, user_id)
    if "error" in user_data:
        print(f"❌ Erro: {user_data['error']}")
        return

    system_prompt = f"""
    Você é Coachito, um treinador da plataforma SupaFit. Oriente o usuário com base em:
    - ID: {user_id}
    - Nome: {user_data.get('name', 'Atleta')}
    - Objetivo: {user_data.get('goal', 'N/A')}
    - Restrições: {user_data.get('restrictions', 'Nenhuma')}
    Ferramentas:
    - get_user_profile(user_id)
    - get_user_plan(user_id)
    - get_exercise_details(exercise_id, exercise_name)
    - find_substitutes(exercise_id, pain_location, restrictions)
    - update_plan_exercise(plan_exercise_id, new_exercise_id)
    - process_numeric_selection(user_selection, context_type)
    Instruções:
    - Liste opções de exercícios sem numeração, apenas nomes.
    - Instrua: "Responda com o nome do exercício desejado para atualizar o plano."
    - Use get_exercise_details para localizar exercícios por nome.
    - Seja direto e profissional. Máximo 1 emoji por resposta.
    """

    messages = [{"role": "system", "content": system_prompt}]
    last_options = {}  # Armazena mapeamento número -> exercise_id

    while True:
        try:
            user_input = input("\n👤 Você: ").strip()

            if user_input.lower() == "sair":
                print("\n👋 Obrigado por usar o Coachito!")
                break

            if user_input.lower() == "limpar":
                messages = [{"role": "system", "content": system_prompt}]
                last_options = {}
                print("\n🔄 Conversa reiniciada!")
                continue

            if not user_input:
                continue

            messages.append({"role": "user", "content": user_input, "timestamp": datetime.now().isoformat()})

            print("\n🤖 Coachito: ", end="", flush=True)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.3,
            )

            message = response.choices[0].message

            if message.tool_calls:
                messages.append({"role": "assistant", "content": message.content or "", "tool_calls": [
                    {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in message.tool_calls
                ]})

                for tool_call in message.tool_calls:
                    fname = tool_call.function.name
                    fargs = json.loads(tool_call.function.arguments)
                    fargs["supabase"] = supabase

                    if fname == "find_substitutes":
                        result = FUNCTION_MAP[fname](**fargs)
                        if "substitutes" in result and result["substitutes"]:
                            last_options = {str(i+1): sub["id"] for i, sub in enumerate(result["substitutes"])}
                            print("\nOpções de substituição:")
                            for i, sub in enumerate(result["substitutes"], 1):
                                print(f"{i}. {sub['nome']}")
                            print("Responda com o nome do exercício desejado para atualizar seu plano.")
                        else:
                            print(result.get("error", "Nenhum substituto encontrado."))

                    elif fname == "update_plan_exercise":
                        # Verificar plan_exercise_id
                        plan_response = supabase.table("plan_exercises").select("plan_exercise_id").eq("exercise_id", fargs.get("exercise_id", "")).eq("plan_id", supabase.table("user_plans").select("plan_id").eq("user_id", user_id).execute().data[0]["plan_id"] if supabase.table("user_plans").select("plan_id").eq("user_id", user_id).execute().data else None).execute()
                        if plan_response.data:
                            fargs["plan_exercise_id"] = plan_response.data[0]["plan_exercise_id"]
                        result = FUNCTION_MAP[fname](**fargs)
                        if result.get("success"):
                            updated_plan = get_user_plan(supabase, user_id)
                            if "error" not in updated_plan:
                                print(f"\n{result['message']}\nPlano atualizado:")
                                for day, plan in updated_plan.items():
                                    print(f"{day} - {plan['title']}:")
                                    for ex in plan["exercises"]:
                                        print(f"- {ex['exercise_name']} ({ex['sets']} séries, {ex['reps']})")
                            else:
                                print(updated_plan["error"])
                        else:
                            print(result["error"])

                    else:
                        result = FUNCTION_MAP[fname](**fargs)
                        print(json.dumps(result, ensure_ascii=False, indent=2))

                    messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(result, ensure_ascii=False)})

                final_response = client.chat.completions.create(
                    model="gpt-3.5-turbo-1106", messages=messages, tools=TOOLS, tool_choice="auto", temperature=0.3
                )
                final_message = final_response.choices[0].message.content
                print(final_message)
                messages.append({"role": "assistant", "content": final_message})
            else:
                print(message.content)
                messages.append({"role": "assistant", "content": message.content})

        except KeyboardInterrupt:
            print("\n\n⚠️ Interrompido pelo usuário. Digite 'sair' para encerrar.")
        except Exception as e:
            print(f"\n❌ Erro: {str(e)}")
            print("Tente novamente ou digite 'sair' para encerrar.")

def main():
    try:
        chat_with_trainer()
    except Exception as e:
        print(f"❌ Erro fatal: {str(e)}")
        print("Verifique suas variáveis de ambiente e conexões.")

if __name__ == "__main__":
    main()