"""
Visualization module for solargraphy analysis results.
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Dict, Optional

from sun_detection import TrackData


class AnalysisVisualizer:
    """Handles visualization and plotting of analysis results."""

    def __init__(
        self,
        original: np.ndarray,
        processed: np.ndarray,
        tracks: List[np.ndarray],
        track_data: List[TrackData],
        horizon: Optional[float] = None,
    ):
        """
        Initialize visualizer.

        Args:
            original: Original color image
            processed: Processed binary image
            tracks: List of contours representing sun tracks
            track_data: List of TrackData objects
            horizon: Y-coordinate of detected horizon
        """
        self.original = original.copy()
        self.processed = processed.copy()
        self.tracks = tracks
        self.track_data = track_data
        self.horizon = horizon
        self.annotated = self.original.copy()
        self.height, self.width = original.shape[:2]
        self._stored_figures: Dict[str, plt.Figure] = {}

        plt.style.use("dark_background")

    def draw_tracks(self) -> None:
        """Draw detected tracks on original image."""
        if not self.tracks:
            return

        colors = self._generate_colors(len(self.tracks))

        for i, (contour, color) in enumerate(zip(self.tracks, colors)):
            cv2.drawContours(self.annotated, [contour], 0, color, 2)

            if self.track_data[i].centroid:
                centroid = tuple(map(int, self.track_data[i].centroid))
                cv2.circle(self.annotated, centroid, 5, color, -1)

        if self.horizon is not None:
            y = int(self.horizon)
            cv2.line(self.annotated, (0, y), (self.width, y), (255, 255, 0), 2)

    def plot_altitude_profile(self) -> None:
        """Create altitude vs. time profile plot."""
        fig, ax = plt.subplots(figsize=(12, 6), dpi=150)

        if not self.track_data:
            ax.text(0.5, 0.5, "No tracks detected", ha="center", va="center")
            self._store_figure(fig, "altitude_profile")
            return

        x_coords = np.array([t.centroid[0] for t in self.track_data])
        y_coords = np.array([t.centroid[1] for t in self.track_data])

        time_normalized = x_coords / self.width
        altitude = 90 * (1 - y_coords / self.height)

        ax.scatter(time_normalized, altitude, s=100, c="orange", marker="o",
                   label="Detected positions", zorder=3)

        if len(self.track_data) > 2:
            try:
                from scipy.interpolate import UnivariateSpline

                spline = UnivariateSpline(
                    time_normalized,
                    altitude,
                    k=min(3, len(self.track_data) - 1),
                    s=100
                )
                x_smooth = np.linspace(0, 1, 200)
                y_smooth = spline(x_smooth)
                ax.plot(x_smooth, y_smooth, "c-", linewidth=2,
                        label="Fitted trajectory", zorder=2)
            except Exception:
                pass

        ax.set_xlabel("Time Progression (normalized)", fontsize=12, fontweight="bold")
        ax.set_ylabel("Solar Altitude (degrees)", fontsize=12, fontweight="bold")
        ax.set_title("Solar Altitude Profile", fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="best")
        ax.set_ylim(-10, 100)

        self._store_figure(fig, "altitude_profile")

    def plot_brightness_heatmap(self) -> None:
        """Create brightness intensity heatmap."""
        fig, ax = plt.subplots(figsize=(12, 8), dpi=150)

        gray = cv2.cvtColor(self.original, cv2.COLOR_BGR2GRAY)
        im = ax.imshow(gray, cmap="hot", origin="upper")
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label("Pixel Intensity", fontweight="bold")

        if self.track_data:
            centroids = np.array([t.centroid for t in self.track_data])
            ax.scatter(
                centroids[:, 0],
                centroids[:, 1],
                s=80,
                c="cyan",
                marker="x",
                linewidths=2,
                label="Track centroids",
            )

        ax.set_xlabel("X Position (pixels)", fontsize=11, fontweight="bold")
        ax.set_ylabel("Y Position (pixels)", fontsize=11, fontweight="bold")
        ax.set_title("Brightness Distribution Heatmap", fontsize=13, fontweight="bold")
        ax.legend(loc="upper right")

        self._store_figure(fig, "brightness_heatmap")

    def plot_track_statistics(self) -> None:
        """Create track statistics visualization."""
        if not self.track_data:
            return

        fig, axes = plt.subplots(2, 2, figsize=(12, 10), dpi=150)

        # Track areas
        areas = [t.area for t in self.track_data]
        axes[0, 0].bar(range(len(areas)), areas, color="skyblue", edgecolor="white")
        axes[0, 0].set_xlabel("Track Index", fontweight="bold")
        axes[0, 0].set_ylabel("Area (pixels²)", fontweight="bold")
        axes[0, 0].set_title("Track Areas", fontweight="bold")
        axes[0, 0].grid(axis="y", alpha=0.3)

        # Brightness distributions
        for i, track in enumerate(self.track_data):
            axes[0, 1].hist(
                track.brightness_profile,
                bins=30,
                alpha=0.6,
                label=f"Track {i}",
            )
        axes[0, 1].set_xlabel("Brightness (0-255)", fontweight="bold")
        axes[0, 1].set_ylabel("Frequency", fontweight="bold")
        axes[0, 1].set_title("Brightness Distribution", fontweight="bold")
        axes[0, 1].legend(fontsize=8)
        axes[0, 1].grid(axis="y", alpha=0.3)

        # Eccentricity
        eccentricity = [t.eccentricity for t in self.track_data]
        axes[1, 0].plot(
            range(len(eccentricity)),
            eccentricity,
            marker="o",
            color="lime",
            linewidth=2,
        )
        axes[1, 0].set_xlabel("Track Index", fontweight="bold")
        axes[1, 0].set_ylabel("Eccentricity", fontweight="bold")
        axes[1, 0].set_title("Track Eccentricity", fontweight="bold")
        axes[1, 0].grid(True, alpha=0.3)

        # Perimeter vs Area
        perimeters = [t.perimeter for t in self.track_data]
        axes[1, 1].scatter(areas, perimeters, s=100, c=range(len(areas)), cmap="viridis")
        axes[1, 1].set_xlabel("Area (pixels²)", fontweight="bold")
        axes[1, 1].set_ylabel("Perimeter (pixels)", fontweight="bold")
        axes[1, 1].set_title("Area vs Perimeter", fontweight="bold")
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        self._store_figure(fig, "track_statistics")

    def save_image(self, output_path: Path) -> None:
        """Save annotated image."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), self.annotated)

    def save_plots(self, output_dir: Path) -> None:
        """Save all generated plots."""
        output_dir.mkdir(parents=True, exist_ok=True)
        for filename, fig in self._stored_figures.items():
            fig.savefig(output_dir / filename, dpi=150, bbox_inches="tight")
            plt.close(fig)

    @staticmethod
    def _generate_colors(count: int) -> List[tuple]:
        """Generate distinct colors for tracks."""
        colors = [
            (0, 255, 255),
            (255, 0, 255),
            (0, 255, 0),
            (255, 255, 0),
            (255, 128, 0),
            (128, 0, 255),
            (255, 0, 128),
            (128, 255, 0),
        ]
        return [colors[i % len(colors)] for i in range(count)]

    def _store_figure(self, fig: plt.Figure, filename: str) -> None:
        """Store figure for later saving."""
        self._stored_figures[f"{filename}.png"] = fig
