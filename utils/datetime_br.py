# utils/datetime_br.py

from datetime import datetime
from zoneinfo import ZoneInfo

ZONE_BR = ZoneInfo("America/Sao_Paulo")

dias_semana_pt = {
    "Monday": "segunda-feira",
    "Tuesday": "terça-feira",
    "Wednesday": "quarta-feira",
    "Thursday": "quinta-feira",
    "Friday": "sexta-feira",
    "Saturday": "sábado",
    "Sunday": "domingo",
}


def get_datetime_br():
    """Retorna informações completas da data/hora atual no fuso de São Paulo."""
    now = datetime.now(ZONE_BR)

    return {
        "datetime": now,
        "hora": now.strftime("%H:%M:%S"),
        "data": now.strftime("%d/%m/%Y"),
        "data_hora": now.strftime("%H:%M:%S -03 %d/%m/%Y"),
        "dia_semana_en": now.strftime("%A"),
        "dia_semana_pt": dias_semana_pt[now.strftime("%A")],
        "formato_extenso": f"{dias_semana_pt[now.strftime('%A')].capitalize()}, {now.strftime('%d/%m/%Y %H:%M')}",
    }
