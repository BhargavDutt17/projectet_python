from config.database import transactions_collection, category_collection
from bson import ObjectId
from models.AdModel import AdResponse
from typing import List
from datetime import datetime
from fastapi import HTTPException

async def get_ads(user_id: str) -> List[AdResponse]:
    try:
        transactions = await transactions_collection.find({"user_id": str(user_id)}).to_list(length=None)

        if not transactions:
            return []  # ✅ Return empty list if no transactions found

        income = 0
        expense = 0
        current_month = datetime.now().strftime("%m/%Y")  # ✅ Get the current month

        for transaction in transactions:
            try:
                transaction_date = datetime.strptime(transaction["date"], "%d/%m/%Y")
                transaction_month = transaction_date.strftime("%m/%Y")

                if transaction_month == current_month:
                    category = await category_collection.find_one({"_id": ObjectId(transaction["category_id"])})
                    transaction_type = category["name"] if category else None

                    if transaction_type == "Income":
                        income += float(transaction["amount"])
                    elif transaction_type == "Expense":
                        expense += float(transaction["amount"])
            except ValueError:
                continue  # Skip invalid dates

        ads = []

        if income > 0:  # ✅ Prevent division by zero
            expense_percentage = (expense / income) * 100
            savings_percentage = 100 - expense_percentage

            print(f"Income: {income}, Expense: {expense}, Expense %: {expense_percentage}, Savings %: {savings_percentage}")

            # 🔹 If expense is more than 60% -> Show expense management ads
            if expense_percentage > 60:
                ads.extend([
                    AdResponse(
                        title="Expense Management Tips",
                        message="Your expenses are over 60%! Consider using budgeting apps to track and reduce spending."
                    ),
                    AdResponse(
                        title="Save on Monthly Bills!",
                        message="Switch to cost-effective plans and subscriptions to lower your monthly expenses."
                    ),
                    AdResponse(
                        title="Cut Unnecessary Expenses",
                        message="Review your spending habits and identify non-essential expenses to save more."
                    )
                ])

            # 🔹 If expense is less than 60% -> Show investment ads
            if savings_percentage > 60:
                ads.extend([
                    AdResponse(
                        title="Invest Smartly!",
                        message="You're saving more than 60%! Explore investment opportunities in mutual funds, stocks, or real estate."
                    ),
                    AdResponse(
                        title="Grow Your Wealth",
                        message="Consider setting up a high-interest savings account or an automated investment plan."
                    ),
                    AdResponse(
                        title="Financial Freedom",
                        message="Use your savings wisely! Check out courses on financial planning and wealth management."
                    )
                ])

        return ads

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
