from fastapi import APIRouter,Body
from models.TransactionModel import Transaction,TransactionUpdate
from controllers import TransactionController
from typing import Optional


router = APIRouter()


@router.post("/addTransaction")
async def post_transaction(transaction: Transaction):
    return await TransactionController.addTransaction(transaction)


@router.get("/getAllTransactions")
async def get_all_transactions():
    return await TransactionController.getAllTransactions()


@router.get("/getTransactionByUserId/{user_id}")
async def get_transaction_by_user_id(user_id: str, month: int = None, year: int = None):
    return await TransactionController.getTransactionByUserId(user_id, month, year)



# Report Generation Endpoint
@router.post("/generateTransactionReport")
async def generate_transaction_report(
    user_id: str,start_date: str = "",end_date: str = "",category_id: str = "",subcategory_id: str = ""
):
    return await TransactionController.generateTransactionReport(
        user_id, start_date, end_date, category_id, subcategory_id
    )

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


@router.delete("/transaction-reports/{report_id}")
async def delete_transaction_report(report_id: str):
    return await TransactionController.delete_transaction_report(report_id)


@router.delete("/deleteTransaction/{transaction_id}")
async def delete_transaction(transaction_id: str, user_id: Optional[str] = None):
    return await TransactionController.deleteTransaction(transaction_id, user_id)

from typing import Dict

@router.put("/editTransaction/{transaction_id}")
async def edit_transaction(
    transaction_id: str, 
    updated_data: TransactionUpdate = Body(...)
):
    # Convert Pydantic model to dictionary and remove unset values (None)
    update_dict = updated_data.dict(exclude_unset=True)
    return await TransactionController.editTransaction(transaction_id, update_dict)