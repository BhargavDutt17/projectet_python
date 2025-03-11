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
async def get_transaction_by_user_id(user_id:str):
    return await TransactionController.getTransactionByUserId(user_id)
