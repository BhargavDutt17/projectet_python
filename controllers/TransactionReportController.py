import pandas as pd
import io
import pytz
from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException
from config.database import (
    transactions_collection,
    transaction_report_collection,
    category_collection,
    sub_category_collection,
    user_collection,  # Fetch username from MongoDB
)
from utils.CloudinaryUtil import upload_file_from_object

# Set India Standard Time (IST)
india_tz = pytz.timezone("Asia/Kolkata")


def auto_adjust_column_width(writer, df, sheet_name):
    """Auto-adjusts column width for an Excel sheet."""
    worksheet = writer.sheets[sheet_name]
    for i, col in enumerate(df.columns):
        max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
        worksheet.set_column(i, i, max_length)


# Generate Transaction Report and Upload Directly to Cloudinary
async def generate_transaction_report(
    user_id: str, start_date: str = None, end_date: str = None
):
    try:
        # Fetch user from MongoDB
        user = await user_collection.find_one({"_id": ObjectId(user_id)})

        # Correctly extract username from the user document
        if user:
            if "username" in user and user["username"]:
                username = user["username"]  # Use username directly
            elif "firstName" in user and "lastName" in user:
                username = f"{user['firstName']}_{user['lastName']}".replace(
                    " ", "_"
                )  # Use full name
            else:
                username = "UnknownUser"  # Fallback if no name found
        else:
            username = "UnknownUser"

        # Default date range (fetch all transactions if no date is provided)
        if not start_date or not end_date:
            start_date = "01/01/2000"
            end_date = datetime.now(india_tz).strftime("%d/%m/%Y")
            date_range_label = "All_Transactions"
        else:
            date_range_label = (
                f"{start_date.replace('/', '-')}_to_{end_date.replace('/', '-')}"
            )

        # Updated Filename: Now Includes Username
        file_name = f"Transaction_Report_{username}_{date_range_label}.xlsx"

        # Fetch transactions for the user
        transactions = await transactions_collection.find({"user_id": user_id}).to_list(
            None
        )
        transactions = [t for t in transactions if start_date <= t["date"] <= end_date]

        enriched_transactions = []
        total_income = 0
        total_expenses = 0

        for t in transactions:
            category = await category_collection.find_one(
                {"_id": ObjectId(t["category_id"])}
            )
            sub_category = await sub_category_collection.find_one(
                {"_id": ObjectId(t["subcategory_id"])}
            )
            amount = t["amount"]

            if category and category["name"].lower() == "income":
                total_income += amount
            elif category and category["name"].lower() == "expense":
                total_expenses += amount

            enriched_transactions.append(
                {
                    "Date": t["date"],
                    "Type": category["name"] if category else "Unknown",
                    "Category": sub_category["name"] if sub_category else "Unknown",
                    "Amount": amount,
                    "Note": t.get("description", ""),
                }
            )

        spent_percentage = (total_expenses / total_income * 100) if total_income else 0
        remaining_balance = total_income - total_expenses

        # Save Excel Report to Memory (No Local File)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            transaction_df = pd.DataFrame(enriched_transactions)
            summary_df = pd.DataFrame(
                [
                    {
                        "Username": username,  # Include Username in Summary
                        "Total Income": total_income,
                        "Total Expenses": total_expenses,
                        "Spent Percentage (%)": round(spent_percentage, 2),
                        "Remaining Balance": remaining_balance,
                    }
                ]
            )

            transaction_df.to_excel(writer, sheet_name="UserReport", index=False)
            summary_df.to_excel(writer, sheet_name="Summary", index=False)

            # Auto-adjust column widths
            auto_adjust_column_width(writer, transaction_df, "UserReport")
            auto_adjust_column_width(writer, summary_df, "Summary")

            writer.close()  # Ensure the writer is properly closed
        output.seek(0)  # Move to the beginning of the stream

        # Upload file directly to Cloudinary
        cloudinary_url = await upload_file_from_object(output, file_name, "xlsx")

        # Insert report metadata into MongoDB
        report_data = {
            "user_id": user_id,
            "username": username,  # Store username in DB
            "start_date": start_date,
            "end_date": end_date,
            "generated_at": datetime.now(india_tz).strftime("%d/%m/%Y %H:%M:%S"),
            "report_file_url": cloudinary_url,
            "report_name": file_name,
        }
        await transaction_report_collection.insert_one(report_data)

        return {
            "message": "Transaction report generated successfully",
            "report_file_url": cloudinary_url,
            "report_name": file_name,
        }

    except Exception as e:
        return {"error": f"Error generating report: {str(e)}"}


# Get Latest Transaction Report
async def get_latest_transaction_report(user_id: str):
    try:
        latest_report = await transaction_report_collection.find_one(
            {"user_id": user_id}, sort=[("generated_at", -1)]
        )
        if not latest_report:
            return {"message": "No reports found", "report_file_url": None}

        return {"report_file_url": latest_report["report_file_url"]}

    except Exception as e:
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


async def get_all_transaction_reports(user_id: str):
    try:
        reports = await transaction_report_collection.find(
            {"user_id": user_id}
        ).to_list(None)
        if not reports:
            return {"message": "No reports found", "reports": []}

        for report in reports:
            report["_id"] = str(report["_id"])  # Convert ObjectId to string

        return {"reports": reports}

    except Exception as e:
        return {"error": str(e)}
