"""
Utility functions for output management and astronomical calculations.
"""

import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

from sun_detection import TrackData


class OutputManager:
    """Manages output directory structure and file operations."""

    def __init__(self, base_dir: str = "output"):
        """Initialize output manager."""
        self.base_dir = Path(base_dir)
        self.images_dir = self.base_dir / "images"
        self.plots_dir = self.base_dir / "plots"
        self.data_dir = self.base_dir / "data"

        for directory in [self.images_dir, self.plots_dir, self.data_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def save_tracks_csv(self, track_data: List[TrackData]) -> Path:
        """Save track data to CSV."""
        csv_path = self.data_dir / "sun_tracks.csv"

        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "index",
                    "centroid_x",
                    "centroid_y",
                    "area",
                    "perimeter",
                    "eccentricity",
                    "orientation",
                    "avg_brightness",
                ],
            )
            writer.writeheader()

            for track in track_data:
                writer.writerow(
                    {
                        "index": track.index,
                        "centroid_x": f"{track.centroid[0]:.2f}",
                        "centroid_y": f"{track.centroid[1]:.2f}",
                        "area": f"{track.area:.2f}",
                        "perimeter": f"{track.perimeter:.2f}",
                        "eccentricity": f"{track.eccentricity:.4f}",
                        "orientation": f"{track.orientation:.2f}",
                        "avg_brightness": f"{track.brightness_profile.mean():.2f}",
                    }
                )

        return csv_path

    def save_comparison_csv(self, comparison_data: Dict[str, Any]) -> Path:
        """Save astronomical comparison to CSV."""
        csv_path = self.data_dir / "astronomical_comparison.csv"

        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(comparison_data.keys()))
            writer.writeheader()
            writer.writerow(comparison_data)

        return csv_path

    def save_summary(self, summary_data: Dict[str, Any]) -> Path:
        """Save analysis summary."""
        txt_path = self.data_dir / "summary.txt"

        with open(txt_path, "w") as f:
            f.write("SOLARGRAPHY ANALYSIS SUMMARY\n")
            f.write("=" * 50 + "\n\n")

            for key, value in summary_data.items():
                f.write(f"{key}: {value}\n")

            f.write(f"\nGenerated: {datetime.now().isoformat()}\n")

        return txt_path


class AstronomicalComparison:
    """Compares detected sun positions with astronomical models."""

    def __init__(self, image_path: Path | str, track_data: List[TrackData]):
        """Initialize comparator."""
        self.image_path = Path(image_path)
        self.track_data = track_data
        self.observation_date = self._extract_date_from_filename()

    def compare_with_model(self) -> Dict[str, Any]:
        """
        Compare observed with theoretical solar positions.

        Returns:
            Dictionary with comparison results
        """
        results = {
            "observation_date": str(self.observation_date) if self.observation_date else "unknown",
            "tracks_detected": len(self.track_data),
            "model_status": "N/A",
        }

        if self.observation_date:
            try:
                from astral import Observer, sun
                from datetime import datetime as dt

                results["model_status"] = "successful"

                # Use approximate coordinates (latitude 55°, longitude 37° - Moscow)
                observer = Observer(latitude=55.75, longitude=37.62, elevation=100)

                sunrise = sun.sun(observer, date=self.observation_date)["sunrise"]
                sunset = sun.sun(observer, date=self.observation_date)["sunset"]

                results["theoretical_sunrise"] = sunrise.isoformat()
                results["theoretical_sunset"] = sunset.isoformat()
                results["day_length_hours"] = (sunset - sunrise).total_seconds() / 3600

            except ImportError:
                results["model_status"] = "astral library not available"
            except Exception as e:
                results["model_status"] = f"error: {str(e)}"

        return results

    def _extract_date_from_filename(self) -> Optional[datetime]:
        """Extract date from filename (YYYY-MM-DD format)."""
        try:
            match = re.search(r"(\d{4})-(\d{2})-(\d{2})", str(self.image_path))
            if match:
                return datetime.strptime(match.group(0), "%Y-%m-%d")
        except Exception:
            pass

        return None
