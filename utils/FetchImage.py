import os
import requests

SERP_API_KEY = ""  # 🔹 Replace with your actual SerpAPI key

def fetch_image_url(query):
    """
    Fetches the first image URL from Google Images using SerpAPI.
    """
    try:
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "tbm": "isch",  # Image search
            "api_key": SERP_API_KEY
        }
        response = requests.get(url, params=params)
        data = response.json()

        # Extract the first image result
        images_results = data.get("images_results", [])
        if images_results:
            return images_results[0]["original"]
        else:
            return None  # No images found
    except Exception as e:
        print(f"Error fetching image for '{query}': {e}")
        return None  # Return None if API fails
