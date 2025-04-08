from fastapi import HTTPException
from bson import ObjectId
from models.AdModel import AdResponse
from config.database import (
    transactions_collection,
    sub_category_collection,
    category_collection,
)
from utils.FetchImage import fetch_image_url  #Import fetch_image_url

async def get_ads(user_id: str, ad_type: str):
    user_expenses = {}
    total_income = 0
    total_expense = 0

    transactions = await transactions_collection.find({"user_id": user_id}).to_list(None)

    if not transactions:
        raise HTTPException(status_code=400, detail="No transactions found for this user")

    for transaction in transactions:
        category_id = transaction.get("category_id")
        subcategory_id = transaction.get("subcategory_id")
        amount = float(transaction.get("amount", 0))

        category_data = await category_collection.find_one({"_id": ObjectId(category_id)})
        category_type = category_data["name"] if category_data else None

        if category_type == "Income":
            total_income += amount
        elif category_type == "Expense":
            total_expense += amount

            subcategory_name = "Unknown"
            if subcategory_id:
                subcategory_data = await sub_category_collection.find_one(
                    {"_id": ObjectId(subcategory_id)}
                )
                if subcategory_data and "name" in subcategory_data:
                    subcategory_name = subcategory_data["name"]

            user_expenses[subcategory_name] = user_expenses.get(subcategory_name, 0) + amount

    if total_income == 0:
        raise HTTPException(status_code=400, detail="No income data found")

    savings_percentage = ((total_income - total_expense) / total_income) * 100
    expense_percentage = (total_expense / total_income) * 100

    ads = []

    if ad_type == "income" and savings_percentage > 60:
        investment_ad_templates = [
            "Smart ways to invest your money",
            "How to maximize your wealth?",
            "Top investment strategies in 2024",
            "The power of compound interest",
            "Build a passive income stream today!",
            "Why saving is not enough: Start investing!",
        ]
        ads = [
            AdResponse(
                title=title,
                message="Discover how to grow your savings effectively.",
                image_url=fetch_image_url(title)  # Fetch image dynamically
            )
            for title in investment_ad_templates
        ]

    elif ad_type == "expense" and expense_percentage > 60:
        sorted_expenses = sorted(user_expenses.items(), key=lambda x: x[1], reverse=True)[:6]
        for subcategory, _ in sorted_expenses:
            ads.extend(
                [
                    AdResponse(
                        title=f"How to spend less on {subcategory}?",
                        message=f"Learn effective ways to reduce expenses on {subcategory} and save more!",
                        image_url=fetch_image_url(f"reduce {subcategory} expenses")  # Fetch subcategory image
                    ),
                    AdResponse(
                        title=f"Top 5 tips to reduce {subcategory} spending",
                        message=f"Discover proven techniques to lower your {subcategory} costs without compromising quality.",
                        image_url=fetch_image_url(f"{subcategory} spending tips")
                    ),
                ]
            )

    return ads
