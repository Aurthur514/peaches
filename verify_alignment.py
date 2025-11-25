#!/usr/bin/env python3
"""
Alignment Quality Verification Tool
==================================

This script helps verify and analyze the quality of thermal-RGB image alignment
by comparing key features and providing visual feedback.

Usage: python verify_alignment.py [output_folder]
"""

import cv2
import numpy as np
import os
import sys
from pathlib import Path
import argparse

def load_image_pair(base_path, image_id):
    """Load aligned thermal and RGB image pair."""
    thermal_path = base_path / f"{image_id}_AT.JPG"
    rgb_path = base_path / f"{image_id}_Z.JPG"
    
    if not thermal_path.exists() or not rgb_path.exists():
        return None, None
    
    thermal = cv2.imread(str(thermal_path))
    rgb = cv2.imread(str(rgb_path))
    
    return thermal, rgb

def create_overlay_comparison(thermal, rgb, alpha=0.5):
    """Create overlay comparison of thermal and RGB images."""
    if thermal is None or rgb is None:
        return None
    
    # Ensure same dimensions
    if thermal.shape != rgb.shape:
        thermal = cv2.resize(thermal, (rgb.shape[1], rgb.shape[0]))
    
    # Create weighted overlay
    overlay = cv2.addWeighted(rgb, 1-alpha, thermal, alpha, 0)
    
    return overlay

