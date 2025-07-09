import json
import uuid
from datetime import datetime
from groq import Groq
from utils.logger import get_logger

logger = get_logger("supafit.workout_generator")


class WorkoutGenerator:
    """Classe para gerar treinos personalizados usando IA"""

    def __init__(self, groq_api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.groq_client = Groq(api_key=groq_api_key)
        self.model = model

    def categorize_exercises(self, exercises):
        """Categoriza exercícios por grupo muscular"""
        grupo_mapping = {
            "Peitoral": ["Peitoral", "Peito", "Pectorais"],
            "Costas": ["Costas", "Dorsal", "Latíssimo", "Trapézio", "Romboides"],
            "Pernas": [
                "Quadríceps",
                "Isquiotibiais",
                "Glúteos",
                "Panturrilha",
                "Adutores",
                "Abdutores",
                "Posterior de Coxa",
            ],
            "Ombros": ["Deltoides", "Ombros", "Deltoide"],
            "Braços": ["Bíceps", "Tríceps", "Antebraços"],
            "Core": ["Abdominal", "Abdômen", "Lombar", "Oblíquo"],
            "Cardio": ["Cardio", "Aeróbico", "Funcional"],
        }

        exercicios_categorizados = {}

        for exercicio in exercises:
            grupo_original = exercicio.get("grupo_muscular", "Outros")
            categoria_encontrada = "Outros"

            for categoria, grupos in grupo_mapping.items():
                if any(grupo.lower() in grupo_original.lower() for grupo in grupos):
                    categoria_encontrada = categoria
                    break

            if categoria_encontrada not in exercicios_categorizados:
                exercicios_categorizados[categoria_encontrada] = []

            exercicios_categorizados[categoria_encontrada].append(exercicio)

        return exercicios_categorizados

    def get_training_parameters(self, goal, exercise_type="compound"):
        """Define parâmetros de treino baseado no objetivo"""
        parameters = {
            "Ganhar massa": {
                "compound": {"sets": 4, "reps": "6-8", "rest": "2-3min"},
                "isolation": {"sets": 3, "reps": "8-12", "rest": "1-2min"},
            },
            "Definir": {
                "compound": {"sets": 3, "reps": "10-12", "rest": "1-2min"},
                "isolation": {"sets": 3, "reps": "12-15", "rest": "45-60s"},
            },
            "Perder peso": {
                "compound": {"sets": 3, "reps": "12-15", "rest": "45-60s"},
                "isolation": {"sets": 2, "reps": "15-20", "rest": "30-45s"},
            },
            "Força": {
                "compound": {"sets": 5, "reps": "3-5", "rest": "3-5min"},
                "isolation": {"sets": 3, "reps": "6-8", "rest": "2-3min"},
            },
            "Resistência": {
                "compound": {"sets": 3, "reps": "15-20", "rest": "30-45s"},
                "isolation": {"sets": 2, "reps": "20-25", "rest": "30s"},
            },
            "Manter forma física": {
                "compound": {"sets": 3, "reps": "10-12", "rest": "1-2min"},
                "isolation": {"sets": 3, "reps": "12-15", "rest": "45-60s"},
            },
            "Hipertrofia": {
                "compound": {"sets": 4, "reps": "6-8", "rest": "2-3min"},
                "isolation": {"sets": 3, "reps": "8-12", "rest": "1-2min"},
            },
        }

        # Normalizar objetivo
        objetivo_normalizado = goal
        if "massa" in goal.lower() or "hipertrofia" in goal.lower():
            objetivo_normalizado = "Hipertrofia"
        elif "definir" in goal.lower() or "definição" in goal.lower():
            objetivo_normalizado = "Definir"
        elif "peso" in goal.lower() or "emagrecer" in goal.lower():
            objetivo_normalizado = "Perder peso"
        elif "força" in goal.lower():
            objetivo_normalizado = "Força"
        elif "resistência" in goal.lower():
            objetivo_normalizado = "Resistência"
        elif "manter" in goal.lower():
            objetivo_normalizado = "Manter forma física"

        return parameters.get(objetivo_normalizado, parameters["Manter forma física"])[
            exercise_type
        ]

    def create_workout_plan(self, exercises_data, user_profile):
        """Cria plano de treino personalizado"""
        try:
            exercises = (
                json.loads(exercises_data)
                if isinstance(exercises_data, str)
                else exercises_data
            )
            user = (
                json.loads(user_profile)
                if isinstance(user_profile, str)
                else user_profile
            )

            exercicios_categorizados = self.categorize_exercises(exercises)
            plan = {"divisao_treino": "", "dias_treino": {}, "observacoes": []}

            objetivo = user.get("goal", "Manter forma física")
            gender = user.get("gender", "Masculino").lower()
            age = user.get("age", 25)

            # Definir divisão de treino baseada no objetivo e perfil
            if "massa" in objetivo.lower() or "hipertrofia" in objetivo.lower():
                plan["divisao_treino"] = "ABCDEF - Hipertrofia"
                divisao_dias = {
                    "Segunda": {
                        "grupos": ["Peitoral", "Braços"],
                        "foco": "Peito e Tríceps",
                    },
                    "Terça": {
                        "grupos": ["Costas", "Braços"],
                        "foco": "Costas e Bíceps",
                    },
                    "Quarta": {"grupos": ["Pernas"], "foco": "Quadríceps e Glúteos"},
                    "Quinta": {"grupos": ["Ombros"], "foco": "Ombros e Trapézio"},
                    "Sexta": {"grupos": ["Pernas"], "foco": "Posterior e Panturrilha"},
                    "Sábado": {
                        "grupos": ["Braços", "Core"],
                        "foco": "Bíceps e Tríceps",
                    },
                }
            elif "definir" in objetivo.lower():
                plan["divisao_treino"] = "Push/Pull/Legs - Definição"
                divisao_dias = {
                    "Segunda": {
                        "grupos": ["Peitoral", "Ombros", "Braços"],
                        "foco": "Push (Empurrar)",
                    },
                    "Terça": {"grupos": ["Costas", "Braços"], "foco": "Pull (Puxar)"},
                    "Quarta": {"grupos": ["Pernas"], "foco": "Legs (Pernas)"},
                    "Quinta": {
                        "grupos": ["Peitoral", "Ombros", "Braços"],
                        "foco": "Push (Empurrar)",
                    },
                    "Sexta": {"grupos": ["Costas", "Braços"], "foco": "Pull (Puxar)"},
                    "Sábado": {"grupos": ["Pernas", "Core"], "foco": "Legs + Core"},
                }
            elif "peso" in objetivo.lower():
                plan["divisao_treino"] = "Full Body + Cardio - Emagrecimento"
                divisao_dias = {
                    "Segunda": {
                        "grupos": ["Peitoral", "Costas", "Pernas"],
                        "foco": "Full Body A",
                    },
                    "Terça": {"grupos": ["Cardio"], "foco": "Cardio Intenso"},
                    "Quarta": {
                        "grupos": ["Ombros", "Braços", "Core"],
                        "foco": "Full Body B",
                    },
                    "Quinta": {"grupos": ["Cardio"], "foco": "Cardio Moderado"},
                    "Sexta": {
                        "grupos": ["Pernas", "Costas", "Peitoral"],
                        "foco": "Full Body C",
                    },
                    "Sábado": {"grupos": ["Core", "Cardio"], "foco": "Core + Cardio"},
                }
            else:
                plan["divisao_treino"] = "ABC - Condicionamento Geral"
                divisao_dias = {
                    "Segunda": {
                        "grupos": ["Peitoral", "Costas"],
                        "foco": "Superiores A",
                    },
                    "Quarta": {"grupos": ["Pernas"], "foco": "Inferiores"},
                    "Sexta": {
                        "grupos": ["Ombros", "Braços", "Core"],
                        "foco": "Superiores B",
                    },
                }

            # Ajustar intensidade baseado na idade
            if age > 50:
                for dia, config in divisao_dias.items():
                    if "Core" not in config["grupos"]:
                        config["grupos"].append("Core")

            # Gerar exercícios para cada dia
            for dia, config in divisao_dias.items():
                exercicios_dia = []

                for grupo in config["grupos"]:
                    if grupo in exercicios_categorizados:
                        exercicios_grupo = exercicios_categorizados[grupo]

                        # Determinar número de exercícios baseado na divisão
                        if len(config["grupos"]) == 1:
                            num_exercicios = 4  # Dia focado em um grupo
                        elif len(config["grupos"]) == 2:
                            num_exercicios = 3  # Dois grupos
                        else:
                            num_exercicios = 2  # Três ou mais grupos

                        # Selecionar exercícios variados
                        exercicios_selecionados = []
                        composto_adicionado = False

                        for exercicio in exercicios_grupo:
                            if len(exercicios_selecionados) >= num_exercicios:
                                break

                            tipo_movimento = exercicio.get("tipo_movimento", "Isolado")

                            # Priorizar pelo menos um exercício composto por grupo
                            if tipo_movimento == "Composto" and not composto_adicionado:
                                exercicios_selecionados.append(exercicio)
                                composto_adicionado = True
                            elif (
                                tipo_movimento == "Isolado"
                                and len(exercicios_selecionados) < num_exercicios
                            ):
                                exercicios_selecionados.append(exercicio)

                        # Formatar exercícios com parâmetros
                        for exercicio in exercicios_selecionados:
                            tipo_movimento = exercicio.get("tipo_movimento", "Isolado")
                            exercise_type = (
                                "compound"
                                if tipo_movimento == "Composto"
                                else "isolation"
                            )
                            params = self.get_training_parameters(
                                objetivo, exercise_type
                            )

                            exercicio_formatado = {
                                "id": exercicio.get("id"),
                                "nome": exercicio.get("nome"),
                                "url_video": exercicio.get("url_video"),
                                "grupo_muscular": exercicio.get("grupo_muscular"),
                                "equipamento": exercicio.get("equipamento"),
                                "sets": params["sets"],
                                "reps": params["reps"],
                                "descanso": params["rest"],
                                "order": len(exercicios_dia) + 1,
                            }
                            exercicios_dia.append(exercicio_formatado)

                plan["dias_treino"][dia] = {
                    "foco": config["foco"],
                    "exercicios": exercicios_dia,
                }

            # Adicionar observações personalizadas
            plan["observacoes"].append(f"Plano personalizado para {objetivo}")
            plan["observacoes"].append("Sempre aqueça antes e alongue após os treinos")

            if gender == "feminino":
                plan["observacoes"].append(
                    "Foque na forma correta e progressão gradual"
                )

            if age > 40:
                plan["observacoes"].append(
                    "Inclua mais tempo de aquecimento e recuperação"
                )

            return json.dumps(plan, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Erro ao criar plano de treino: {str(e)}")
            return json.dumps(
                {"error": f"Erro ao criar plano: {str(e)}"}, ensure_ascii=False
            )

    def generate_plan_with_groq(self, exercises, user_data):
        """Gera plano usando Groq AI - VERSÃO SÍNCRONA"""
        try:
            exercises_json = json.dumps(exercises, ensure_ascii=False)
            user_json = json.dumps(user_data, ensure_ascii=False)

            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "create_workout_plan",
                        "description": "Cria um plano de treino personalizado baseado no perfil do usuário",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "exercises_data": {
                                    "type": "string",
                                    "description": "Dados dos exercícios disponíveis em formato JSON",
                                },
                                "user_profile": {
                                    "type": "string",
                                    "description": "Perfil do usuário com objetivo, idade, peso, etc.",
                                },
                            },
                            "required": ["exercises_data", "user_profile"],
                        },
                    },
                }
            ]

            messages = [
                {
                    "role": "system",
                    "content": """Você é um treinador personal experiente especializado em criar planos de treino personalizados. 
                    Considere sempre o objetivo, idade, gênero, peso, altura e restrições do usuário.
                    Use a ferramenta create_workout_plan para gerar planos seguros e eficazes.
                    Priorize a progressão gradual e a forma correta dos exercícios.""",
                },
                {
                    "role": "user",
                    "content": f"""Crie um plano de treino personalizado para o usuário com os seguintes dados:
                    {user_json}
                    
                    Considere:
                    - Objetivo principal do usuário
                    - Nível de condicionamento físico
                    - Restrições médicas ou físicas
                    - Gênero e idade para ajustar intensidade
                    - Variação de exercícios para evitar monotonia""",
                },
            ]

            logger.info("Enviando requisição para Groq AI...")

            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_completion_tokens=4096,
                temperature=0.3,
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                messages.append(response_message)

                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    if function_name == "create_workout_plan":
                        function_response = self.create_workout_plan(
                            exercises_data=exercises_json, user_profile=user_json
                        )

                        messages.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": function_response,
                            }
                        )

                try:
                    result = json.loads(function_response)
                    logger.info("Plano de treino gerado com sucesso")
                    return result
                except json.JSONDecodeError:
                    logger.error("Erro ao decodificar resposta JSON")
                    return {"error": "Erro ao processar resposta da IA"}

            logger.warning("Nenhuma ferramenta foi chamada pela IA")
            return {"error": "Nenhuma resposta válida da IA"}

        except Exception as e:
            logger.error(f"Erro na API Groq: {str(e)}")
            return {"error": f"Erro na API Groq: {str(e)}"}

    def format_plan_for_database(self, plan_data, user_id):
        """Formata o plano gerado para inserção no banco de dados"""
        try:
            if "error" in plan_data:
                raise Exception(plan_data["error"])

            dias_treino = plan_data.get("dias_treino", {})
            formatted_plans = []

            for dia, config in dias_treino.items():
                # Criar user_plan
                plan_id = str(uuid.uuid4())
                user_plan = {
                    "plan_id": plan_id,
                    "user_id": user_id,
                    "day": dia,
                    "title": config.get("foco", f"Treino {dia}"),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }

                # Criar plan_exercises
                plan_exercises = []
                exercicios = config.get("exercicios", [])

                for exercicio in exercicios:
                    plan_exercise = {
                        "plan_exercise_id": str(uuid.uuid4()),
                        "plan_id": plan_id,
                        "exercise_id": exercicio.get("id"),
                        "order": exercicio.get("order", 1),
                        "sets": exercicio.get("sets", 3),
                        "reps": str(exercicio.get("reps", "12")),
                    }
                    plan_exercises.append(plan_exercise)

                formatted_plans.append(
                    {"user_plan": user_plan, "plan_exercises": plan_exercises}
                )

            return {
                "plans": formatted_plans,
                "metadata": {
                    "divisao_treino": plan_data.get("divisao_treino", ""),
                    "observacoes": plan_data.get("observacoes", []),
                    "generated_at": datetime.now().isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"Erro ao formatar plano para banco: {str(e)}")
            return {"error": f"Erro ao formatar plano: {str(e)}"}


def store_workout_temporarily(page, workout_data):
    """Armazena o treino temporariamente no client storage"""
    try:
        workout_json = json.dumps(workout_data, ensure_ascii=False)
        page.client_storage.set("supafit.temp_workout", workout_json)
        logger.info("Treino armazenado temporariamente")
        return True
    except Exception as e:
        logger.error(f"Erro ao armazenar treino temporariamente: {str(e)}")
        return False


def get_temporary_workout(page):
    """Recupera o treino temporário do client storage"""
    try:
        workout_json = page.client_storage.get("supafit.temp_workout")
        if workout_json:
            return json.loads(workout_json)
        return None
    except Exception as e:
        logger.error(f"Erro ao recuperar treino temporário: {str(e)}")
        return None


def clear_temporary_workout(page):
    """Remove o treino temporário do client storage"""
    try:
        page.client_storage.remove("supafit.temp_workout")
        logger.info("Treino temporário removido")
    except Exception as e:
        logger.error(f"Erro ao remover treino temporário: {str(e)}")


def generate_and_store_workout(page, supabase_service, user_data, groq_api_key):
    """Gera treino e armazena temporariamente - VERSÃO SÍNCRONA"""
    try:
        # Buscar exercícios do banco
        exercises = supabase_service.get_all_exercises()
        if not exercises:
            raise Exception("Nenhum exercício encontrado no banco de dados")

        # Gerar treino
        generator = WorkoutGenerator(groq_api_key)
        workout_plan = generator.generate_plan_with_groq(exercises, user_data)

        if "error" in workout_plan:
            raise Exception(workout_plan["error"])

        # Armazenar temporariamente
        success = store_workout_temporarily(page, workout_plan)
        if not success:
            raise Exception("Erro ao armazenar treino temporariamente")

        logger.info("Treino gerado e armazenado temporariamente com sucesso")
        return True

    except Exception as e:
        logger.error(f"Erro ao gerar e armazenar treino: {str(e)}")
        return False


def save_workout_to_database(page, supabase_service, user_id):
    """Salva o treino temporário no banco de dados - VERSÃO SÍNCRONA"""
    try:
        # Recuperar treino temporário
        workout_data = get_temporary_workout(page)
        if not workout_data:
            raise Exception("Nenhum treino temporário encontrado")

        # Formatar para banco
        generator = WorkoutGenerator("")  # Não precisa do API key para formatação
        formatted_data = generator.format_plan_for_database(workout_data, user_id)

        if "error" in formatted_data:
            raise Exception(formatted_data["error"])

        # Salvar no banco
        for plan_data in formatted_data["plans"]:
            # Inserir user_plan
            supabase_service.create_user_plan(plan_data["user_plan"])

            # Inserir plan_exercises
            for plan_exercise in plan_data["plan_exercises"]:
                supabase_service.create_plan_exercise(plan_exercise)

        # Limpar treino temporário
        clear_temporary_workout(page)

        logger.info(f"Treino salvo no banco para user_id: {user_id}")
        return True

    except Exception as e:
        logger.error(f"Erro ao salvar treino no banco: {str(e)}")
        return False
