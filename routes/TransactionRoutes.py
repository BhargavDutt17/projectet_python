from fastapi import APIRouter,Body,Query
from models.TransactionModel import Transaction,TransactionUpdate
from pydantic import BaseModel
from controllers import TransactionController
from typing import Optional,List


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
    user_id: str,
    start_date: str = "",
    end_date: str = "",
    category_id: str = "",
    subcategory_id: str = ""
):
    return await TransactionController.generateTransactionReport(
        user_id, start_date, end_date, category_id, subcategory_id
    )

@router.get("/admin/generateTransactionReport")
async def admin_generate_transaction_report(
    user_id: str,
    start_date: str = "",
    end_date: str = "",
    category_id: str = "",
    subcategory_id: str = ""
):
    return await TransactionController.generateTransactionReportForAdmin(
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

@router.delete("/all-transaction-reports/{user_id}")
async def delete_all_transaction_reports(user_id: str):
    return await TransactionController.delete_all_transaction_reports(user_id)

@router.delete("/deleteTransaction/{transaction_id}")
async def delete_transaction(transaction_id: str, user_id: Optional[str] = None):
    return await TransactionController.deleteTransaction(transaction_id, user_id)

# Pydantic model for selected delete
class DeleteTransactionIds(BaseModel):
    transaction_ids: List[str]

# Delete selected transactions (POST) with optional user_id
@router.post("/transactions/delete-selected")
async def delete_selected_transactions_post(
    payload: DeleteTransactionIds,
    user_id: str = Query(None)  # <-- This is the only change
):
    return await TransactionController.delete_selected_transactions(payload.transaction_ids, user_id)

# Delete all transactions for a user (DELETE)
@router.delete("/all-transactions/{user_id}")
async def delete_all_transactions_route(user_id: str):
    return await TransactionController.delete_all_transactions(user_id)

@router.put("/editTransaction/{transaction_id}")
async def edit_transaction(
    transaction_id: str, 
    updated_data: TransactionUpdate = Body(...)
):
    # Convert Pydantic model to dictionary and remove unset values (None)
    update_dict = updated_data.dict(exclude_unset=True)
    return await TransactionController.editTransaction(transaction_id, update_dict)

@router.get("/admin/getTransactionsByUserSearch")
async def get_transactions_by_user_search(q: str):
    return await TransactionController.getTransactionsByUserSearch(q)

class DeleteReportIds(BaseModel):
    report_id: List[str]
@router.post("/transaction-reports/delete-selected")
async def delete_selected_transaction_reports_post(
    payload: DeleteReportIds
):
    return await TransactionController.deleteSelectedTransactionReports(payload.report_id)





