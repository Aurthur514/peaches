#!/usr/bin/env python3
"""
Test Script for Drone Image Alignment
=====================================

This script helps test the image alignment functionality with sample data
and provides debugging capabilities.

Usage:
    python test_alignment.py
"""

import cv2
import numpy as np
import os
from pathlib import Path
import logging

# Configure logging for testing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_data():
    """
    Create synthetic test data to verify the alignment algorithm.
    This generates a pair of images with known transformation.
    """
    logger.info("Creating synthetic test data...")
    
    # Create test directory
    test_dir = Path("test_images")
    test_dir.mkdir(exist_ok=True)
    
    # Create a synthetic RGB image with features
    rgb_img = np.zeros((800, 1200, 3), dtype=np.uint8)
    
    # Add some geometric features for matching
    # Rectangles
    cv2.rectangle(rgb_img, (100, 100), (300, 200), (255, 255, 255), -1)
    cv2.rectangle(rgb_img, (500, 300), (700, 400), (128, 128, 128), -1)
    cv2.rectangle(rgb_img, (200, 500), (400, 600), (64, 64, 64), -1)
    
    # Circles
    cv2.circle(rgb_img, (800, 200), 80, (255, 255, 255), -1)
    cv2.circle(rgb_img, (300, 400), 50, (192, 192, 192), -1)
    
    # Lines for additional features
    cv2.line(rgb_img, (0, 400), (1200, 400), (255, 255, 255), 3)
    cv2.line(rgb_img, (600, 0), (600, 800), (255, 255, 255), 3)
    
    # Add some text
    cv2.putText(rgb_img, "RGB TEST", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)
    
    # Create a thermal image by applying transformation
    # Define transformation parameters
    angle = 5  # 5 degree rotation
    scale = 0.8  # Slight scale difference
    tx, ty = 50, 30  # Translation
    
    # Create transformation matrix
    center = (rgb_img.shape[1]//2, rgb_img.shape[0]//2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, scale)
    rotation_matrix[0, 2] += tx
    rotation_matrix[1, 2] += ty
    
    # Apply transformation to create thermal image
    thermal_img = cv2.warpAffine(rgb_img, rotation_matrix, (rgb_img.shape[1], rgb_img.shape[0]))
    
    # Convert thermal to single channel (simulate thermal camera)
    thermal_gray = cv2.cvtColor(thermal_img, cv2.COLOR_BGR2GRAY)
    thermal_img = cv2.applyColorMap(thermal_gray, cv2.COLORMAP_JET)
    
    # Resize thermal image to simulate different resolution
    thermal_img = cv2.resize(thermal_img, (640, 480))
    
    # Save test images
    cv2.imwrite(str(test_dir / "TEST_001_Z.JPG"), rgb_img)
    cv2.imwrite(str(test_dir / "TEST_001_T.JPG"), thermal_img)
    
    logger.info(f"Test images created in {test_dir}/")
    return str(test_dir)


def verify_installation():
    """Verify that all required packages are properly installed."""
    logger.info("Verifying installation...")
    
    try:
        import cv2
        logger.info(f"✅ OpenCV version: {cv2.__version__}")
        
        # Check if SIFT is available
        try:
            sift = cv2.SIFT_create()
            logger.info("✅ SIFT detector available")
        except Exception as e:
            logger.warning(f"⚠️  SIFT not available: {e}")
        
        # Check ORB
        try:
            orb = cv2.ORB_create()
            logger.info("✅ ORB detector available")
        except Exception as e:
            logger.warning(f"⚠️  ORB not available: {e}")
        
        # Check AKAZE
        try:
            akaze = cv2.AKAZE_create()
            logger.info("✅ AKAZE detector available")
        except Exception as e:
            logger.warning(f"⚠️  AKAZE not available: {e}")
        
        import numpy as np
        logger.info(f"✅ NumPy version: {np.__version__}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        logger.info("Please install requirements: pip install -r cv_requirements.txt")
        return False


def test_alignment():
    """Test the alignment functionality with synthetic data."""
    logger.info("Testing alignment functionality...")
    
    # Verify installation first
    if not verify_installation():
        return False
    
    # Create test data
    test_dir = create_test_data()
    
    # Import and test the aligner
    try:
        from task_1_code import DroneImageAligner
        
        # Initialize aligner
        aligner = DroneImageAligner(feature_detector='SIFT', min_matches=8)
        
        # Process test images
        output_dir = "test_output"
        stats = aligner.process_folder(test_dir, output_dir)
        
        if stats['successful'] > 0:
            logger.info("✅ Alignment test successful!")
            logger.info(f"📁 Test results in: {output_dir}/")
            return True
        else:
            logger.error("❌ Alignment test failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False


def main():
    """Main test function."""
    logger.info("="*50)
    logger.info("DRONE IMAGE ALIGNMENT - TEST SUITE")
    logger.info("="*50)
    
    success = test_alignment()
    
    if success:
        logger.info("\n🎉 All tests passed! The alignment system is ready to use.")
        logger.info("\nTo process your own drone images:")
        logger.info("  python task_1_code.py your_input_folder task_1_output")
    else:
        logger.error("\n❌ Tests failed. Please check the installation and try again.")


if __name__ == "__main__":
    main()