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
    get_latest_transaction_report,
    get_all_transaction_reports,
    delete_transaction_report
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
async def getTransactionByUserId(user_id: str, month: int = None, year: int = None):
    try:
        transactions = await transactions_collection.find({"user_id": str(user_id)}).to_list(None)

        filtered_transactions = []
        for transaction in transactions:
            # Convert `_id` to string, keep others as strings
            transaction["_id"] = str(transaction["_id"])
            transaction["user_id"] = str(transaction["user_id"])
            transaction["category_id"] = str(transaction["category_id"])
            transaction["subcategory_id"] = str(transaction["subcategory_id"])

            # Convert stored "DD/MM/YYYY" format back to "YYYY-MM-DD"
            if "date" in transaction and isinstance(transaction["date"], str):
                try:
                    # Convert string date "DD/MM/YYYY" to datetime object
                    transaction_date = datetime.strptime(transaction["date"], "%d/%m/%Y")
                    transaction["date"] = transaction_date.strftime("%Y-%m-%d")

                    # Apply month and year filter if provided
                    if (month is None or transaction_date.month == month) and (year is None or transaction_date.year == year):
                        filtered_transactions.append(transaction)
                except ValueError:
                    pass  # Keep original format if conversion fails

            # Fetch and Convert References
            category = await category_collection.find_one({"_id": ObjectId(transaction["category_id"])})
            transaction["category_id"] = convert_objectid_to_str(category) if category else None

            subcategory = await sub_category_collection.find_one({"_id": ObjectId(transaction["subcategory_id"])})
            transaction["subcategory_id"] = convert_objectid_to_str(subcategory) if subcategory else None

            user = await user_collection.find_one({"_id": ObjectId(transaction["user_id"])})
            transaction["user_id"] = convert_objectid_to_str(user) if user else None

        return [TransactionOut(**transaction) for transaction in filtered_transactions]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching transactions for user: {str(e)}")


async def editTransaction(transaction_id: str, updated_data: dict):
    try:
        # Fetch the existing transaction from the database
        existing_transaction = await transactions_collection.find_one({"_id": ObjectId(transaction_id)})

        if not existing_transaction:
            raise HTTPException(status_code=404, detail="Transaction not found.")

        # Only update fields that are present in updated_data and not empty
        update_fields = {
            key: updated_data[key]
            for key in updated_data 
            if updated_data[key] is not None and updated_data[key] != "string"
        }

        # Ensure we don't update with empty data
        if not update_fields:
            return {"message": "No valid fields provided for update."}

        # Ensure date formatting if updated
        if "date" in update_fields:
            try:
                update_fields["date"] = datetime.strptime(update_fields["date"], "%Y-%m-%d").strftime("%d/%m/%Y")
            except ValueError:
                pass  # Keep existing format if conversion fails

        # Perform update operation
        result = await transactions_collection.update_one(
            {"_id": ObjectId(transaction_id)},
            {"$set": update_fields}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Transaction not found.")

        return {"message": "Transaction updated successfully!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating transaction: {str(e)}")
    
    
    # Delete Transaction (Optional user_id)
async def deleteTransaction(transaction_id: str, user_id: str = None):
    try:
        query = {"_id": ObjectId(transaction_id)}
        if user_id:
            query["user_id"] = user_id

        result = await transactions_collection.delete_one(query)

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Transaction not found or unauthorized access.")

        return JSONResponse(content={"message": "Transaction deleted successfully!"}, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting transaction: {str(e)}")


# Add Transaction Report Functions Inside TransactionController
async def generateTransactionReport(user_id: str, start_date: str, end_date: str):
    return await generate_transaction_report(user_id, start_date, end_date)

async def getTransactionReport(report_id: str):
    return await get_transaction_report(report_id)

async def getLatestTransactionReport(user_id: str):
    return await get_latest_transaction_report(user_id)

async def getAllTransactionReports(user_id: str):
    return await get_all_transaction_reports(user_id)

async def deleteTransactionReport(report_id: str):
    # Call a properly defined function instead of itself
    return await delete_transaction_report(report_id)
