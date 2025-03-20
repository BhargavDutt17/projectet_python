from fastapi import APIRouter
from models.TransactionModel import Transaction
from controllers import TransactionController

router = APIRouter()

@router.post("/addTransaction")
async def post_transaction(transaction: Transaction):
    return await TransactionController.addTransaction(transaction)

@router.get("/getAllTransactions")
async def get_all_transactions():
    return await TransactionController.getAllTransactions()

@router.get("/getTransactionByUserId/{user_id}")
async def get_transaction_by_user_id(user_id: str):
    return await TransactionController.getTransactionByUserId(user_id)

# Report Generation Endpoint
@router.post("/generateTransactionReport")
async def generate_transaction_report(
    user_id: str,
    start_date: str,
    end_date: str
):
    return await TransactionController.generateTransactionReport(user_id, start_date, end_date)

# Get Specific Report by `report_id`
@router.get("/getTransactionReport/{report_id}")
async def get_transaction_report(report_id: str):
    return await TransactionController.getTransactionReport(report_id)

# Get Latest Transaction Report for a User
@router.get("/getLatestTransactionReport/{user_id}")
async def get_latest_transaction_report(user_id: str):
    return await TransactionController.getLatestTransactionReport(user_id)

# Get All Reports for a User (For Report Page)
@router.get("/getAllTransactionReports/{user_id}")
async def get_all_transaction_reports(user_id: str):
    return await TransactionController.getAllTransactionReports(user_id)
