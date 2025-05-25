from typing import Optional
from pydantic import BaseModel

class State(BaseModel):
    user_message: str
    response: Optional[str] = None
    output: Optional[str] = None