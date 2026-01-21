"""
Simple script to create placeholder PNG images without external dependencies.
Uses base64 encoded 1x1 colored pixels and scales them up using built-in methods.
"""

import os
import struct
import zlib

def create_png(filename, width, height, r, g, b):
    """Create a simple solid color PNG file."""
    def make_chunk(chunk_type, data):
        chunk_len = struct.pack('>I', len(data))
        chunk_crc = struct.pack('>I', zlib.crc32(chunk_type + data) & 0xffffffff)
        return chunk_len + chunk_type + data + chunk_crc

    # PNG signature
    signature = b'\x89PNG\r\n\x1a\n'

    # IHDR chunk
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr = make_chunk(b'IHDR', ihdr_data)

    # IDAT chunk (image data)
    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'  # filter byte
        for x in range(width):
            raw_data += bytes([r, g, b])

    compressed = zlib.compress(raw_data, 9)
    idat = make_chunk(b'IDAT', compressed)

    # IEND chunk
    iend = make_chunk(b'IEND', b'')

    # Write file
    with open(filename, 'wb') as f:
        f.write(signature + ihdr + idat + iend)


def main():
    os.makedirs("static/Menu", exist_ok=True)

    # Menu items with RGB colors
    items = {
        "Big_Burger_Combo.png": (255, 107, 53),
        "Double_Cheeseburger.png": (247, 147, 30),
        "Cheeseburger.png": (255, 179, 71),
        "Hamburger.png": (139, 69, 19),
        "Crispy_Chicken_Sandwich.png": (222, 184, 135),
        "Chicken_Nuggets__6_pc.png": (218, 165, 32),
        "Filet_Fish_Sandwich.png": (70, 130, 180),
        "Fries.png": (255, 215, 0),
        "Apple_Pie.png": (205, 133, 63),
        "coca_cola.png": (220, 20, 60),
    }

    print("Creating placeholder images...")

    for filename, (r, g, b) in items.items():
        filepath = f"static/Menu/{filename}"
        create_png(filepath, 200, 200, r, g, b)
        print(f"Created: {filepath}")

    print("\nPlaceholder images created!")
    print("Replace these with actual food images for production use.")


if __name__ == "__main__":
    main()
