import os
import logging
import requests
import httpx
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ANTHROPIC_API_URL = os.getenv("ANTHROPIC_API_URL")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")


class SupabaseService:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.error(
                "SUPABASE_URL e SUPABASE_KEY devem ser definidos nas variáveis de ambiente."
            )
            raise ValueError("Faltando configuração do Supabase")
        try:
            self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Supabase client inicializado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao inicializar o cliente Supabase: {e}")
            raise

    def login(self, email: str, password: str):
        try:
            logger.info(f"Tentando fazer login com o email: {email}")
            response = self.client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            logger.info("Login com sucesso.")
            if response.error:
                logger.error(f"Erro ao fazer login: {response.error}")
                return None
            return response
        except Exception as e:
            logger.error(f"Erro ao fazer login: {e}")
            return None

    def get_workouts(self, user_id: str):
        try:
            logger.info(f"Buscando treinos para o user_id: {user_id}")
            return (
                self.client.table("daily_workouts")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )
        except Exception as e:
            logger.error(f"Erro ao buscar treinos: {e}")
            raise

    def get_exercises(self, workout_id: str):
        try:
            logger.info(f"Buscando exercícios para o workout_id: {workout_id}")
            return (
                self.client.table("exercises")
                .select("*")
                .eq("workout_id", workout_id)
                .execute()
            )
        except Exception as e:
            logger.error(f"Erro ao buscar exercícios: {e}")
            raise

    def update_exercise(self, exercise_id: str, data: dict):
        try:
            logger.info(f"Atualizando exercício {exercise_id} com {data}")
            return (
                self.client.table("exercises")
                .update(data)
                .eq("id", exercise_id)
                .execute()
            )
        except Exception as e:
            logger.error(f"Erro ao atualizar exercício: {e}")
            raise

    def get_profile(self, user_id: str):
        try:
            logger.info(f"Buscando perfil para o user_id: {user_id}")
            return (
                self.client.table("user_profiles")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )
        except Exception as e:
            logger.error(f"Error fetching profile: {e}")
            raise


class AnthropicService:
    def __init__(
        self, api_key: str = ANTHROPIC_API_KEY, base_url: str = ANTHROPIC_API_URL
    ):
        if not api_key or not base_url:
            logger.error(
                "ANTHROPIC_API_KEY and ANTHROPIC_API_URL must be set in environment variables."
            )
            raise ValueError("Missing Anthropic configuration")
        self.api_key = api_key
        self.base_url = base_url
        logger.info("AnthropicService initialized with base_url: %s", self.base_url)

    def get_motivational_quote(self) -> str:
        try:
            logger.info("Requesting motivational quote from Anthropic.")
            headers = {
                "x-api-key": self.api_key,
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
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            quote = data["content"][0]["text"].strip()
            logger.info("Received motivational quote.")
            return quote
        except Exception as e:
            logger.error(f"Error generating motivational quote: {e}")
            return "Você é mais forte do que imagina!"

    def answer_question(self, question: str, history: list) -> str:
        """
        Envia a pergunta e o histórico para a API da Anthropic e retorna o texto da resposta.
        Usa modelo 'claude-3-5-sonnet-latest' para maior qualidade.
        """
        try:
            logger.info("Sending question to Anthropic: %s", question)
            # Monta o payload com histórico + nova pergunta
            messages = []
            for item in history:
                messages.append({"role": "user", "content": item.get("question", "")})
                messages.append({"role": "assistant", "content": item.get("answer", "")})
            messages.append({"role": "user", "content": question})

            payload = {
                "model": "claude-3-5-sonnet-latest",
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7,
            }
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            }
            # Chama o endpoint v1/messages
            response = httpx.post(
                f"{self.base_url}/v1/messages" if not self.base_url.endswith('/v1/messages') else self.base_url,
                json=payload,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            # Analisa resposta, pode variar conforme a versão da API
            # Tenta primeiro 'content', depois 'completion'
            if "content" in data and isinstance(data["content"], list):
                text = data["content"][0].get("text", "").strip()
            elif "completion" in data:
                # para versões que retornam {'completion': 'texto...'}
                text = data["completion"].strip()
            else:
                # fallback: converte tudo em string
                text = str(data)

            logger.info("Received answer from Anthropic: %s", text[:50])
            return text

        except httpx.HTTPStatusError as ex:
            error_text = ex.response.text or str(ex)
            logger.error(
                "Anthropic API returned status %s: %s", ex.response.status_code, error_text
            )
            raise
        except Exception as ex:
            logger.error(f"Unexpected error in answer_question: {ex}")
            return "Desculpe, não consegui responder agora."

    def get_training_tip(self, exercise_name: str, level: str) -> str:
        try:
            logger.info(
                "Requesting training tip for '%s' at level '%s'.", exercise_name, level
            )
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            prompt = f"Forneça uma dica prática e específica para melhorar a execução do exercício '{exercise_name}' para uma pessoa de nível {level}."
            payload = {
                "model": "claude-3-5-sonnet-latest",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": prompt}],
            }
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            tip = data["content"][0]["text"].strip()
            logger.info("Received training tip.")
            return tip
        except Exception as e:
            logger.error(f"Error generating training tip: {e}")
            return "Mantenha a postura correta e respire adequadamente!"

    def generate_workout_plan(
        self, day: str, user_level: str, supabase: SupabaseService
    ) -> str:
        try:
            logger.info(
                "Generating workout plan for day '%s' at level '%s'.", day, user_level
            )
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            prompt = f"Crie um plano de treino para o dia {day} para uma pessoa de nível {user_level}. Inclua 4-6 exercícios com nome, séries, repetições e carga sugerida (se aplicável)."
            payload = {
                "model": "claude-3-5-sonnet-latest",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}],
            }
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            plan = data["content"][0]["text"].strip()
            # Insert into Supabase
            supabase.client.table("workouts").insert(
                {"day": day, "name": f"Treino {day.capitalize()}", "description": plan}
            ).execute()
            logger.info("Workout plan generated and saved to database.")
            return plan
        except Exception as e:
            logger.error(f"Error generating workout plan: {e}")
            return "Não foi possível gerar o plano de treino. Tente novamente!"


def get_unsplash_image(query: str) -> str:
    if not UNSPLASH_ACCESS_KEY:
        logger.error("UNSPLASH_ACCESS_KEY is not set in environment variables.")
        return "https://picsum.photos/200"
    try:
        logger.info(f"Fetching Unsplash image for query: {query}")
        url = f"https://api.unsplash.com/search/photos?query={query}&client_id={UNSPLASH_ACCESS_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        if results:
            image_url = results[0]["urls"]["regular"]
            logger.info("Unsplash image fetched successfully.")
            return image_url
        logger.warning("No Unsplash results for query: %s", query)
        return "https://picsum.photos/200"
    except Exception as e:
        logger.error(f"Error fetching Unsplash image: {e}")
        return "https://picsum.photos/200"
