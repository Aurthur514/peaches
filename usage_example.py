#!/usr/bin/env python3
"""
Usage Example for Drone Image Alignment
=======================================

This script demonstrates how to use the task_1_code.py for aligning
thermal and RGB drone imagery with various options and configurations.

Author: Computer Vision Engineer
Date: November 2025
"""

import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def show_usage_examples():
    """Display comprehensive usage examples for the alignment tool."""
    
    print("="*80)
    print("🚁 DRONE IMAGE ALIGNMENT TOOL - USAGE GUIDE")
    print("="*80)
    print()
    
    print("📋 BASIC USAGE:")
    print("  python task_1_code.py input_folder [output_folder]")
    print()
    
    print("📂 INPUT FOLDER STRUCTURE:")
    print("  input_folder/")
    print("  ├── DJI_0001_T.JPG  (Thermal image)")
    print("  ├── DJI_0001_Z.JPG  (RGB image)")
    print("  ├── DJI_0002_T.JPG")
    print("  ├── DJI_0002_Z.JPG")
    print("  └── ...")
    print()
    
    print("📤 OUTPUT FOLDER STRUCTURE:")
    print("  task_1_output/")
    print("  ├── DJI_0001_AT.JPG (Aligned thermal)")
    print("  ├── DJI_0001_Z.JPG  (Copied RGB)")
    print("  ├── DJI_0002_AT.JPG")
    print("  ├── DJI_0002_Z.JPG")
    print("  └── ...")
    print()
    
    print("🔧 ADVANCED OPTIONS:")
    print("  --detector {SIFT,ORB,AKAZE}  Feature detector algorithm")
    print("  --ratio FLOAT               Lowe's ratio test threshold (0.0-1.0)")
    print("  --min-matches INT           Minimum matches for homography")
    print("  --verbose                   Enable detailed logging")
    print()
    
    print("💡 EXAMPLE COMMANDS:")
    print()
    print("  # Basic usage with default settings:")
    print("  python task_1_code.py drone_images")
    print()
    print("  # Specify custom output folder:")
    print("  python task_1_code.py drone_images aligned_results")
    print()
    print("  # Use ORB detector for faster processing:")
    print("  python task_1_code.py drone_images output --detector ORB")
    print()
    print("  # More strict matching criteria:")
    print("  python task_1_code.py drone_images output --ratio 0.6 --min-matches 15")
    print()
    print("  # Verbose output for debugging:")
    print("  python task_1_code.py drone_images output --verbose")
    print()
    
    print("⚙️ ALGORITHM SELECTION GUIDE:")
    print()
    print("  🎯 SIFT (Default - Recommended):")
    print("     • Best quality and accuracy")
    print("     • Handles scale and rotation well")
    print("     • Slower but most robust")
    print()
    print("  ⚡ ORB (Fast):")
    print("     • Faster processing")
    print("     • Good for real-time applications")
    print("     • Less accurate than SIFT")
    print()
    print("  🔄 AKAZE (Balanced):")
    print("     • Good balance of speed and accuracy")
    print("     • Handles blur well")
    print("     • Memory efficient")
    print()
    
    print("📊 PARAMETER TUNING TIPS:")
    print()
    print("  📐 Match Ratio (--ratio):")
    print("     • Lower values (0.5-0.7): More strict matching, fewer false positives")
    print("     • Higher values (0.7-0.9): More permissive, more matches but less reliable")
    print("     • Default 0.75 works well for most cases")
    print()
    print("  🔢 Minimum Matches (--min-matches):")
    print("     • Higher values: More reliable transformation, may fail on sparse scenes")
    print("     • Lower values: Works with fewer features, less reliable")
    print("     • Default 10 is good for typical drone imagery")
    print()
    
    print("🚨 TROUBLESHOOTING:")
    print()
    print("  ❌ \"Insufficient matches\" errors:")
    print("     • Try ORB or AKAZE detector")
    print("     • Increase --ratio threshold")
    print("     • Decrease --min-matches")
    print("     • Check if images actually show the same scene")
    print()
    print("  ❌ \"Homography computation failed\":")
    print("     • Images may be too different")
    print("     • Try different detector")
    print("     • Check for sufficient overlap between images")
    print()
    print("  ❌ Poor alignment quality:")
    print("     • Decrease --ratio for stricter matching")
    print("     • Increase --min-matches")
    print("     • Use SIFT detector for better accuracy")
    print()
    
    print("📝 LOG FILE:")
    print("  • Detailed processing log saved to: image_alignment.log")
    print("  • Use --verbose for more detailed console output")
    print()
    
    print("="*80)


