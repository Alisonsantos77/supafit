from supabase import create_client, Client
import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
ANTHROPIC_API_URL = os.getenv("ANTHROPIC_API_URL")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")


# Supabase
class SupabaseService:
    def __init__(self):
        self.client: Client = create_client(
            os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
        )

    def login(self, email: str, password: str):
        try:
            response = self.client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            return response
        except Exception as e:
            print(f"Erro ao logar: {e}")
            return None

    def get_workouts(self, user_id: str):
        return (
            self.client.table("daily_workouts")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

    def get_exercises(self, workout_id: str):
        return (
            self.client.table("exercises")
            .select("*")
            .eq("workout_id", workout_id)
            .execute()
        )

    def update_exercise(self, exercise_id: str, data: dict):
        return (
            self.client.table("exercises").update(data).eq("id", exercise_id).execute()
        )

    def get_profile(self, user_id: str):
        return (
            self.client.table("user_profiles")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )


# Anthropic
class AnthropicService:
    @staticmethod
    def get_motivational_quote():
        try:
            headers = {
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            payload = {
                "model": "claude-3-5-sonnet-latest",
                "max_tokens": 50,
                "messages": [
                    {
                        "role": "user",
                        "content": "Forneça uma frase motivacional curta e inspiradora para alguém que está começando a treinar na academia.",
                    }
                ],
            }
            response = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"].strip()
        except Exception as e:
            logger.error(f"Erro ao gerar citação motivacional: {str(e)}")
            return "Você é mais forte do que imagina!"

    @staticmethod
    def answer_question(question, history):
        try:
            headers = {
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            messages = [
                {
                    "role": "system",
                    "content": "Você é um treinador de fitness experiente. Responda de forma amigável e profissional.",
                }
            ]
            for msg in history:
                messages.append({"role": "user", "content": msg["question"]})
                messages.append({"role": "assistant", "content": msg["answer"]})
            messages.append({"role": "user", "content": question})
            payload = {
                "model": "claude-3-5-sonnet-latest",
                "max_tokens": 500,
                "messages": messages,
            }
            response = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"].strip()
        except Exception as e:
            logger.error(f"Erro ao responder pergunta: {str(e)}")
            return "Desculpe, não consegui responder agora. Tente novamente!"

    @staticmethod
    def get_training_tip(exercise_name: str, level: str):
        try:
            headers = {
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            prompt = f"Forneça uma dica prática e específica para melhorar a execução do exercício '{exercise_name}' para uma pessoa de nível {level}."
            payload = {
                "model": "claude-3-5-sonnet-latest",
                "max_tokens": 100,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            }
            response = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"].strip()
        except Exception as e:
            logger.error(f"Erro ao gerar dica de treino: {str(e)}")
            return "Mantenha a postura correta e respire adequadamente!"

    @staticmethod
    def generate_workout_plan(day: str, user_level: str, supabase):
        try:
            headers = {
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            prompt = f"Crie um plano de treino para o dia {day} para uma pessoa de nível {user_level}. Inclua 4-6 exercícios com nome, séries, repetições e carga sugerida (se aplicável)."
            payload = {
                "model": "claude-3-5-sonnet-latest",
                "max_tokens": 500,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            }
            response = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            plan = data["content"][0]["text"].strip()
            supabase.client.table("workouts").insert(
                {"day": day, "name": f"Treino {day.capitalize()}", "description": plan}
            ).execute()
            return plan
        except Exception as e:
            logger.error(f"Erro ao gerar plano de treino: {str(e)}")
            return "Não foi possível gerar o plano de treino. Tente novamente!"


# Unsplash
def get_unsplash_image(query):
    access_key = UNSPLASH_ACCESS_KEY
    url = f"https://api.unsplash.com/search/photos?query={query}&client_id={access_key}"
    response = requests.get(url)
    data = response.json()
    print(f"Imagem retornada: {data}")
    if data["results"]:
        return data["results"][0]["urls"]["regular"]
    return "https://picsum.photos/200"
