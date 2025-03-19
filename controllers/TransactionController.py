from models.TransactionModel import Transaction, TransactionOut
from bson import ObjectId
from config.database import (
    user_collection,
    transactions_collection,
    category_collection,
    sub_category_collection,
)
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from controllers.TransactionReportController import (
    generate_transaction_report,
    get_transaction_report,
)
from datetime import datetime


# Function to convert ObjectId fields safely
def convert_objectid_to_str(data):
    """Recursively converts ObjectId fields to strings."""
    if isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, dict):
        return {k: convert_objectid_to_str(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_objectid_to_str(i) for i in data]
    return data


# Add Transaction (Only `_id` as ObjectId, Other IDs as String)
async def addTransaction(transaction: Transaction):
    try:
        transaction_dict = transaction.dict()

        # Store _id as ObjectId (Only for Transaction ID)
        transaction_dict["_id"] = ObjectId()

        # Keep user_id, category_id, and subcategory_id as strings
        transaction_dict["user_id"] = str(transaction_dict["user_id"])
        transaction_dict["category_id"] = str(transaction_dict["category_id"])
        transaction_dict["subcategory_id"] = str(transaction_dict["subcategory_id"])

        # Convert date format to "DD/MM/YYYY" before storing
        try:
            transaction_dict["date"] = datetime.strptime(transaction_dict["date"], "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            pass  # If already in correct format, keep as is

        await transactions_collection.insert_one(transaction_dict)
        return JSONResponse(content={"message": "Transaction saved successfully!!"}, status_code=201)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding transaction: {str(e)}")


# Get All Transactions (Follow ProductController Structure)
async def getAllTransactions():
    try:
        transactions = await transactions_collection.find().to_list(None)

        for transaction in transactions:
            # Convert `_id` to string, keep others as strings
            transaction["_id"] = str(transaction["_id"])
            transaction["user_id"] = str(transaction["user_id"])
            transaction["category_id"] = str(transaction["category_id"])
            transaction["subcategory_id"] = str(transaction["subcategory_id"])

            # Convert stored "DD/MM/YYYY" format back to "YYYY-MM-DD"
            if "date" in transaction and isinstance(transaction["date"], str):
                try:
                    transaction["date"] = datetime.strptime(transaction["date"], "%d/%m/%Y").strftime("%Y-%m-%d")
                except ValueError:
                    pass  # Keep original format if conversion fails

            # Fetch and Convert References
            category = await category_collection.find_one({"_id": ObjectId(transaction["category_id"])})
            transaction["category_id"] = convert_objectid_to_str(category) if category else None

            subcategory = await sub_category_collection.find_one({"_id": ObjectId(transaction["subcategory_id"])})
            transaction["subcategory_id"] = convert_objectid_to_str(subcategory) if subcategory else None

            user = await user_collection.find_one({"_id": ObjectId(transaction["user_id"])})
            transaction["user_id"] = convert_objectid_to_str(user) if user else None

        return [TransactionOut(**transaction) for transaction in transactions]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching transactions: {str(e)}")


# Get Transactions by User ID (Follow ProductController Structure)
async def getTransactionByUserId(user_id: str):
    try:
        transactions = await transactions_collection.find({"user_id": str(user_id)}).to_list(None)

        for transaction in transactions:
            # Convert `_id` to string, keep others as strings
            transaction["_id"] = str(transaction["_id"])
            transaction["user_id"] = str(transaction["user_id"])
            transaction["category_id"] = str(transaction["category_id"])
            transaction["subcategory_id"] = str(transaction["subcategory_id"])

            # Convert stored "DD/MM/YYYY" format back to "YYYY-MM-DD"
            if "date" in transaction and isinstance(transaction["date"], str):
                try:
                    transaction["date"] = datetime.strptime(transaction["date"], "%d/%m/%Y").strftime("%Y-%m-%d")
                except ValueError:
                    pass  # Keep original format if conversion fails

            # Fetch and Convert References
            category = await category_collection.find_one({"_id": ObjectId(transaction["category_id"])})
            transaction["category_id"] = convert_objectid_to_str(category) if category else None

            subcategory = await sub_category_collection.find_one({"_id": ObjectId(transaction["subcategory_id"])})
            transaction["subcategory_id"] = convert_objectid_to_str(subcategory) if subcategory else None

            user = await user_collection.find_one({"_id": ObjectId(transaction["user_id"])})
            transaction["user_id"] = convert_objectid_to_str(user) if user else None

        return [TransactionOut(**transaction) for transaction in transactions]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching transactions for user: {str(e)}")


# Add Transaction Report Functions Inside TransactionController
async def generateTransactionReport(user_id: str, report_type: str, start_date: str, end_date: str):
    return await generate_transaction_report(user_id, report_type, start_date, end_date)


async def getTransactionReport(report_id: str):
    return await get_transaction_report(report_id)