def check_file_structure(folder_path):
    """
    Check if the input folder has the correct structure for processing.
    
    Args:
        folder_path: Path to the input folder
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        logger.error(f"Folder does not exist: {folder_path}")
        return False
    
    # Find thermal and RGB files
    thermal_files = list(folder.glob("*_T.JPG")) + list(folder.glob("*_T.jpg"))
    rgb_files = list(folder.glob("*_Z.JPG")) + list(folder.glob("*_Z.jpg"))
    
    logger.info(f"Found {len(thermal_files)} thermal images (*_T.JPG)")
    logger.info(f"Found {len(rgb_files)} RGB images (*_Z.JPG)")
    
    if len(thermal_files) == 0:
        logger.error("No thermal images found! Expected format: *_T.JPG")
        return False
    
    if len(rgb_files) == 0:
        logger.error("No RGB images found! Expected format: *_Z.JPG")
        return False
    
    # Check for pairs
    pairs = 0
    for thermal_file in thermal_files:
        base_name = thermal_file.stem.replace("_T", "")
        rgb_file = folder / f"{base_name}_Z.JPG"
        if not rgb_file.exists():
            rgb_file = folder / f"{base_name}_Z.jpg"
        
        if rgb_file.exists():
            pairs += 1
        else:
            logger.warning(f"No RGB pair found for: {thermal_file.name}")
    
    logger.info(f"Found {pairs} valid image pairs")
    
    if pairs == 0:
        logger.error("No valid image pairs found!")
        return False
    
    return True


def create_sample_structure():
    """Create a sample folder structure to demonstrate the expected format."""
    sample_dir = Path("sample_input")
    sample_dir.mkdir(exist_ok=True)
    
    readme_content = """
SAMPLE INPUT FOLDER STRUCTURE
============================

This folder shows the expected structure for drone image pairs:

Required naming convention:
- Thermal images: [ID]_T.JPG
- RGB images: [ID]_Z.JPG

Examples:
- DJI_0001_T.JPG ← Thermal camera image
- DJI_0001_Z.JPG ← RGB camera image (same drone position)
- DJI_0002_T.JPG
- DJI_0002_Z.JPG
- etc.

The ID part (DJI_0001) can be any string, but it must match
between the thermal and RGB images from the same capture.

To process your images:
1. Organize them in this format
2. Run: python task_1_code.py your_folder_name

The script will automatically find all pairs and align them.
"""
    
    with open(sample_dir / "README.txt", "w") as f:
        f.write(readme_content)
    
    logger.info(f"Created sample structure in: {sample_dir}/")
    logger.info("Check README.txt for detailed instructions")


def main():
    """Main function for the usage example."""
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            show_usage_examples()
            return
        elif sys.argv[1] == "--check":
            if len(sys.argv) > 2:
                check_file_structure(sys.argv[2])
            else:
                logger.error("Please specify folder to check: python usage_example.py --check folder_path")
            return
        elif sys.argv[1] == "--create-sample":
            create_sample_structure()
            return
    
    print("🚁 DRONE IMAGE ALIGNMENT - USAGE HELPER")
    print()
    print("Available commands:")
    print("  python usage_example.py --help           Show detailed usage guide")
    print("  python usage_example.py --check FOLDER   Check folder structure")
    print("  python usage_example.py --create-sample  Create sample folder structure")
    print()
    print("Quick start:")
    print("  1. Organize your images: [ID]_T.JPG (thermal) and [ID]_Z.JPG (RGB)")
    print("  2. Run: python task_1_code.py your_input_folder")
    print("  3. Find results in: task_1_output/")
    print()
    print("For detailed help: python usage_example.py --help")


if __name__ == "__main__":
    main()