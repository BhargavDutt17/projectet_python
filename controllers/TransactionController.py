from models.TransactionModel import Transaction, TransactionOut
from models.CategoryModel import CategoryOut
from bson import ObjectId
from config.database import user_collection, transactions_collection, category_collection,role_collection ,sub_category_collection
from fastapi import HTTPException
from fastapi.responses import JSONResponse


async def addTransaction(transaction: Transaction):
    saved_transaction = await transactions_collection.insert_one(transaction.dict())
    return JSONResponse(content={"message": "Transaction saved successfully!!"}, status_code=201)


async def getAllTransactions():
    Transactions = await transactions_collection.find().to_list()
    print(Transactions)

    for transaction in Transactions:

        if "user_id" in transaction and isinstance(transaction["user_id"], ObjectId):
            transaction["user_id"] = str(transaction["user_id"])

        user = await user_collection.find_one({"_id": ObjectId(transaction["user_id"])})
        if user:
            user["_id"] = str(user["_id"])
            transaction["user_id"] = user

        if "role_id" in transaction and isinstance(transaction["role_id"], ObjectId):
            transaction["role_id"] = str(transaction["role_id"])

        role = await role_collection.find_one({"_id": ObjectId(transaction["role_id"])})
        if role:
            role["_id"] = str(role["_id"])
            transaction["role_id"] = role

        if "category_id" in transaction and isinstance(transaction["category_id"], ObjectId):
            transaction["category_id"] = str(transaction["category_id"])

        category = await category_collection.find_one({"_id": ObjectId(transaction["category_id"])})
        if category:
            category["_id"] = str(category["_id"])
            transaction["category_id"] = category


        if "subcategory_id" in transaction and isinstance(transaction["subcategory_id"], ObjectId):
            transaction["subcategory_id"] = str(transaction["subcategory_id"])

        subcategory = await sub_category_collection.find_one({"_id": ObjectId(transaction["subcategory_id"])})
        if subcategory:
            subcategory["_id"] = str(subcategory["_id"])
            transaction["subcategory_id"] = subcategory
            

    return [TransactionOut(**transaction) for transaction in Transactions]


async def getTransactionByUserId(user_id:str):
    Transactions = await transactions_collection.find({"user_id":user_id}).to_list()
    print(Transactions)

    for transaction in Transactions:

        if "user_id" in transaction and isinstance(transaction["user_id"], ObjectId):
            transaction["user_id"] = str(transaction["user_id"])

        user = await user_collection.find_one({"_id": ObjectId(transaction["user_id"])})
        if user:
            user["_id"] = str(user["_id"])
            transaction["user_id"] = user

        if "role_id" in transaction and isinstance(transaction["role_id"], ObjectId):
            transaction["role_id"] = str(transaction["role_id"])

        role = await role_collection.find_one({"_id": ObjectId(transaction["role_id"])})
        if role:
            role["_id"] = str(role["_id"])
            transaction["role_id"] = role

        if "category_id" in transaction and isinstance(transaction["category_id"], ObjectId):
            transaction["category_id"] = str(transaction["category_id"])

        category = await category_collection.find_one({"_id": ObjectId(transaction["category_id"])})
        if category:
            category["_id"] = str(category["_id"])
            transaction["category_id"] = category


        if "subcategory_id" in transaction and isinstance(transaction["subcategory_id"], ObjectId):
            transaction["subcategory_id"] = str(transaction["subcategory_id"])

        subcategory = await sub_category_collection.find_one({"_id": ObjectId(transaction["subcategory_id"])})
        if subcategory:
            subcategory["_id"] = str(subcategory["_id"])
            transaction["subcategory_id"] = subcategory

    return [TransactionOut(**transaction) for transaction in Transactions]