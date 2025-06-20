import re
import random
import time
import logging


# Filtro para substituir caracteres Unicode problemáticos
class UnicodeFilter(logging.Filter):
    def filter(self, record):
        if record.msg and isinstance(record.msg, str):
            record.msg = record.msg.encode("ascii", "replace").decode("ascii")
        if record.args:
            record.args = tuple(
                (
                    arg.encode("ascii", "replace").decode("ascii")
                    if isinstance(arg, str)
                    else arg
                )
                for arg in record.args
            )
        return True


from utils.logger import get_logger

logger = get_logger("supabafit.quebra_mensagem")

"""
Arquivo para manipulação de textos no chat do SupaFit, 
especialmente para o trainer_tab.py, garantindo que respostas 
longas sejam quebradas de forma natural e fluida.
"""


def calculate_typing_delay(message: str) -> float:
    """
    Calcula o delay de digitação para simular um treinador digitando.
    Baseado no tamanho da mensagem e otimizado para respostas de fitness.

    Args:
        message (str): Mensagem a ser exibida.

    Returns:
        float: Tempo em segundos para o delay.
    """
    try:
        # Ajustado para respostas de fitness: 60 palavras por minuto
        typing_speed_wpm = 60
        words = len(message.split())
        typing_time = words / typing_speed_wpm  # Tempo em minutos
        typing_time_seconds = typing_time * 60  # Converte para segundos
        typing_time_seconds = max(
            1, min(round(typing_time_seconds, 2), 8)
        )  # Entre 1 e 8 segundos
        logger.info(f"Delay calculado para '{message[:50]}...': {typing_time_seconds}s")
        return typing_time_seconds
    except Exception as ex:
        logger.error(f"Erro ao calcular delay de digitação: {ex}")
        return 3.0  # Valor padrão em caso de erro


def is_list_item(line: str) -> bool:
    """
    Verifica se a linha é um item de lista (numerada ou com bullet) comum em planos de treino.
    Exemplo: "1. Agachamento" ou "- Flexão".

    Args:
        line (str): Linha de texto a verificar.

    Returns:
        bool: True se for item de lista, False caso contrário.
    """
    return bool(re.match(r"^\s*(\d+\.\s+|-|\*)\s*", line.strip()))


def process_fitness_list(items: list) -> list:
    """
    Concatena itens consecutivos de lista Markdown em uma única mensagem,
    substituindo '**' por '*' e adicionando uma mensagem introdutória para listas
    com mais de 3 itens, no contexto de fitness.

    Args:
        items (list): Lista de strings a processar.

    Returns:
        list: Lista de mensagens processadas.
    """
    result = []
    i = 0
    while i < len(items):
        if is_list_item(items[i]):
            block_items = [items[i]]
            j = i + 1
            while j < len(items) and is_list_item(items[j]):
                block_items.append(items[j])
                j += 1
            # Se o bloco tem mais de 3 itens, adiciona uma mensagem introdutória
            if len(block_items) > 3:
                pre_list = [
                    "Aguarde um instante, vou te passar o plano de treino! 💪",
                    "Um momento, estou organizando os exercícios pra você! 🏋️",
                    "Só um segundinho, vou listar suas atividades! 🏃",
                    "Espere um pouquinho, estou montando seu treino! 🔥",
                    "Dá um minutinho, vou detalhar seus exercícios! 💪",
                ]
                result.append(random.choice(pre_list))
            # Concatena itens com quebra de linha e substitui negrito
            combined = "\n".join(block_items).replace("**", "*")
            result.append(combined)
            i = j
        else:
            result.append(items[i])
            i += 1
    logger.info(f"Processadas {len(result)} mensagens após tratamento de listas")
    return result


def break_messages(text: str, break_probability: float = 0.5) -> list:
    """
    Quebra mensagens longas em pedaços menores, preservando listas de treino
    e simulando uma experiência de chat natural. Otimizado para o SupaFit.

    Args:
        text (str): Texto a ser segmentado.
        break_probability (float): Probabilidade de quebra em pontos naturais.

    Returns:
        list: Lista de mensagens segmentadas.
    """
    messages = []
    current_message = ""

    try:
        # Proteger valores monetários (ex.: R$100,00)
        currency_pattern = r"R\$\d{1,3}(?:\.\d{3})*,\d{2}"
        currencies = re.findall(currency_pattern, text)
        currency_placeholders = {}
        for i, currency in enumerate(currencies):
            placeholder = f"<CURRENCY_{i}>"
            currency_placeholders[placeholder] = currency
            text = text.replace(currency, placeholder)

        # Proteger números de telefone (ex.: (11) 99999-9999)
        phone_pattern = r"\(\d{2}\)\s*\d{4,5}-\d{4}"
        phones = re.findall(phone_pattern, text)
        phone_placeholders = {}
        for i, phone in enumerate(phones):
            placeholder = f"<PHONE_{i}>"
            phone_placeholders[placeholder] = phone
            text = text.replace(phone, placeholder)

        # Inserir quebras antes de itens de lista
        text = re.sub(r"(?<!\n)(^\d+\.\s+|^[-*]\s+)", r"\n\1", text, flags=re.MULTILINE)

        # Dividir em linhas
        lines = text.split("\n")
        contains_list = any(is_list_item(line) for line in lines)

        if contains_list:
            # Processar linha por linha para listas (comuns em planos de treino)
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if is_list_item(line):
                    if current_message:
                        messages.append(current_message.strip())
                        current_message = ""
                    messages.append(line)
                else:
                    current_message += line + " "
            if current_message:
                messages.append(current_message.strip())
        else:
            # Divisão simples por sentenças para textos sem listas
            sentences = re.split(r"(?<=[.!?])\s+", text.strip())
            for sentence in sentences:
                if sentence:
                    current_message += sentence + " "
                    if random.random() < break_probability:
                        messages.append(current_message.strip())
                        current_message = ""
            if current_message:
                messages.append(current_message.strip())

        # Restaurar placeholders
        for placeholder, currency in currency_placeholders.items():
            messages = [msg.replace(placeholder, currency) for msg in messages]
        for placeholder, phone in phone_placeholders.items():
            messages = [msg.replace(placeholder, phone) for msg in messages]

        # Processar listas de treino
        messages = process_fitness_list(messages)
        logger.info(f"Texto quebrado em {len(messages)} mensagens")

    except Exception as ex:
        logger.error(f"Erro ao quebrar mensagens: {ex}")
        messages = [text]  # Fallback para o texto original

    return messages


def integrate_with_chat(message: str) -> list:
    """
    Integra a quebra de mensagens com delay para o chat do trainer_tab.py.

    Args:
        message (str): Mensagem original do treinador.

    Returns:
        list: Lista de tuplas com (mensagem, delay).
    """
    messages = break_messages(message, break_probability=0.5)
    return [(msg, calculate_typing_delay(msg)) for msg in messages]
