import pandas as pd
import io
import pytz  # Import timezone library
from datetime import datetime
from bson import ObjectId
from config.database import (
    transactions_collection,
    transaction_report_collection,
    category_collection,
    sub_category_collection,
    user_collection,
    role_collection,
)
from utils.CloudinaryUtil import upload_file

india_tz = pytz.timezone("Asia/Kolkata")  # Set India Standard Time (IST)


# Helper to parse date strings in dd/mm/yyyy format
def safe_parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%d/%m/%Y")
    except Exception as e:
        print(f"Error parsing date {date_str}: {e}")
        return None  # Return None for bad dates


# Helper to get category or sub-category name
async def get_name(collection, id):
    if not ObjectId.is_valid(id):
        return "Unknown"
    doc = await collection.find_one({"_id": ObjectId(id)})
    return doc["name"] if doc and "name" in doc else "Unknown"


# Helper to get user and role details
async def get_user_details(user_id):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})
    role_name = "Unknown"
    if user and "role_id" in user:
        role_name = await get_name(role_collection, user["role_id"])
    return {
        "user_id": str(user["_id"]),
        "first_name": user.get("firstName", ""),
        "last_name": user.get("lastName", ""),
        "username": user.get("email", ""),
        "role": role_name,
    }


# Auto-adjust column width based on content
def auto_adjust_column_width(writer, df, sheet_name):
    worksheet = writer.sheets[sheet_name]
    for col_num, col_name in enumerate(df.columns):
        max_len = max(df[col_name].astype(str).map(len).max(), len(col_name)) + 2
        worksheet.set_column(col_num, col_num, max_len)


# Main function to generate transaction report
async def generate_transaction_report(
    user_id: str, report_type: str, start_date: str, end_date: str
):
    try:
        start_date_str = start_date
        end_date_str = end_date

        # Fetch user details
        user_details = await get_user_details(user_id)

        # Fetch transactions
        all_transactions = await transactions_collection.find(
            {"user_id": user_id}
        ).to_list(None)

        # Filter transactions in date range
        transactions = [
            t
            for t in all_transactions
            if safe_parse_date(t["date"])
            and start_date_str <= t["date"] <= end_date_str
        ]

        # Prepare transactions and totals
        enriched_transactions = []
        total_income = 0
        total_expenses = 0

        for t in transactions:
            type_name = await get_name(category_collection, t["category_id"])
            sub_category_name = await get_name(
                sub_category_collection, t["subcategory_id"]
            )
            amount = t["amount"]

            if type_name.lower() == "income":
                total_income += amount
            elif type_name.lower() == "expense":
                total_expenses += amount

            enriched_transactions.append(
                {
                    "Date": t["date"],
                    "Type": type_name,
                    "Category": sub_category_name,
                    "Amount": amount,
                    "Note": t.get("description", ""),
                }
            )

        # Summary calculations
        spent_percentage = (total_expenses / total_income * 100) if total_income else 0
        remaining_balance = total_income - total_expenses

        # Prepare DataFrames
        transaction_df = (
            pd.DataFrame(enriched_transactions)
            if enriched_transactions
            else pd.DataFrame([{"Info": "No Data Available"}])
        )
        summary_df = pd.DataFrame(
            {
                "Field": [
                    "User ID",
                    "First Name",
                    "Last Name",
                    "Username",
                    "Role",
                    "Total Income",
                    "Total Expenses",
                    "Spent Percentage (%)",
                    "Remaining Balance",
                ],
                "Value": [
                    user_details["user_id"],
                    user_details["first_name"],
                    user_details["last_name"],
                    user_details["username"],
                    user_details["role"],
                    total_income,
                    total_expenses,
                    round(spent_percentage, 2),
                    remaining_balance,
                ],
            }
        )

        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            transaction_df.to_excel(writer, sheet_name="UserReport", index=False)
            summary_df.to_excel(writer, sheet_name="Summary", index=False)

            # Auto-adjust column widths
            auto_adjust_column_width(writer, transaction_df, "UserReport")
            auto_adjust_column_width(writer, summary_df, "Summary")

        output.seek(0)  # Move cursor to start

        # Upload to Cloudinary
        cloudinary_url = await upload_file(output)  # Pass in-memory file

        # Save report reference in DB
        report_entry = {
            "report_type": report_type,
            "start_date": start_date_str,
            "end_date": end_date_str,
            "generated_at": datetime.now(india_tz).strftime(
                "%d/%m/%Y %H:%M:%S"
            ),  # Use IST time
            "report_file_url": cloudinary_url,
        }
        await transaction_report_collection.insert_one(report_entry)

        return {
            "message": "Transaction report generated successfully",
            "report_file_url": cloudinary_url,
        }

    except Exception as e:
        print(f"Error generating report: {e}")
        return {"error": str(e)}


# Function to get the report download link
async def get_transaction_report(report_id: str):
    try:
        report = await transaction_report_collection.find_one(
            {"_id": ObjectId(report_id)}
        )
        if not report:
            raise Exception("Report not found")

        return {"report_file_url": report["report_file_url"]}
    except Exception as e:
        return {"error": str(e)}
