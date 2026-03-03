from typing import Optional
from pydantic import BaseModel
"""  token d'indentification pour les users (utliser en auth, ...)"""
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None