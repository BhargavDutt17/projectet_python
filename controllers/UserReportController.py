from config.database import user_collection, user_report_collection, role_collection
import pandas as pd
import io, pytz
from datetime import datetime
from fastapi import HTTPException
from bson import ObjectId, errors
from utils.CloudinaryUtil import upload_file_from_object,delete_file
from fastapi import Request
import re
from typing import Optional,List
 

india_tz = pytz.timezone("Asia/Kolkata")


def auto_adjust_column_width(writer, df, sheet_name):
    worksheet = writer.sheets[sheet_name]
    for i, col in enumerate(df.columns):
        max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
        worksheet.set_column(i, i, max_length)


async def generate_user_report(request: Request):
    try:
        data = await request.json()
        selected_role = data.get("selectedRole", "all")
        selected_status = data.get("selectedStatus", "all")
        search_term = data.get("searchTerm", "").lower()

        users = await user_collection.find().to_list(None)
        rows = []

        for index, user in enumerate(users, start=1):
            role_id = user.get("role_id")
            role_name = "N/A"

            if role_id:
                role = await role_collection.find_one({"_id": ObjectId(role_id)})
                if role:
                    role_name = role.get("name", "N/A")

            # ✅ Apply filters
            if selected_role != "all" and role_name != selected_role:
                continue
            if selected_status != "all" and user.get("status") != selected_status:
                continue
            if search_term:
                full_text = " ".join([user.get("firstName", ""),
                                      user.get("lastName", ""),
                                      user.get("username", ""),
                                      user.get("email", "")]).lower()
                if search_term not in full_text:
                    continue

            rows.append({
                "Sr. No.": len(rows) + 1,
                "First Name": user.get("firstName", ""),
                "Last Name": user.get("lastName", ""),
                "Username": user.get("username", ""),
                "Email": user.get("email", ""),
                "Role": role_name,
                "Status": user.get("status", "")
            })

        df = pd.DataFrame(rows)
        output = io.BytesIO()

        file_name = "User_Report"  # Let Cloudinary handle timestamping
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="User Report", index=False)
            auto_adjust_column_width(writer, df, "User Report")

        output.seek(0)
        uploaded_info = await upload_file_from_object(output, file_name, "xlsx")
        cloudinary_url = uploaded_info["secure_url"]
        public_id = uploaded_info["public_id"]  # Ensure public_id is returned here
        final_file_name = public_id.split("/")[-1] + ".xlsx"

        report_data = {
            "username": "admin",
            "user_id": "admin",
            "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "report_file_url": cloudinary_url,
            "report_name": final_file_name,
            "public_id": public_id  # Ensure public_id is stored here in the DB
        }

        await user_report_collection.insert_one(report_data)

        return {
            "message": "User report generated successfully",
            "report_file_url": cloudinary_url,
            "report_name": final_file_name
        }

    except Exception as e:
        return {"error": f"Error generating user report: {str(e)}"}


async def get_latest_user_report():
    latest = await user_report_collection.find_one(sort=[("generated_at", -1)])
    if not latest:
        return {"message": "No reports found", "report_file_url": None}
    return {"report_file_url": latest["report_file_url"]}

async def get_all_user_reports():
    reports = await user_report_collection.find().to_list(None)
    for report in reports:
        report["_id"] = str(report["_id"])
    return {"reports": reports}

async def get_user_report_by_id(report_id: str):
    try:
        report = await user_report_collection.find_one({"_id": ObjectId(report_id)})
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return {"report_file_url": report["report_file_url"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def delete_user_report(report_id: str):
    try:
        report_obj_id = ObjectId(report_id)
        report = await user_report_collection.find_one({"_id": report_obj_id})

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        public_id = report.get("public_id")
        if public_id:
            result = await delete_file(public_id)  # or destroy(public_id) if not using async utils
            if result.get("result") != "ok":
                raise HTTPException(status_code=500, detail="Failed to delete file from Cloudinary")

        deleted = await user_report_collection.delete_one({"_id": report_obj_id})
        if deleted.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Failed to delete report from DB")

        return {"message": "User report and associated file deleted successfully"}

    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
async def delete_selected_user_reports(report_ids: List[str]):
    try:
        if not report_ids:
            raise HTTPException(status_code=400, detail="No report IDs provided")

        success_count = 0
        for report_id in report_ids:
            try:
                await delete_user_report(report_id)
                success_count += 1
            except Exception as e:
                print(f"Skipping report ID {report_id} due to error: {e}")

        return {"message": f"{success_count} report(s) deleted successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting selected reports: {str(e)}")

async def delete_all_user_reports():
    reports = await user_report_collection.find().to_list(None)

    for report in reports:
        public_id = report.get("public_id", "")
        if not public_id:
            print(f"No public_id found for report ID: {report.get('_id')}")
            continue

        print(f"Attempting to delete Cloudinary public_id: {public_id}")

        try:
            result = await delete_file(public_id, resource_type="raw")  # Await this!
            print(f"Cloudinary delete result: {result}")

            if result.get("result") != "ok":
                print(f"Failed to delete from Cloudinary: {result}")
            else:
                print(f"Successfully deleted from Cloudinary")
        except Exception as e:
            print(f"Error deleting from Cloudinary: {str(e)}")

        deleted = await user_report_collection.delete_one({"_id": report["_id"]})
        if deleted.deleted_count == 0:
            print(f"Failed to delete report from MongoDB")
        else:
            print(f"Successfully deleted report from MongoDB")

    return {"message": f"{len(reports)} report(s) deleted successfully"}
