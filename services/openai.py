import asyncio
from datetime import datetime
import os
import json
import httpx
import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv
from services.supabase import SupabaseService
from utils.logger import get_logger
from services.trainer_functions import FUNCTION_MAP, get_user_plan

logger = get_logger("supafit.services")


class OpenAIService:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1/chat/completions"
        openai.api_key = self.api_key
        self.client = AsyncOpenAI(api_key=self.api_key)
        logger.info(f"Serviço OpenAI inicializado com base_url: {self.base_url}")

    def get_workout_plan(self, user_data: dict):
        """Gera um plano de treino personalizado com base nos dados do usuário.

        Args:
            user_data (dict): Dados do usuário (nível, objetivo, peso, altura, idade).

        Returns:
            str: Plano de treino gerado.

        Raises:
            Exception: Se a geração do plano falhar.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        prompt = f"""
        Crie um plano de treino personalizado com base nos seguintes dados do usuário:
        - Nível: {user_data.get('level', '')}
        - Objetivo: {user_data.get('goal', '')}
        - Peso: {user_data.get('weight', '')} kg
        - Altura: {user_data.get('height', '')} cm
        - Idade: {user_data.get('age', '')} anos

        Forneça um plano de treino semanal, com exercícios, séries, repetições e dias da semana.
        """
        data = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.7,
        }
        try:
            response = httpx.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            logger.info("Plano de treino gerado com sucesso pelo OpenAI.")
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Erro ao gerar plano de treino com OpenAI: {str(e)}")
            raise e

    async def answer_question(
        self, question: str, history: list, system_prompt: str = None
    ) -> str:
        """Envia a pergunta, histórico e prompt do sistema para a API da OpenAI e retorna a resposta.

        Args:
            question (str): Pergunta do usuário.
            history (list): Histórico de mensagens no formato [{"role": "user/assistant", "content": "..."}].
            system_prompt (str, optional): Prompt do sistema para personalizar a resposta.

        Returns:
            str: Resposta gerada pela API.

        Raises:
            httpx.HTTPStatusError: Se a chamada à API falhar.
        """
        try:
            logger.info("Enviando pergunta para OpenAI: %s", question)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
                logger.debug("Prompt do sistema incluído: %s", system_prompt[:50])
            for item in history:
                if item.get("role") in ["user", "assistant"] and item.get("content"):
                    messages.append({"role": item["role"], "content": item["content"]})
            messages.append({"role": "user", "content": question})

            payload = {
                "model": "gpt-4o",
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7,
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url, json=payload, headers=headers, timeout=30
                )
                response.raise_for_status()
                data = response.json()
                text = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
                logger.info("Resposta recebida de OpenAI: %s", text[:50])
                return text
        except httpx.HTTPStatusError as ex:
            error_text = ex.response.text or str(ex)
            logger.error(
                f"API OpenAI retornou status #{ex.response.status_code}: {error_text}"
            )
            raise
        except Exception as ex:
            logger.error(f"Erro inesperado em answer_question: {ex}")
            return "Desculpe, não consegui responder agora."

    def is_sensitive_question(self, question: str) -> bool:
        """Verifica se a pergunta contém conteúdo sensível ou inadequado usando a API da OpenAI.

        Args:
            question (str): Pergunta a ser verificada.

        Returns:
            bool: True se for sensível, False caso contrário.
        """
        try:
            moderation_prompt = f"""
            Você é um moderador virtual treinado para filtrar postagens em uma comunidade fitness.
            Sua tarefa é analisar o texto da postagem e **retornar única e exclusivamente** uma dessas duas respostas:
            - "sensitive"
            - "safe"

            1) [80% Prevenção] Se o texto contiver qualquer um dos seguintes elementos, retorne "sensitive":
            - Termos ou insinuações sexuais explícitas
            - Discurso de ódio ou linguagem tóxica
            - Descrições gráficas de violência ou automutilação
            - Exposição de dados pessoais sensíveis (ex.: CPF, endereço)
            - Conteúdo que incentive comportamento perigoso ou ilegal

            2) [20% Ação] Caso contrário, retorne "safe".
            
            Texto a verificar: {question}
            """
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": moderation_prompt}],
                "max_tokens": 2,
                "temperature": 0.0,
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            response = httpx.post(
                self.base_url, json=payload, headers=headers, timeout=10
            )
            response.raise_for_status()
            data = response.json()
            text = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            return text.lower() == "sensitive"
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP ao verificar pergunta sensível: {e.response.text}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Erro de decodificação JSON: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar pergunta sensível: {str(e)}")
            return False

    def is_sensitive_name(self, name: str) -> bool:
        """Verifica se o nome contém conteúdo sensível ou inadequado usando a API da OpenAI."""
        try:
            moderation_prompt = f"""
            Você é um verificador de nomes de usuário em uma plataforma fitness.
            Sua tarefa é analisar o nome proposto e **retornar única e exclusivamente** uma dessas duas respostas:
            - "sensitive"
            - "safe"

            1) [80% Prevenção] Se o nome contiver qualquer um dos seguintes elementos, retorne "sensitive":
            - Palavrões, insultos ou termos de ódio
            - Implicação de marca registrada sem autorização
            - Conteúdo sexualmente sugestivo ou explícito
            - Dados pessoais de terceiros (ex.: CPF, RG)
            - Imitação de nomes de staff ou moderadores

            2) [20% Ação] Caso contrário, retorne "safe".

            Nome a verificar: {name}
            """
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": moderation_prompt}],
                "max_tokens": 2,
                "temperature": 0.0,
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            response = httpx.post(
                self.base_url, json=payload, headers=headers, timeout=10
            )
            response.raise_for_status()
            data = response.json()
            text = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            return text.lower() == "sensitive"
        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP ao verificar nome sensível: {e.response.text}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Erro de decodificação JSON: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar nome sensível: {str(e)}")
            return False

    def is_sensitive_restrictions(self, text: str) -> bool:
        """Verifica se o texto contém conteúdo sensível usando a API da OpenAI.

        Args:
            text (str): Texto a ser verificado (restrições do usuário).

        Returns:
            bool: True se o texto contém conteúdo sensível, False caso contrário.
        """
        try:
            moderation_prompt = f"""
            Você é um assistente que coleta informações de lesões e limitações físicas em uma aplicação fitness.
            Sua tarefa é analisar o relato do usuário e **retornar única e exclusivamente** uma dessas duas respostas:
            - "sensitive"
            - "safe"

            1) [80% Prevenção] Se o texto contiver qualquer um dos seguintes elementos, retorne "sensitive":
            - Descrições gráficas de ferimentos (ex.: “ossos expostos”, “sangue em abundância”)
            - Dados de saúde vinculados a informações pessoais identificáveis (ex.: CPF, data de nascimento)
            - Ausência de qualquer termo que indique lesão ou dor (ex.: “lesão”, “fratura”, “luxação”, “dor”)

            2) [20% Ação] Se o texto for um relato objetivo de lesão ou limitação (contiver termos como “lesão”, “fratura”, “dor” sem os elementos acima), retorne "safe".

            Texto a verificar: {text}
            """
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": moderation_prompt}],
                "max_tokens": 2,
                "temperature": 0.0,
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            response = httpx.post(
                self.base_url, json=payload, headers=headers, timeout=10
            )
            response.raise_for_status()
            data = response.json()
            text = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            return text.lower() == "sensitive"
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Erro HTTP ao verificar restrições sensíveis: {e.response.text}"
            )
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Erro de decodificação JSON: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar restrições sensíveis: {str(e)}")
            return False

    @staticmethod
    def get_system_prompt(user_data: dict, user_id: str) -> str:
        return f"""
    # IDENTIDADE E PAPEL PRINCIPAL
    Você é Coach Coachito, treinador virtual do SupaFit, um personal trainer experiente, motivacional e dedicado ao sucesso do aluno. Sua missão é ser um parceiro de treino conhecedor, paciente e focado em resultados reais, utilizando dados do perfil e plano de treino do usuário para personalização.

    ## PERSONALIDADE E COMUNICAÇÃO
    - Tom: Amigável, motivacional, profissional, como um treinador que se importa.
    - Estilo: Conversacional, humano, evitando linguagem robótica ou formal.
    - Emojis: Use 1-2 por resposta para entusiasmo ou conquistas.
    - Tratamento: Use o nome do usuário quando disponível para conexão pessoal.

    ## DADOS DO ALUNO (Contexto Personalizado)
    - Nome: {user_data.get('name', 'Campeão(ã)')}
    - Idade: {user_data.get('age', 'N/A')} anos
    - Peso Atual: {user_data.get('weight', 'N/A')} kg
    - Altura: {user_data.get('height', 'N/A')} cm
    - Objetivo Principal: {user_data.get('goal', 'N/A')}
    - Nível de Experiência: {user_data.get('level', 'N/A')}
    - Restrições: {user_data.get('restrictions', 'Nenhuma')}
    - Data/Hora: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
    - Plano de Treino: {get_user_plan(SupabaseService.get_instance(), user_id) if user_id else 'N/A'}

    ## DIRETRIZES FUNDAMENTAIS (80% Prevenção)
    ### ⚠️ SEGURANÇA EM PRIMEIRO LUGAR
    - Use a função `get_user_profile` para verificar limitações físicas ou lesões antes de recomendar exercícios.
    - SEMPRE sugira consulta médica para programas intensos ou se houver relatos de dor/desconforto.
    - Identifique sinais de overtraining (fadiga, dores persistentes) e interrompa orientações se necessário.
    - Use `is_sensitive_question` para filtrar perguntas inadequadas; retorne "Pergunta sensível detectada" se aplicável.

    ### 🚫 LIMITAÇÕES PROFISSIONAIS
    - NÃO prescreva medicamentos, suplementos ou dietas restritivas.
    - NÃO diagnostique lesões ou condições médicas.
    - Direcione para médicos ou nutricionistas quando necessário.
    - Evite respostas fora do escopo fitness (ex.: questões médicas, financeiras).

    ### 🎯 PERSONALIZAÇÃO OBRIGATÓRIA
    - Use `get_user_plan` para acessar o plano de treino e adaptar recomendações.
    - Considere nível de experiência, objetivo, restrições, tempo e equipamentos disponíveis.
    - Se o usuário relatar dor, use `find_substitutes` para sugerir exercícios alternativos e `update_plan_exercise` para atualizar o plano.
    - Mantenha respostas coerentes com o objetivo e histórico do usuário.

    ### 📚 EDUCAÇÃO E CONSCIÊNCIA
    - Explique o motivo das recomendações (ex.: benefícios do exercício).
    - Promova progressão segura, descanso e mindset de longo prazo.
    - Eduque sobre técnica, recuperação e hidratação.

    ## AÇÕES DIRETAS (20% Ação)
    ### 💪 ORIENTAÇÃO DE EXERCÍCIOS
    - Use `get_user_plan` para recomendar exercícios do plano atual.
    - Forneça 3-5 exercícios com:
    - Séries/repetições ajustadas ao nível.
    - Descrição clara da execução.
    - Progressões/regressões.
    - Aquecimento e descanso entre séries.
    - Inclua sinais para parar (ex.: dor aguda, tontura).
    - Se necessário, use `find_substitutes` para substituições seguras.

    ### 🍎 ORIENTAÇÕES NUTRICIONAIS GERAIS
    - Oriente sobre:
    - Alimentação saudável (ex.: equilíbrio de macronutrientes).
    - Timing de nutrição (pré/pós-treino).
    - Hidratação.
    - NÃO prescreva dietas específicas ou calorias exatas.

    ### 🎉 MOTIVAÇÃO E SUPORTE
    - Celebre progressos e pequenas vitórias.
    - Transforme obstáculos em oportunidades (ex.: sugerir alternativas).
    - Mantenha expectativas realistas e motive confiança.

    ## PADRÕES DE RESPOSTA
    ### Para Iniciantes:
    - Foque em movimentos básicos (ex.: agachamento com peso corporal).
    - Enfatize técnica e progressão gradual.
    - Explique benefícios simples.

    ### Para Intermediários/Avançados:
    - Sugira variações desafiadoras (ex.: agachamento com carga).
    - Discuta periodização e técnicas avançadas.
    - Use dados do plano para maior precisão.

    ### Para Dúvidas Gerais:
    - Responda de forma educativa, conectando ao objetivo.
    - Sugira próximos passos práticos.
    - Use histórico (`history_cache`) para manter contexto.

    ## INTEGRAÇÃO COM FERRAMENTAS
    - get_user_profile: Obtenha dados do perfil antes de responder.
    - get_user_plan: Consulte o plano de treino para recomendações.
    - find_substitutes: Sugira alternativas se o usuário relatar dor.
    - update_plan_exercise: Atualize o plano com substituições aprovadas.
    - Persista interações no Supabase via `trainer_qa` para histórico.

    ## EXEMPLO DE RESPOSTA IDEAL
    Oi {user_data.get('name', 'Campeão(ã)')}! 💪 Com base no seu objetivo de {user_data.get('goal', 'N/A')} e nível {user_data.get('level', 'N/A')}, aqui está uma sugestão do seu plano de treino para hoje:

    [Lista de exercícios do plano, com séries/repetições]

    **Por que isso?** [Explicação do benefício].  
    **Dica**: [Princípio educativo, ex.: descanso adequado].  
    Lembre-se: se sentir dor, pare e me avise para ajustarmos com alternativas seguras! 😊 Como estão seus treinos? Alguma dúvida?

    ## LEMBRETE FINAL
    Você é um parceiro de jornada fitness. Use as ferramentas do SupaFit (`get_user_profile`, `get_user_plan`, `find_substitutes`, `update_plan_exercise`) para respostas precisas e seguras. Cada interação deve motivar, informar e aumentar a confiança do usuário em seus objetivos de forma sustentável.
    """

    async def chat_with_functions(
        self, messages: list, functions: list, function_call: str = "auto"
    ):
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            functions=functions,
            function_call=function_call,
        )
        return response

    async def execute_function_by_name(self, name: str, arguments: dict):
        func = FUNCTION_MAP.get(name)
        if not func:
            raise ValueError(f"Função '{name}' não registrada em FUNCTION_MAP")
        if asyncio.iscoroutinefunction(func):
            return await func(**arguments)
        return func(**arguments)
