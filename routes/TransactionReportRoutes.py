from fastapi import APIRouter, HTTPException
from controllers.TransactionReportController import generate_transaction_report, get_transaction_report

router = APIRouter()

@router.post("/generateTransactionReport")
async def generate_transaction_report_endpoint(
    user_id: str,
    report_type: str,
    start_date: str,  # dd/mm/yyyy
    end_date: str  # dd/mm/yyyy
):
    try:
        result = await generate_transaction_report(user_id, report_type, start_date, end_date)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/getTransactionReport/{report_id}")
async def get_transaction_report_endpoint(report_id: str):
    try:
        result = await get_transaction_report(report_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