def create_side_by_side_comparison(thermal, rgb):
    """Create side-by-side comparison."""
    if thermal is None or rgb is None:
        return None
    
    # Ensure same height
    height = min(thermal.shape[0], rgb.shape[0])
    thermal_resized = cv2.resize(thermal, (int(thermal.shape[1] * height / thermal.shape[0]), height))
    rgb_resized = cv2.resize(rgb, (int(rgb.shape[1] * height / rgb.shape[0]), height))
    
    # Concatenate horizontally
    comparison = np.hstack([rgb_resized, thermal_resized])
    
    # Add labels
    cv2.putText(comparison, "RGB", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(comparison, "Aligned Thermal", (rgb_resized.shape[1] + 10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    return comparison

def create_difference_map(thermal, rgb):
    """Create difference map to show alignment errors."""
    if thermal is None or rgb is None:
        return None
    
    # Convert to grayscale
    thermal_gray = cv2.cvtColor(thermal, cv2.COLOR_BGR2GRAY)
    rgb_gray = cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY)
    
    # Compute absolute difference
    diff = cv2.absdiff(thermal_gray, rgb_gray)
    
    # Apply colormap for better visualization
    diff_colored = cv2.applyColorMap(diff, cv2.COLORMAP_JET)
    
    return diff_colored

def analyze_alignment_quality(thermal, rgb):
    """Analyze alignment quality metrics."""
    if thermal is None or rgb is None:
        return {}
    
    # Convert to grayscale
    thermal_gray = cv2.cvtColor(thermal, cv2.COLOR_BGR2GRAY)
    rgb_gray = cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY)
    
    # Calculate structural similarity (requires skimage, optional)
    try:
        from skimage.metrics import structural_similarity as ssim
        ssim_score = ssim(thermal_gray, rgb_gray)
    except ImportError:
        ssim_score = None
    
    # Calculate correlation coefficient
    correlation = cv2.matchTemplate(thermal_gray, rgb_gray, cv2.TM_CCORR_NORMED)[0, 0]
    
    # Calculate mean squared error
    mse = np.mean((thermal_gray.astype(float) - rgb_gray.astype(float)) ** 2)
    
    return {
        'ssim': ssim_score,
        'correlation': correlation,
        'mse': mse,
        'thermal_shape': thermal.shape,
        'rgb_shape': rgb.shape
    }

def verify_all_alignments(output_folder):
    """Verify all alignments in the output folder."""
    output_path = Path(output_folder)
    
    if not output_path.exists():
        print(f"❌ Output folder not found: {output_folder}")
        return
    
    # Find all aligned thermal images
    thermal_files = list(output_path.glob("*_AT.JPG"))
    
    if not thermal_files:
        print(f"❌ No aligned thermal images found in {output_folder}")
        return
    
    print(f"🔍 Analyzing {len(thermal_files)} aligned image pairs...")
    print("=" * 80)
    
    verification_folder = output_path / "verification"
    verification_folder.mkdir(exist_ok=True)
    
    total_quality_score = 0
    processed_count = 0
    
    for thermal_file in thermal_files:
        # Extract image ID
        image_id = thermal_file.stem.replace("_AT", "")
        
        print(f"\n📸 Analyzing: {image_id}")
        
        # Load image pair
        thermal, rgb = load_image_pair(output_path, image_id)
        
        if thermal is None or rgb is None:
            print(f"❌ Could not load pair for {image_id}")
            continue
        
        # Analyze quality
        metrics = analyze_alignment_quality(thermal, rgb)
        
        print(f"   📊 Metrics:")
        print(f"      • Correlation: {metrics['correlation']:.3f}")
        print(f"      • MSE: {metrics['mse']:.2f}")
        if metrics['ssim'] is not None:
            print(f"      • SSIM: {metrics['ssim']:.3f}")
        print(f"      • Dimensions: Thermal {metrics['thermal_shape']}, RGB {metrics['rgb_shape']}")
        
        # Create visualizations
        overlay = create_overlay_comparison(thermal, rgb, alpha=0.4)
        side_by_side = create_side_by_side_comparison(thermal, rgb)
        diff_map = create_difference_map(thermal, rgb)
        
        # Save verification images
        if overlay is not None:
            cv2.imwrite(str(verification_folder / f"{image_id}_overlay.jpg"), overlay)
        
        if side_by_side is not None:
            cv2.imwrite(str(verification_folder / f"{image_id}_comparison.jpg"), side_by_side)
        
        if diff_map is not None:
            cv2.imwrite(str(verification_folder / f"{image_id}_difference.jpg"), diff_map)
        
        # Calculate quality score (correlation is a good indicator)
        quality_score = metrics['correlation']
        total_quality_score += quality_score
        processed_count += 1
        
        # Quality assessment
        if quality_score > 0.7:
            quality_status = "✅ Excellent"
        elif quality_score > 0.5:
            quality_status = "🟡 Good"
        elif quality_score > 0.3:
            quality_status = "🟠 Fair"
        else:
            quality_status = "❌ Poor"
        
        print(f"   🎯 Quality: {quality_status} ({quality_score:.3f})")
    
    # Overall statistics
    print("\n" + "=" * 80)
    print("📈 OVERALL ALIGNMENT QUALITY")
    print("=" * 80)
    
    if processed_count > 0:
        avg_quality = total_quality_score / processed_count
        print(f"📊 Average Quality Score: {avg_quality:.3f}")
        print(f"🎯 Successfully Processed: {processed_count}/{len(thermal_files)} pairs")
        
        # Overall assessment
        if avg_quality > 0.7:
            overall_status = "🎉 Excellent alignment quality!"
        elif avg_quality > 0.5:
            overall_status = "✅ Good alignment quality"
        elif avg_quality > 0.3:
            overall_status = "🟡 Fair alignment - consider parameter tuning"
        else:
            overall_status = "❌ Poor alignment - review input data and parameters"
        
        print(f"🏆 Overall Assessment: {overall_status}")
        print(f"📁 Verification images saved to: {verification_folder}")
    
    print("\n💡 Tips for improvement:")
    print("   • Low correlation: Try different feature detectors (SIFT, AKAZE)")
    print("   • High MSE: Adjust ratio threshold or minimum matches")
    print("   • Poor overall quality: Check input image overlap and quality")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Verify thermal-RGB image alignment quality")
    parser.add_argument(
        'output_folder',
        nargs='?',
        default='task_1_output_improved',
        help='Output folder containing aligned images (default: task_1_output_improved)'
    )
    
    args = parser.parse_args()
    
    print("🔍 THERMAL-RGB ALIGNMENT VERIFICATION")
    print("=" * 80)
    print(f"📁 Analyzing folder: {args.output_folder}")
    
    verify_all_alignments(args.output_folder)

if __name__ == "__main__":
    main()