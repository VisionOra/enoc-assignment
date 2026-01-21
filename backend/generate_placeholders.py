"""
Script to generate placeholder images for menu items.
Run this once to create placeholder images, then replace with actual images.

Requirements: pip install Pillow
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create Menu directory if it doesn't exist
os.makedirs("static/Menu", exist_ok=True)

# Menu items with colors
items = {
    "Big_Burger_Combo": {"color": "#FF6B35", "emoji": "🍔🍟🥤"},
    "Double_Cheeseburger": {"color": "#F7931E", "emoji": "🍔🍔"},
    "Cheeseburger": {"color": "#FFB347", "emoji": "🍔"},
    "Hamburger": {"color": "#8B4513", "emoji": "🍔"},
    "Crispy_Chicken_Sandwich": {"color": "#DEB887", "emoji": "🍗"},
    "Chicken_Nuggets__6_pc": {"color": "#DAA520", "emoji": "🍗"},
    "Filet_Fish_Sandwich": {"color": "#4682B4", "emoji": "🐟"},
    "Fries": {"color": "#FFD700", "emoji": "🍟"},
    "Apple_Pie": {"color": "#CD853F", "emoji": "🥧"},
    "coca_cola": {"color": "#DC143C", "emoji": "🥤"},
}


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def create_placeholder(name, color, emoji, size=(300, 300)):
    # Create image with gradient background
    img = Image.new('RGBA', size, (42, 42, 74, 255))
    draw = ImageDraw.Draw(img)

    # Draw colored circle
    center = size[0] // 2
    radius = 80
    rgb = hex_to_rgb(color)

    # Draw circle
    draw.ellipse(
        [center - radius, center - radius - 30, center + radius, center + radius - 30],
        fill=rgb
    )

    # Draw item name
    display_name = name.replace("_", " ").replace("  ", " (")
    if "6 pc" in display_name:
        display_name = display_name.replace("6 pc", "6 pc)")

    # Try to use a font, fall back to default
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except:
        font = ImageFont.load_default()

    # Get text bbox for centering
    bbox = draw.textbbox((0, 0), display_name, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (size[0] - text_width) // 2

    draw.text((text_x, size[1] - 50), display_name, fill=(255, 255, 255), font=font)

    return img


def main():
    print("Generating placeholder images...")

    for name, props in items.items():
        img = create_placeholder(name, props["color"], props["emoji"])
        filepath = f"static/Menu/{name}.png"
        img.save(filepath, "PNG")
        print(f"Created: {filepath}")

    print("\nDone! Replace these placeholders with actual food images.")
    print("Image files should be placed in: backend/static/Menu/")


if __name__ == "__main__":
    main()
