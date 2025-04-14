from pydantic import BaseModel, Field
from typing import Optional,List


class TransactionReport(BaseModel):
    report_type: str 
    start_date: str  # Now stored as string (dd/mm/yyyy)
    end_date: str  # Now stored as string (dd/mm/yyyy)
    total_income: float
    total_expenses: float
    spent_percentage: float
    remaining_balance: float
    generated_at: str  # Now stored as string (dd/mm/yyyy HH:MM:SS)
    report_file_url: Optional[str] = None  # Cloudinary file URL


class ReportIdsRequest(BaseModel):
    report_id: List[str]