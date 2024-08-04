from pydantic import BaseModel
from typing import Optional


class ArticleModel(BaseModel):
    title: Optional[str] = ""
    date: Optional[str] = ""
    description: Optional[str] = ""
    profile_picture: Optional[str] = ""
    phrase: Optional[int] = 0
    amount: Optional[str] = ""
