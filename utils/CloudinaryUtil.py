import cloudinary
from cloudinary.uploader import upload
import time  # Add this import for generating unique filenames

# Cloudinary Configuration
cloudinary.config(
    cloud_name="dvpsq8fur",
    api_key="844355169722191",
    api_secret="g9ZHUl_13Mn3-XjaWvNiMdUVZdo",
)


# Upload image (for profile pictures, products, etc.)
async def upload_image(image):
    image_bytes = await image.read()  # Await the coroutine to read the file
    result = upload(image_bytes, resource_type="image")  # Now `image_bytes` is readable
    return result["secure_url"]


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

    return result["secure_url"]
