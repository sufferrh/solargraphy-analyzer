#!/usr/bin/env python3
"""
Solargraphy Image Analysis - Main Entry Point
Analyzes solarography images to extract sun trajectories and solar data.
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

from image_processing import ImageProcessor
from sun_detection import SunTrackDetector
from plotting import AnalysisVisualizer
from utils import OutputManager, AstronomicalComparison


def setup_logging(output_dir: Path) -> logging.Logger:
    """Configure logging to file and console."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(output_dir / "analysis.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def validate_image_path(image_path: str) -> Path:
    """Validate image file exists and has supported format."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    supported_formats = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
    if path.suffix.lower() not in supported_formats:
        raise ValueError(
            f"Unsupported image format: {path.suffix}. "
            f"Supported: {supported_formats}"
        )

    return path


def analyze_solargraphy(image_path: str, output_dir: Optional[str] = None) -> None:
    """
    Main analysis pipeline.

    Args:
        image_path: Path to solargraphy image
        output_dir: Optional custom output directory
    """
    image_path = validate_image_path(image_path)
    output_manager = OutputManager(output_dir or "output")
    logger = setup_logging(output_manager.base_dir)

    logger.info(f"Starting solargraphy analysis: {image_path}")

    try:
        # Step 1: Load and preprocess image
        logger.info("Step 1/6: Loading and preprocessing image...")
        processor = ImageProcessor(image_path)
        original = processor.load_image()
        processed = processor.preprocess()

        # Step 2: Detect sun tracks
        logger.info("Step 2/6: Detecting sun tracks...")
        detector = SunTrackDetector(processed, original)
        tracks, track_data = detector.detect_tracks()
        cloudiness = detector.estimate_cloudiness()
        horizon = detector.detect_horizon()

        logger.info(f"Detected {len(tracks)} sun track(s)")
        logger.info(f"Cloudiness estimate: {cloudiness:.1f}%")

        # Step 3: Visualize tracks
        logger.info("Step 3/6: Generating visualizations...")
        visualizer = AnalysisVisualizer(
            original, processed, tracks, track_data, horizon
        )
        visualizer.draw_tracks()
        visualizer.save_image(output_manager.images_dir / "output_tracks.png")

        # Step 4: Create analysis plots
        logger.info("Step 4/6: Creating analysis plots...")
        visualizer.plot_altitude_profile()
        visualizer.plot_brightness_heatmap()
        visualizer.plot_track_statistics()

        visualizer.save_plots(output_manager.plots_dir)

        # Step 5: Compare with astronomical data
        logger.info("Step 5/6: Comparing with astronomical model...")
        comparator = AstronomicalComparison(image_path, track_data)
        comparison_results = comparator.compare_with_model()
        logger.info(f"Astronomical comparison complete")

        # Step 6: Save results
        logger.info("Step 6/6: Saving results...")
        output_manager.save_tracks_csv(track_data)
        output_manager.save_comparison_csv(comparison_results)
        output_manager.save_summary(
            {
                "image_file": str(image_path),
                "tracks_detected": len(tracks),
                "cloudiness_percent": cloudiness,
                "horizon_detected": horizon is not None,
                "processing_status": "SUCCESS",
            }
        )

        logger.info("✓ Analysis complete")
        logger.info(f"Results saved to: {output_manager.base_dir}")

    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        output_manager.save_summary(
            {
                "image_file": str(image_path),
                "processing_status": "FAILED",
                "error": str(e),
            }
        )
        sys.exit(1)


def main() -> None:
    """Parse arguments and run analysis."""
    parser = argparse.ArgumentParser(
        description="Solargraphy Image Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --image solargraphy.jpg
  python main.py --image data/solar.png --output results/
        """,
    )

    parser.add_argument(
        "--image",
        type=str,
        required=True,
        help="Path to solargraphy image (jpg, png, tif)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory (default: ./output)",
    )

    args = parser.parse_args()

    analyze_solargraphy(args.image, args.output)


if __name__ == "__main__":
    main()
