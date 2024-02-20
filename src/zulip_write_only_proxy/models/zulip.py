import enum
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, HttpUrl, SecretStr


class PropagateMode(str, enum.Enum):
    change_one = "change_one"
    change_all = "change_all"
    change_later = "change_later"


class BotConfig(BaseModel):
    name: str
    email: EmailStr
    api_key: SecretStr
    site: Annotated[HttpUrl, Field(default="https://mylog.connect.xfel.eu/")]
    id: int


MessageID = int


class Message(BaseModel):
    topic: str
    id: MessageID
    content: str


class Messages(BaseModel):
    found_newest: bool
    found_oldest: bool
    messages: list[Message]
    client: str