from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Victory:
    """Model para representar uma vitória da comunidade"""

    id: Optional[str] = None
    user_id: str = ""
    content: str = ""
    category: str = "Geral"
    created_at: Optional[datetime] = None
    author_name: str = ""
    likes: int = 0
    liked: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "Victory":
        """Cria uma instância Victory a partir de um dicionário"""
        victory = cls()
        victory.id = data.get("id")
        victory.user_id = data.get("user_id", "")
        victory.content = data.get("content", "")
        victory.category = data.get("category", "Geral")
        victory.author_name = data.get("author_name", "")
        victory.likes = data.get("likes", 0)
        victory.liked = data.get("liked", False)

        # Parse da data
        created_at_str = data.get("created_at", "")
        if created_at_str:
            try:
                victory.created_at = datetime.fromisoformat(
                    created_at_str.replace("Z", "+00:00")
                )
            except ValueError:
                victory.created_at = None

        return victory

    def get_formatted_date(self) -> str:
        """Retorna a data formatada para exibição"""
        if self.created_at:
            return self.created_at.strftime("%d/%m/%Y %H:%M")
        return "Data desconhecida"


@dataclass
class VictoryPost:
    """Model para criar uma nova vitória"""

    user_id: str
    content: str
    category: str
    created_at: datetime

    def to_dict(self) -> dict:
        """Converte para dicionário para inserção no banco"""
        return {
            "user_id": self.user_id,
            "content": self.content,
            "category": self.category,
            "created_at": self.created_at.isoformat(),
        }
