from fastapi import APIRouter
from models.TransactionModel import Transaction
from controllers.TransactionController import addTransaction, getAllTransactions, getTransactionsByUser

router = APIRouter()

@router.post("/addTransaction", tags=["Transaction"])
async def post_transaction(transaction: Transaction):
    return await addTransaction(transaction)

@router.get("/getAllTransactions", tags=["Transaction"])
async def get_all_transactions():
    return await getAllTransactions()

@router.get("/getTransactionsByUser/{user_id}", tags=["Transaction"])
async def get_transactions_by_user(user_id: str):
    return await getTransactionsByUser(user_id)
