from datetime import datetime


def format_date(date: str) -> str:
    return datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y")
