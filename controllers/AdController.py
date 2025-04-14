from fastapi import HTTPException
from bson import ObjectId
from datetime import datetime
from models.AdModel import AdResponse
from config.database import (
    transactions_collection,
    sub_category_collection,
    category_collection,
)
from utils.FetchImage import fetch_image_url  # Import fetch_image_url

async def get_ads(user_id: str, ad_type: str):
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required.")
    
    if ad_type not in ['income', 'expense']:
        raise HTTPException(status_code=400, detail="Invalid ad type.")
    
    # Your existing logic to fetch user data

    user_expenses = {}
    total_income = 0
    total_expense = 0

    now = datetime.now()
    current_month = now.month
    current_year = now.year

    transactions = await transactions_collection.find({"user_id": user_id}).to_list(None)

    if not transactions:
        raise HTTPException(status_code=400, detail="No transactions found for this user")

    for transaction in transactions:
        txn_date = datetime.strptime(transaction['date'], "%d/%m/%Y")
        if txn_date.month != current_month or txn_date.year != current_year:
            continue

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
                subcategory_data = await sub_category_collection.find_one({"_id": ObjectId(subcategory_id)})
                if subcategory_data and "name" in subcategory_data:
                    subcategory_name = subcategory_data["name"]

            user_expenses[subcategory_name] = user_expenses.get(subcategory_name, 0) + amount

    if total_income == 0:
        raise HTTPException(status_code=400, detail="No income data found")

    savings_percentage = ((total_income - total_expense) / total_income) * 100
    expense_percentage = (total_expense / total_income) * 100

    ads = []

    if ad_type == "income" and savings_percentage > 40:
        # Dynamically generate investment ad titles based on income levels or strategies
        investment_ad_templates = await fetch_investment_strategies(total_income, savings_percentage)

        ads = [
            AdResponse(
                title=title,
                message="Discover how to grow your savings effectively.",
                image_url=fetch_image_url(title)  # Fetch image dynamically
            )
            for title in investment_ad_templates
        ]

    if ad_type == "expense" and expense_percentage > 60:
        # Dynamically sort expenses and generate related ads
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
                    # Add more dynamic expense-related ads as required
                ]
            )

    return ads
async def fetch_investment_strategies(total_income, savings_percentage):
    """
    Fetches dynamic investment ad templates based on income and savings percentage.
    This could be extended to pull from a database or generate content dynamically.
    """
    strategies = []

    # Dynamically generate investment strategies based on income or savings percentage
    if savings_percentage > 30:
        strategies = [
            "Maximize returns on your savings",
            "How to build a portfolio with low risk",
            "The best investment opportunities for steady growth",
            "Explore sustainable investments",
            "How to diversify your investments",
            "Let your savings work smarter, not harder",
        ]
    elif total_income > 50000:
        strategies = [
            "Smart ways to invest your money",
            "How to maximize your wealth?",
            "Top investment strategies for high earners",
            "The power of compound interest",
            "Build a passive income stream today!",
            "Why saving is not enough: Start investing!",
        ]
    else:
        strategies = [
            "Beginner’s guide to investments",
            "Top investment strategies for first-time investors",
            "How to start investing with limited funds",
            "Investing 101: A simple guide to financial growth",
        ]
    
    return strategies