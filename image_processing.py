"""
Image preprocessing module for solargraphy analysis.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional


class ImageProcessor:
    """Handles image loading and preprocessing."""

    def __init__(self, image_path: Path | str, max_width: int = 2048):
        """
        Initialize image processor.

        Args:
            image_path: Path to image file
            max_width: Maximum image width for processing (respects aspect ratio)
        """
        self.image_path = Path(image_path)
        self.max_width = max_width
        self._original: Optional[np.ndarray] = None
        self._grayscale: Optional[np.ndarray] = None
        self._processed: Optional[np.ndarray] = None

    def load_image(self) -> np.ndarray:
        """Load and resize image."""
        image = cv2.imread(str(self.image_path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Failed to load image: {self.image_path}")

        self._original = self._resize_if_needed(image)
        return self._original

    def preprocess(self) -> np.ndarray:
        """
        Apply full preprocessing pipeline.

        Returns:
            Preprocessed binary image for track detection
        """
        if self._original is None:
            raise RuntimeError("Image not loaded. Call load_image() first.")

        # Convert to grayscale
        gray = cv2.cvtColor(self._original, cv2.COLOR_BGR2GRAY)
        self._grayscale = gray

        # Denoise
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)

        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # Edge enhancement using Laplacian
        laplacian = cv2.Laplacian(enhanced, cv2.CV_64F)
        enhanced = cv2.convertScaleAbs(laplacian)
        enhanced = cv2.normalize(enhanced, None, 0, 255, cv2.NORM_MINMAX).astype(
            np.uint8
        )

        # Adaptive thresholding
        binary = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

        self._processed = binary
        return binary

    def get_original(self) -> np.ndarray:
        """Get original image."""
        if self._original is None:
            raise RuntimeError("Image not loaded")
        return self._original.copy()

    def get_grayscale(self) -> np.ndarray:
        """Get grayscale image."""
        if self._grayscale is None:
            raise RuntimeError("Image not loaded and preprocessed")
        return self._grayscale.copy()

    def get_processed(self) -> np.ndarray:
        """Get processed binary image."""
        if self._processed is None:
            raise RuntimeError("Image not preprocessed")
        return self._processed.copy()

    def get_dimensions(self) -> Tuple[int, int]:
        """Get image height and width."""
        if self._original is None:
            raise RuntimeError("Image not loaded")
        height, width = self._original.shape[:2]
        return height, width

    @staticmethod
    def _resize_if_needed(image: np.ndarray, max_width: int = 2048) -> np.ndarray:
        """Resize image if width exceeds max_width."""
        height, width = image.shape[:2]
        if width > max_width:
            scale = max_width / width
            new_width = max_width
            new_height = int(height * scale)
            return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        return image

    def apply_brightness_correction(self, clip_limit: float = 3.0) -> np.ndarray:
        """Apply advanced contrast correction."""
        if self._grayscale is None:
            raise RuntimeError("Image not loaded")

        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(16, 16))
        corrected = clahe.apply(self._grayscale)
        return corrected

    @staticmethod
    def estimate_noise_level(image: np.ndarray) -> float:
        """Estimate noise level using Laplacian variance."""
        laplacian = cv2.Laplacian(image, cv2.CV_64F)
        noise = laplacian.var()
        return noise
