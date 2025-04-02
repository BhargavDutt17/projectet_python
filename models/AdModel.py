from pydantic import BaseModel

class AdResponse(BaseModel):
    title: str
    message: str
