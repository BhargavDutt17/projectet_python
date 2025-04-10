from pydantic import BaseModel
from typing import Optional

class UserReport(BaseModel):
    user_id: str
    username: str
    generated_at: str
    report_file_url: Optional[str] = None
    report_name: str
