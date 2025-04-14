import cloudinary
from cloudinary.uploader import upload,destroy
import time  # Add this import for generating unique filenames
from fastapi import HTTPException

# Cloudinary Configuration
cloudinary.config(
    cloud_name="dvpsq8fur",
    api_key="844355169722191",
    api_secret="g9ZHUl_13Mn3-XjaWvNiMdUVZdo",
)


# Upload image (for profile pictures, products, etc.)
# cloudinaryutil.py

async def upload_image(image):
    try:
        image_bytes = await image.read()  # Await the coroutine to read the file
        result = upload(image_bytes, resource_type="image")  # Upload the image to Cloudinary
        return {
            "secure_url": result["secure_url"],
            "public_id": result["public_id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

async def delete_image(public_id: str):
    try:
        result = destroy(public_id)
        return result
    except Exception as e:
        print(f"Error deleting image: {e}")
        return None



# Upload a file directly from memory (For Reports)
async def upload_file_from_object(file_stream, file_name, file_format="xlsx"):
    if file_format not in ["xlsx", "csv", "pdf", "txt"]:
        raise ValueError("Unsupported file format. Use 'xlsx', 'csv', 'pdf', or 'txt'.")

    # Generate a unique suffix based on the current timestamp
    unique_suffix = int(time.time())  # You can also use UUID for even more uniqueness

    result = upload(
        file_stream,
        resource_type="raw",  # Ensure it's uploaded as a file (not an image)
        public_id=f"transaction_reports/{file_name}_{unique_suffix}",  # Append the unique suffix to the filename
        format=file_format,
        overwrite=False,  # Do not overwrite if the file already exists
    )

    # Store the exact public_id as it is used for deletion
    return {
        "secure_url": result["secure_url"],
        "public_id": result["public_id"]
    }

async def delete_file(public_id: str, resource_type: str = "raw"):
    try:
        # If using sync Cloudinary SDK in async context, wrap it with asyncio.to_thread
        import asyncio
        result = await asyncio.to_thread(destroy, public_id, resource_type=resource_type)
        return result
    except Exception as e:
        print(f"Cloudinary delete error: {e}")
        return {"result": "error", "message": str(e)}
