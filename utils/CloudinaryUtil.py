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

# Upload a file directly from memory (For Reports)
async def upload_file_from_object(file_stream, file_name, file_format="xlsx"):
    if file_format not in ["xlsx", "csv", "pdf", "txt"]:
        raise ValueError("Unsupported file format. Use 'xlsx', 'csv', 'pdf', or 'txt'.")

    result = upload(
        file_stream,
        resource_type="raw",  # Ensure it's uploaded as a file (not an image)
        public_id=f"transaction_reports/{file_name}",  # Store in Cloudinary folder
        format=file_format,
        overwrite=True  # Overwrite if the file already exists
    )

    return result["secure_url"]
