from pydantic import BaseModel

class AdResponse(BaseModel):
    title: str
    message: str
    image_url: str | None  # Allow None if no image found
