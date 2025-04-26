from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()


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
