"""
Script to download free food images for the menu.
Uses direct URLs from free image sources.
"""

import os
import ssl
import urllib.request

# Create Menu directory
os.makedirs("static/Menu", exist_ok=True)

# Bypass SSL verification (for development only)
ssl._create_default_https_context = ssl._create_unverified_context

# Free food images (from Unsplash - royalty free)
IMAGES = {
    "Big_Burger_Combo.png": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&h=400&fit=crop&auto=format",
    "Double_Cheeseburger.png": "https://images.unsplash.com/photo-1586190848861-99aa4a171e90?w=400&h=400&fit=crop&auto=format",
    "Cheeseburger.png": "https://images.unsplash.com/photo-1550547660-d9450f859349?w=400&h=400&fit=crop&auto=format",
    "Hamburger.png": "https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=400&h=400&fit=crop&auto=format",
    "Crispy_Chicken_Sandwich.png": "https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=400&h=400&fit=crop&auto=format",
    "Chicken_Nuggets__6_pc.png": "https://images.unsplash.com/photo-1562967914-608f82629710?w=400&h=400&fit=crop&auto=format",
    "Filet_Fish_Sandwich.png": "https://images.unsplash.com/photo-1521305916504-4a1121188589?w=400&h=400&fit=crop&auto=format",
    "Fries.png": "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=400&h=400&fit=crop&auto=format",
    "Apple_Pie.png": "https://images.unsplash.com/photo-1535920527002-b35e96722eb9?w=400&h=400&fit=crop&auto=format",
    "coca_cola.png": "https://images.unsplash.com/photo-1554866585-cd94860890b7?w=400&h=400&fit=crop&auto=format",
}

def download_image(url, filename):
    """Download an image from URL."""
    filepath = f"static/Menu/{filename}"
    try:
        request = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            with open(filepath, 'wb') as f:
                f.write(response.read())
        print(f"Downloaded: {filename}")
        return True
    except Exception as e:
        print(f"Failed to download {filename}: {e}")
        return False

def main():
    print("Downloading food images from Unsplash...")
    print("-" * 40)

    success = 0
    failed = 0

    for filename, url in IMAGES.items():
        if download_image(url, filename):
            success += 1
        else:
            failed += 1

    print("-" * 40)
    print(f"Downloaded: {success}, Failed: {failed}")

    if failed > 0:
        print("\nNote: Some images failed to download.")
        print("You can manually add images to: backend/static/Menu/")
        print("\nRecommended free image sources:")
        print("- Unsplash: https://unsplash.com/s/photos/burger")
        print("- Pexels: https://www.pexels.com/search/burger/")
        print("- Pixabay: https://pixabay.com/images/search/burger/")

if __name__ == "__main__":
    main()
