#!/usr/bin/env python3
"""
Generate sample solargraphy image for testing.
"""

import cv2
import numpy as np
from pathlib import Path


def create_sample_solargraphy() -> None:
    """Create synthetic solargraphy image."""
    height, width = 600, 800
    image = np.zeros((height, width, 3), dtype=np.uint8)

    # Background
    image[:] = (20, 15, 10)

    # Generate sun tracks
    for track_idx in range(5):
        angle = 25 + track_idx * 8
        amplitude = 150 - track_idx * 15
        y_offset = height // 2 - track_idx * 30

        for x in range(width):
            y = int(y_offset + amplitude * np.sin(np.radians(angle) * (x / width)))
            if 0 <= y < height:
                # Draw thick arc
                for offset in range(-3, 4):
                    if 0 <= y + offset < height:
                        brightness = 150 + offset * 10 + np.random.randint(-20, 20)
                        brightness = np.clip(brightness, 0, 255)
                        image[y + offset, x] = (brightness, brightness // 2, 0)

    # Add noise
    noise = np.random.normal(0, 10, image.shape).astype(np.int16)
    image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    output_path = Path("sample_solargraphy.jpg")
    cv2.imwrite(str(output_path), image)
    print(f"✓ Sample image created: {output_path}")


if __name__ == "__main__":
    create_sample_solargraphy()
