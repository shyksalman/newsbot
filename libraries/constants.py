from dataclasses import dataclass


@dataclass
class NewsArticle:
    title: str
    date: str
    description: str
    profile_picture: str