"""
Sun track detection module.
Identifies and analyzes sun trajectories in solargraphy images.
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class TrackData:
    """Data structure for detected sun track."""

    index: int
    centroid: Tuple[float, float]
    area: float
    perimeter: float
    eccentricity: float
    orientation: float
    brightness_profile: np.ndarray


class SunTrackDetector:
    """Detects sun tracks in processed solargraphy images."""

    MIN_TRACK_AREA = 50
    MAX_TRACK_AREA = 50000
    MIN_TRACK_SOLIDITY = 0.4

    def __init__(self, processed: np.ndarray, original: np.ndarray):
        """
        Initialize detector.

        Args:
            processed: Binary processed image
            original: Original color image
        """
        self.processed = processed
        self.original = original
        self.height, self.width = processed.shape[:2]

    def detect_tracks(self) -> Tuple[List[np.ndarray], List[TrackData]]:
        """
        Detect sun tracks in image.

        Returns:
            Tuple of (contours list, TrackData list)
        """
        contours, _ = cv2.findContours(
            self.processed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        valid_contours = []
        track_data_list = []

        for idx, contour in enumerate(contours):
            area = cv2.contourArea(contour)

            # Filter by area
            if area < self.MIN_TRACK_AREA or area > self.MAX_TRACK_AREA:
                continue

            # Filter by solidity
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            solidity = area / hull_area if hull_area > 0 else 0
            if solidity < self.MIN_TRACK_SOLIDITY:
                continue

            # Calculate moments for centroid
            M = cv2.moments(contour)
            if M["m00"] == 0:
                continue

            cx = M["m10"] / M["m00"]
            cy = M["m01"] / M["m00"]

            # Calculate perimeter
            perimeter = cv2.arcLength(contour, True)

            # Fit ellipse if possible
            eccentricity, orientation = self._calculate_ellipse_params(contour)

            # Extract brightness profile
            brightness_profile = self._extract_brightness(contour)

            track = TrackData(
                index=len(valid_contours),
                centroid=(cx, cy),
                area=area,
                perimeter=perimeter,
                eccentricity=eccentricity,
                orientation=orientation,
                brightness_profile=brightness_profile,
            )

            valid_contours.append(contour)
            track_data_list.append(track)

        # Sort by x-coordinate (time progression)
        if track_data_list:
            sorted_indices = np.argsort([t.centroid[0] for t in track_data_list])
            valid_contours = [valid_contours[i] for i in sorted_indices]
            track_data_list = [track_data_list[i] for i in sorted_indices]

            # Reindex
            for i, track in enumerate(track_data_list):
                track.index = i

        return valid_contours, track_data_list

    def detect_horizon(self) -> Optional[float]:
        """
        Detect horizon line using Hough transform.

        Returns:
            Y-coordinate of horizon or None
        """
        edges = cv2.Canny(self.processed, 50, 150)
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 100)

        if lines is None:
            return None

        # Find most horizontal line
        horizontal_lines = []
        for line in lines:
            rho, theta = line[0]
            if np.abs(np.sin(theta)) < 0.2:  # Near horizontal
                y = int(rho / np.cos(theta)) if np.cos(theta) != 0 else None
                if y is not None and 0 < y < self.height:
                    horizontal_lines.append(y)

        if horizontal_lines:
            return float(np.median(horizontal_lines))

        return None

    def estimate_cloudiness(self) -> float:
        """
        Estimate cloudiness percentage.

        Returns:
            Cloudiness as percentage (0-100)
        """
        white_pixels = np.sum(self.processed == 255)
        total_pixels = self.height * self.width
        return (white_pixels / total_pixels) * 100

    @staticmethod
    def _calculate_ellipse_params(contour: np.ndarray) -> Tuple[float, float]:
        """Calculate eccentricity and orientation from contour."""
        if len(contour) < 5:
            return 0.0, 0.0

        try:
            ellipse = cv2.fitEllipse(contour)
            (cx, cy), (major, minor), angle = ellipse

            if major > 0:
                eccentricity = np.sqrt(1 - (minor / major) ** 2)
            else:
                eccentricity = 0.0

            return eccentricity, angle

        except cv2.error:
            return 0.0, 0.0

    def _extract_brightness(self, contour: np.ndarray) -> np.ndarray:
        """Extract brightness values within contour."""
        gray = cv2.cvtColor(self.original, cv2.COLOR_BGR2GRAY)
        mask = np.zeros(self.processed.shape, dtype=np.uint8)
        cv2.drawContours(mask, [contour], 0, 255, -1)

        brightness = gray[mask == 255].flatten()
        return brightness if len(brightness) > 0 else np.array([0])
