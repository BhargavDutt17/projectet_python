import pandas as pd
import io
import pytz
from datetime import datetime
from pymongo import ASCENDING
from bson import ObjectId, errors
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from config.database import (
    transactions_collection,
    transaction_report_collection,
    category_collection,
    sub_category_collection,
    user_collection,
)
from utils.CloudinaryUtil import upload_file_from_object

india_tz = pytz.timezone("Asia/Kolkata")


def auto_adjust_column_width(writer, df, sheet_name):
    worksheet = writer.sheets[sheet_name]
    for i, col in enumerate(df.columns):
        max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
        worksheet.set_column(i, i, max_length)


# ✅ Admin version: Generate report and return as downloadable Excel file
async def generate_transaction_report_for_admin(
    user_id: str,
    start_date: str = None,
    end_date: str = None,
    category_id: str = None,
    subcategory_id: str = None
):
    try:
        user = await user_collection.find_one({"_id": ObjectId(user_id)})
        username = user.get("username", "UnknownUser") if user else "UnknownUser"

        date_format = "%d/%m/%Y"
        if start_date and end_date:
            start_date_obj = datetime.strptime(start_date, date_format)
            end_date_obj = datetime.strptime(end_date, date_format)
            date_range_label = f"{start_date.replace('/', '-')}_to_{end_date.replace('/', '-')}"
        else:
            start_date_obj = datetime.strptime("01/01/2000", date_format)
            end_date_obj = datetime.now()
            date_range_label = "All_Transactions"

        transactions = await transactions_collection.find({"user_id": user_id}).sort("date", ASCENDING).to_list(None)

        filtered_transactions = []
        total_income = 0
        total_expenses = 0
        sr_no = 1

        for t in transactions:
            try:
                transaction_date_obj = datetime.strptime(t["date"], date_format)

                if not (start_date_obj <= transaction_date_obj <= end_date_obj):
                    continue

                category = await category_collection.find_one({"_id": ObjectId(t["category_id"])})
                sub_category = await sub_category_collection.find_one({"_id": ObjectId(t["subcategory_id"])})

                if category_id and str(category["_id"]) != category_id:
                    continue
                if subcategory_id and str(sub_category["_id"]) != subcategory_id:
                    continue

                amount = t["amount"]
                if category and category["name"].lower() == "income":
                    total_income += amount
                elif category and category["name"].lower() == "expense":
                    total_expenses += amount

                filtered_transactions.append({
                    "Sr. No.": sr_no,
                    "Date": t["date"],
                    "Type": category["name"] if category else "Unknown",
                    "Category": sub_category["name"] if sub_category else "Unknown",
                    "Amount": amount,
                    "Note": t.get("description", "")
                })
                sr_no += 1
            except Exception:
                continue

        spent_percentage = (total_expenses / total_income * 100) if total_income else 0
        remaining_balance = total_income - total_expenses

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            transaction_df = pd.DataFrame(filtered_transactions)
            summary_df = pd.DataFrame([{
                "Username": username,
                "Total Income": total_income,
                "Total Expenses": total_expenses,
                "Spent Percentage (%)": round(spent_percentage, 2),
                "Remaining Balance": remaining_balance,
            }])
            transaction_df.to_excel(writer, sheet_name="UserReport", index=False)
            summary_df.to_excel(writer, sheet_name="Summary", index=False)
            auto_adjust_column_width(writer, transaction_df, "UserReport")
            auto_adjust_column_width(writer, summary_df, "Summary")
            writer.close()

        output.seek(0)
        file_name = f"{username}_Report_{date_range_label}.xlsx"
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={file_name}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating admin report: {str(e)}")


