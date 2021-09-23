from enum import auto, Enum
from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    role: str
    first_name: Optional[str]

    class Config:
        deep_query = {"role": {"regex": "|".join(["admin", "developer"])}}


class Role(str, Enum):
    admin = auto()
    developer = auto()


class UserWithEnum(BaseModel):
    role: Role
    first_name: Optional[str]
