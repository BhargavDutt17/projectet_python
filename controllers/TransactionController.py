from models.TransactionModel import Transaction, TransactionOut
from bson import ObjectId
from config.database import transaction_collection, category_collection, sub_category_collection
from fastapi.responses import JSONResponse
from fastapi import HTTPException

async def addTransaction(transaction: Transaction):
    transaction_dict = transaction.dict()

    # Fetch category details using category_id
    category = await category_collection.find_one({"_id": ObjectId(transaction.category_id)})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Fetch subcategory details using subcategory_id
    subcategory = await sub_category_collection.find_one({"_id": ObjectId(transaction.subcategory_id)})
    if not subcategory:
        raise HTTPException(status_code=404, detail="Subcategory not found")

    # Store category & subcategory details
    transaction_dict["category"] = category
    transaction_dict["subcategory"] = subcategory

    savedTransaction = await transaction_collection.insert_one(transaction_dict)
    return JSONResponse(content={"message": "Transaction saved successfully!"}, status_code=201)

async def getAllTransactions():
    transactions = await transaction_collection.find().to_list(None)

    for txn in transactions:
        if "category_id" in txn and isinstance(txn["category_id"], ObjectId):
            txn["category_id"] = str(txn["category_id"])

        if "subcategory_id" in txn and isinstance(txn["subcategory_id"], ObjectId):
            txn["subcategory_id"] = str(txn["subcategory_id"])

    return [TransactionOut(**txn) for txn in transactions]

async def getTransactionsByUser(user_id: str):
    transactions = await transaction_collection.find({"created_by.user_id": user_id}).to_list(None)

    for txn in transactions:
        if "category_id" in txn and isinstance(txn["category_id"], ObjectId):
            txn["category_id"] = str(txn["category_id"])

        if "subcategory_id" in txn and isinstance(txn["subcategory_id"], ObjectId):
            txn["subcategory_id"] = str(txn["subcategory_id"])

    return [TransactionOut(**txn) for txn in transactions]
