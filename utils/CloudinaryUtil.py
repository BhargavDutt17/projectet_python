import cloudinary
from cloudinary.uploader import upload

# Cloudinary Configuration
cloudinary.config(
    cloud_name="dvpsq8fur",
    api_key="844355169722191",
    api_secret="g9ZHUl_13Mn3-XjaWvNiMdUVZdo"
)

# Upload image (for profile pictures, products, etc.)
async def upload_image(image):
    result = upload(image, resource_type="image")  # Ensure it's an image
    print("Cloudinary response (Image):", result)
    return result["secure_url"]  # Return URL as string

# Upload file (Excel, CSV, PDF, etc.)
async def upload_file(file, file_format="xlsx"):
    if file_format not in ["xlsx", "csv", "pdf", "txt"]:
        raise ValueError("Unsupported file format. Use 'xlsx', 'csv', 'pdf', or 'txt'.")

    result = upload(file, resource_type="raw", format=file_format)  # Ensures correct format
    print("Cloudinary response (File):", result)
    return result["secure_url"]  # Return URL as string
