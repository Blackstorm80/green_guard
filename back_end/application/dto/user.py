# back_end/application/dto/user.py
from pydantic import BaseModel


class UserDTO(BaseModel):
    id: int
    name: str
    email: str
    role: str  # "admin", "manager", etc.