# ✅ Existing: User report generation with Cloudinary upload
async def generate_transaction_report(
    user_id: str,
    start_date: str = None,
    end_date: str = None,
    category_id: str = None,
    subcategory_id: str = None
):
    try:
        user = await user_collection.find_one({"_id": ObjectId(user_id)})
        full_username = "UnknownUser"
        if user:
            first_name = user.get("firstName", "Unknown")
            last_name = user.get("lastName", "Unknown")
            username = user.get("username", "UnknownUser")
            full_username = f"{first_name}_{last_name} ({username})".replace(" ", "_")

        date_format = "%d/%m/%Y"
        if start_date and end_date:
            start_date_obj = datetime.strptime(start_date, date_format)
            end_date_obj = datetime.strptime(end_date, date_format)
            date_range_label = f"{start_date.replace('/', '-')}_to_{end_date.replace('/', '-')}"
        else:
            start_date_obj = datetime.strptime("01/01/2000", date_format)
            end_date_obj = datetime.now()
            date_range_label = "All_Transactions"

        filter_label = ""
        if category_id:
            category = await category_collection.find_one({"_id": ObjectId(category_id)})
            filter_label += f"Category_{category['name']}_"
        if subcategory_id:
            subcategory = await sub_category_collection.find_one({"_id": ObjectId(subcategory_id)})
            filter_label += f"SubCategory_{subcategory['name']}_"    

        file_name = f"Transaction_Report_{full_username}_{date_range_label}_{filter_label}xlsx"

        transactions = await transactions_collection.find({"user_id": user_id}).sort("date", ASCENDING).to_list(None)

        filtered_transactions = []
        total_income = 0
        total_expenses = 0
        sr_no = 1

        for t in transactions:
            try:
                transaction_date_obj = datetime.strptime(t["date"], date_format)

                if not (start_date_obj <= transaction_date_obj <= end_date_obj):
                    continue

                category = await category_collection.find_one({"_id": ObjectId(t["category_id"])})
                sub_category = await sub_category_collection.find_one({"_id": ObjectId(t["subcategory_id"])})

                if category_id and str(category["_id"]) != category_id:
                    continue
                if subcategory_id and str(sub_category["_id"]) != subcategory_id:
                    continue

                amount = t["amount"]
                if category and category["name"].lower() == "income":
                    total_income += amount
                elif category and category["name"].lower() == "expense":
                    total_expenses += amount

                filtered_transactions.append({
                    "Sr. No.": sr_no,
                    "Date": t["date"],
                    "Type": category["name"] if category else "Unknown",
                    "Category": sub_category["name"] if sub_category else "Unknown",
                    "Amount": amount,
                    "Note": t.get("description", "")
                })
                sr_no += 1
            except Exception:
                continue

        spent_percentage = (total_expenses / total_income * 100) if total_income else 0
        remaining_balance = total_income - total_expenses

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            transaction_df = pd.DataFrame(filtered_transactions)
            summary_df = pd.DataFrame([{
                "Username": username,
                "Total Income": total_income,
                "Total Expenses": total_expenses,
                "Spent Percentage (%)": round(spent_percentage, 2),
                "Remaining Balance": remaining_balance,
            }])
            transaction_df.to_excel(writer, sheet_name="UserReport", index=False)
            summary_df.to_excel(writer, sheet_name="Summary", index=False)
            auto_adjust_column_width(writer, transaction_df, "UserReport")
            auto_adjust_column_width(writer, summary_df, "Summary")
            writer.close()

        output.seek(0)
        cloudinary_url = await upload_file_from_object(output, file_name, "xlsx")

        await transaction_report_collection.insert_one({
            "user_id": user_id,
            "username": username,
            "start_date": start_date,
            "end_date": end_date,
            "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "report_file_url": cloudinary_url,
            "report_name": file_name,
        })

        return {
            "message": "Transaction report generated successfully",
            "report_file_url": cloudinary_url,
            "report_name": file_name,
        }

    except Exception as e:
        return {"error": f"Error generating report: {str(e)}"}


# ✅ Other helper functions remain unchanged
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


async def get_transaction_report(report_id: str):
    try:
        report = await transaction_report_collection.find_one({"_id": ObjectId(report_id)})
        if not report:
            raise Exception("Report not found")
        return {"report_file_url": report["report_file_url"]}
    except Exception as e:
        return {"error": str(e)}


async def get_all_transaction_reports(user_id: str):
    try:
        reports = await transaction_report_collection.find({"user_id": user_id}).to_list(None)
        for report in reports:
            report["_id"] = str(report["_id"])
        return {"reports": reports}
    except Exception as e:
        return {"error": str(e)}


async def delete_transaction_report(report_id: str):
    try:
        report_object_id = ObjectId(report_id)
        report = await transaction_report_collection.find_one({"_id": report_object_id})
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        await transaction_report_collection.delete_one({"_id": report_object_id})
        return {"message": "Transaction report deleted successfully"}
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid report ID format")
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")
