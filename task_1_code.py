#!/usr/bin/env python3
"""
align_thermal_to_rgb.py

Align thermal images (suffix *_T.JPG) to RGB images (suffix *_Z.JPG) using feature
matching + homography (RANSAC). Saves aligned thermal images as *_AT.JPG in the
specified output folder.

Usage:
    python align_thermal_to_rgb.py --input_dir /path/to/input --output_dir /path/to/output
    python align_thermal_to_rgb.py -i ./pairs -o ./aligned --overlay   # also save visual overlay for inspection

Dependencies:
    - Python 3.8+
    - OpenCV (cv2) with contrib (for SIFT) recommended, but ORB fallback used automatically.
        pip install opencv-python opencv-contrib-python
    - numpy
"""

import os
import sys
import argparse
import cv2
import numpy as np
from collections import defaultdict

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}


def is_image_file(fname: str) -> bool:
    _, ext = os.path.splitext(fname)
    return ext.lower() in IMAGE_EXTS


def find_pairs(input_dir: str):
    """
    Scans input_dir and returns a dict mapping prefix -> {'T': thermal_path, 'Z': rgb_path}
    where the filenames follow the pattern <prefix>_T.<ext> and <prefix>_Z.<ext>.
    Handles timestamp variations in DJI filenames.
    """
    pairs = defaultdict(dict)
    thermal_files = {}
    rgb_files = {}
    
    # First pass: collect all thermal and RGB files
    for fname in os.listdir(input_dir):
        if not is_image_file(fname):
            continue
        name, ext = os.path.splitext(fname)
        
        if name.lower().endswith('_t'):
            prefix = name[:-2]
            thermal_files[prefix] = os.path.join(input_dir, fname)
        elif name.lower().endswith('_z'):
            prefix = name[:-2]
            rgb_files[prefix] = os.path.join(input_dir, fname)
    
    # Second pass: match thermal files with RGB files, handling timestamp variations
    for t_prefix, t_path in thermal_files.items():
        # Try exact match first
        if t_prefix in rgb_files:
            pairs[t_prefix]['T'] = t_path
            pairs[t_prefix]['Z'] = rgb_files[t_prefix]
            continue
        
        # For DJI files with timestamps, try flexible matching
        parts = t_prefix.split('_')
        if len(parts) >= 3:
            dji_prefix = parts[0]  # DJI
            timestamp = parts[1]   # YYYYMMDDHHMMSS
            number = parts[2]      # NNNN
            
            # Look for RGB with same prefix and number but different timestamp
            best_match = None
            min_time_diff = float('inf')
            
            for r_prefix in rgb_files:
                r_parts = r_prefix.split('_')
                if (len(r_parts) >= 3 and 
                    r_parts[0] == dji_prefix and 
                    r_parts[2] == number):
                    try:
                        time_diff = abs(int(r_parts[1]) - int(timestamp))
                        if time_diff < min_time_diff and time_diff <= 10:  # Allow up to 10 second difference
                            min_time_diff = time_diff
                            best_match = r_prefix
                    except ValueError:
                        continue
            
            if best_match:
                pairs[t_prefix]['T'] = t_path
                pairs[t_prefix]['Z'] = rgb_files[best_match]
    
    return pairs


def make_feature_detector():
    """
    Return (detector, is_sift) where detector is an OpenCV feature detector (SIFT preferred)
    and is_sift boolean indicates whether we are using SIFT (we will use appropriate matcher params).
    """
    # Try SIFT first with more features
    try:
        sift = cv2.SIFT_create(nfeatures=10000, contrastThreshold=0.04, edgeThreshold=10)
        return sift, True
    except Exception:
        # Fallback to ORB with many features for better matching
        try:
            orb = cv2.ORB_create(nfeatures=10000, scaleFactor=1.2, nlevels=8)
            return orb, False
        except Exception:
            akaze = cv2.AKAZE_create()
            return akaze, False


def match_features(desc1, desc2, is_sift):
    """
    Match descriptors using BFMatcher with more relaxed parameters for thermal-RGB matching.
    For SIFT / AKAZE (float descriptors) use cv2.NORM_L2 and ratio test.
    For ORB (binary) use cv2.NORM_HAMMING and ratio test.
    Returns list of good matches (after Lowe's ratio test).
    """
    if desc1 is None or desc2 is None:
        return []

    if is_sift:
        bf = cv2.BFMatcher(cv2.NORM_L2)
        ratio_threshold = 0.8  # More relaxed for thermal-RGB matching
    else:
        # ORB / AKAZE might produce uint8 descriptors — choose HAMMING for ORB, but AKAZE may be float
        # We'll check dtype
        norm_type = cv2.NORM_HAMMING if desc1.dtype == np.uint8 else cv2.NORM_L2
        bf = cv2.BFMatcher(norm_type)
        ratio_threshold = 0.85  # Even more relaxed for binary descriptors

    # knnMatch for ratio test
    try:
        matches = bf.knnMatch(desc1, desc2, k=2)
    except Exception:
        # If knnMatch fails, try basic matching
        try:
            basic_matches = bf.match(desc1, desc2)
            return sorted(basic_matches, key=lambda x: x.distance)[:50]  # Top 50 matches
        except Exception:
            return []

    good = []
    for m_n in matches:
        if len(m_n) != 2:
            continue
        m, n = m_n
        # More relaxed Lowe's ratio test for thermal-RGB pairs
        if m.distance < ratio_threshold * n.distance:
            good.append(m)
    return good


def warp_thermal_to_rgb(thermal_img, rgb_img, H):
    """
    Warps thermal_img into the coordinate frame of rgb_img using homography H.
    Will return the warped thermal image sized to rgb_img (same height/width).
    """
    h_rgb, w_rgb = rgb_img.shape[:2]
    warped = cv2.warpPerspective(thermal_img, H, (w_rgb, h_rgb), flags=cv2.INTER_LINEAR)
    return warped


def ensure_three_channels(img):
    """
    Ensure the image has 3 channels (BGR); if single-channel, convert to BGR.
    """
    if img is None:
        return None
    if len(img.shape) == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    if img.shape[2] == 1:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    return img


def apply_colormap_to_thermal(gray_thermal):
    """
    If thermal is single-channel, convert to colored heatmap for overlay visualization.
    Returns a 3-channel BGR colored image.
    """
    # normalize to 0..255 then apply colormap
    norm = cv2.normalize(gray_thermal, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    colored = cv2.applyColorMap(norm, cv2.COLORMAP_JET)
    return colored


def refine_with_ecc(warped_bgr, rgb_bgr, max_iters=2000, eps=1e-6):
    """Refine alignment using ECC (intensity-based) with an affine model.
    warped_bgr: warped thermal image (BGR)
    rgb_bgr: reference RGB image (BGR)
    Returns refined warped image (BGR)."""
    try:
        # Convert to grayscale
        warped_gray = cv2.cvtColor(ensure_three_channels(warped_bgr), cv2.COLOR_BGR2GRAY)
        rgb_gray = cv2.cvtColor(ensure_three_channels(rgb_bgr), cv2.COLOR_BGR2GRAY)

        # Resize rgb to warped if shapes mismatch
        if warped_gray.shape != rgb_gray.shape:
            rgb_gray = cv2.resize(rgb_gray, (warped_gray.shape[1], warped_gray.shape[0]), interpolation=cv2.INTER_LINEAR)

        # Convert to float32
        warped_f = warped_gray.astype(np.float32) / 255.0
        rgb_f = rgb_gray.astype(np.float32) / 255.0

        # Initial warp (affine 2x3)
        warp_matrix = np.eye(2, 3, dtype=np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, max_iters, eps)

        # Run ECC
        cc, warp_matrix = cv2.findTransformECC(rgb_f, warped_f, warp_matrix, cv2.MOTION_AFFINE, criteria, inputMask=None, gaussFiltSize=5)

        # Apply affine warp to the colored warped image
        h, w = warped_bgr.shape[:2]
        refined = cv2.warpAffine(warped_bgr, warp_matrix, (w, h), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
        return refined
    except Exception:
        return warped_bgr


def process_pair(prefix, thermal_path, rgb_path, output_dir, detector, is_sift, overlay=False):
    print(f"[{prefix}] Processing pair:")
    print(f"    Thermal: {thermal_path}")
    print(f"    RGB:     {rgb_path}")

    # Read images
    t_img = cv2.imdecode(np.fromfile(thermal_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    z_img = cv2.imdecode(np.fromfile(rgb_path, dtype=np.uint8), cv2.IMREAD_COLOR)

    if t_img is None:
        print(f"  ERROR: Could not read thermal image '{thermal_path}'. Skipping.")
        return

    if z_img is None:
        print(f"  ERROR: Could not read RGB image '{rgb_path}'. Skipping.")
        return

    # For feature detection convert to gray and enhance contrast
    # Note: thermal images may already be single-channel; convert safely.
    if len(t_img.shape) == 3 and t_img.shape[2] == 3:
        t_gray = cv2.cvtColor(t_img, cv2.COLOR_BGR2GRAY)
    elif len(t_img.shape) == 3 and t_img.shape[2] == 4:
        t_gray = cv2.cvtColor(t_img, cv2.COLOR_BGRA2GRAY)
    else:
        t_gray = t_img.copy() if len(t_img.shape) == 2 else cv2.cvtColor(t_img, cv2.COLOR_BGR2GRAY)

    z_gray = cv2.cvtColor(z_img, cv2.COLOR_BGR2GRAY)
    
    # Enhance contrast for better feature detection
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    t_gray = clahe.apply(t_gray)
    z_gray = clahe.apply(z_gray)

    # Detect keypoints and descriptors
    kp1, des1 = detector.detectAndCompute(t_gray, None)
    kp2, des2 = detector.detectAndCompute(z_gray, None)

    if not kp1 or not kp2:
        print(f"  WARNING: No keypoints detected in one of the images (thermal={len(kp1)} rgb={len(kp2)}). Skipping.")
        return

    # Match descriptors
    good_matches = match_features(des1, des2, is_sift)

    print(f"  Found {len(good_matches)} good matches.")

    # Need at least 4 good matches to compute homography, but try with fewer if necessary
    min_matches = 4
    if len(good_matches) < min_matches:
        print(f"  WARNING: Only {len(good_matches)} matches found. Trying alternative approach...")
        
        # Try with all available matches if we have at least 3
        if len(good_matches) >= 3:
            print(f"  Proceeding with {len(good_matches)} matches (minimum for homography)...")
        else:
            print("  ERROR: Not enough matches to compute homography. Need >=3. Skipping.")
            return

    # Extract matched keypoint coordinates
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)  # thermal points
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)  # rgb points

    # Compute homography using RANSAC with more relaxed parameters
    try:
        if len(good_matches) >= 4:
            H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0, maxIters=3000)
        else:
            # For 3 matches, use different method
            H, mask = cv2.findHomography(src_pts, dst_pts, cv2.LMEDS)
    except Exception as e:
        print(f"  ERROR: Homography computation failed: {e}. Skipping.")
        return
        
    if H is None:
        print("  ERROR: Homography computation failed. Skipping.")
        return

    inliers = int(mask.sum()) if mask is not None else 0
    print(f"  Homography found with {inliers} inliers out of {len(good_matches)} matches.")

    # Warp the *original* thermal image (not the grayscale) into RGB frame
    warped = warp_thermal_to_rgb(t_img, z_img, H)

    # Try ECC-based refinement (affine) to improve pixel-level alignment
    def ecc_refine(warped_img, ref_img, max_iters=2000, eps=1e-6):
        try:
            # Convert to gray and float32
            if len(warped_img.shape) == 3:
                warped_gray = cv2.cvtColor(warped_img, cv2.COLOR_BGR2GRAY)
            else:
                warped_gray = warped_img.copy()
            ref_gray = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)

            warped_f = warped_gray.astype(np.float32)
            ref_f = ref_gray.astype(np.float32)

            # Normalize to [0,1]
            warped_f = (warped_f - warped_f.min()) / (warped_f.max() - warped_f.min() + 1e-9)
            ref_f = (ref_f - ref_f.min()) / (ref_f.max() - ref_f.min() + 1e-9)

            # Initialize affine warp
            warp_matrix = np.eye(2, 3, dtype=np.float32)

            criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, max_iters, eps)
            cc, warp_matrix = cv2.findTransformECC(ref_f, warped_f, warp_matrix, cv2.MOTION_AFFINE, criteria, inputMask=None, gaussFiltSize=5)

            # Apply warp to the color warped image
            h, w = ref_img.shape[:2]
            refined = cv2.warpAffine(warped_img, warp_matrix, (w, h), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
            return refined, True
        except Exception:
            return warped_img, False

    refined_warped, refined_ok = ecc_refine(warped, z_img)
    if refined_ok:
        warped = refined_warped

    # Refine alignment with ECC (intensity-based) using an affine model
    refined = refine_with_ecc(warped, z_img)
    # Use refined image for saving and overlay
    warped = refined

    # Save the warped thermal image as <prefix>_AT.JPG
    out_filename = f"{prefix}_AT.JPG"
    out_path = os.path.join(output_dir, out_filename)

    # Ensure the image to save is 3-channel BGR for JPG compatibility
    warped_to_save = ensure_three_channels(warped)
    try:
        # Use imencode + tofile to safely support non-ascii paths on Windows
        ext = '.jpg'
        _, enc = cv2.imencode(ext, warped_to_save, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        enc.tofile(out_path)
        print(f"  Saved aligned thermal -> {out_path}")
    except Exception as e:
        print(f"  ERROR: Failed to save {out_path}: {e}")
        return

    # Also save the RGB image as <prefix>_Z.JPG for submission requirements
    rgb_filename = f"{prefix}_Z.JPG"
    rgb_out_path = os.path.join(output_dir, rgb_filename)
    try:
        _, enc_rgb = cv2.imencode('.jpg', z_img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        enc_rgb.tofile(rgb_out_path)
        print(f"  Saved RGB reference -> {rgb_out_path}")
    except Exception as e:
        print(f"  ERROR: Failed to save RGB {rgb_out_path}: {e}")

    # Optionally create and save an overlay for inspection
    if overlay:
        # If thermal is single-channel, make a color map of warped grayscale
        if len(warped.shape) == 2:
            colored_thermal = apply_colormap_to_thermal(warped)
        else:
            # If warped has color channels, convert to grayscale and then colorize to standardize overlay
            warped_gray = cv2.cvtColor(ensure_three_channels(warped), cv2.COLOR_BGR2GRAY)
            colored_thermal = apply_colormap_to_thermal(warped_gray)

        rgb_vis = ensure_three_channels(z_img)
        # Blend the two images
        blended = cv2.addWeighted(rgb_vis, 0.6, colored_thermal, 0.4, 0)
        overlay_path = os.path.join(output_dir, f"{prefix}_OV.JPG")
        try:
            _, enc2 = cv2.imencode('.jpg', blended, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            enc2.tofile(overlay_path)
            print(f"  Saved overlay visualization -> {overlay_path}")
        except Exception as e:
            print(f"  WARNING: Failed to save overlay {overlay_path}: {e}")
        # Also save overlay to top-level 'sample-output' folder for quick inspection (optional)
        try:
            sample_dir = os.path.join(os.getcwd(), 'sample-output')
            os.makedirs(sample_dir, exist_ok=True)
            sample_overlay = os.path.join(sample_dir, f"{prefix}_OV.JPG")
            _, enc3 = cv2.imencode('.jpg', blended, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            enc3.tofile(sample_overlay)
            print(f"  Also saved overlay -> {sample_overlay}")
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Align thermal images (_T) to RGB images (_Z) and save aligned thermal (_AT).")
    # Defaults chosen to match project expectations: input_images and task_1_output
    parser.add_argument("-i", "--input_dir", required=False, default=os.path.join(os.getcwd(), 'input_images'), help="Input folder containing *_T.* and *_Z.* pairs (default: ./input_images)")
    parser.add_argument("-o", "--output_dir", required=False, default=os.path.join(os.getcwd(), 'task_1_output'), help="Output folder for aligned thermal images (default: ./task_1_output)")
    parser.add_argument("--overlay", action="store_true", help="Also save a blended overlay (prefix_OV.JPG) for visual inspection")
    parser.add_argument("--min_matches", type=int, default=4, help="Minimum good matches required to compute homography (default 4)")
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir
    overlay = args.overlay

    if not os.path.isdir(input_dir):
        print(f"ERROR: Input folder '{input_dir}' not found or not a directory.")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    # Find pairs
    pairs = find_pairs(input_dir)
    if not pairs:
        print("No valid image files with suffixes '_T' or '_Z' found in input directory.")
        sys.exit(1)

    # Initialize detector
    detector, is_sift = make_feature_detector()
    detector_name = detector.__class__.__name__
    print(f"Using feature detector: {detector_name} (SIFT-like float descriptors? {'Yes' if is_sift else 'No'})")

    total = 0
    skipped = 0
    for prefix, d in pairs.items():
        if 'T' not in d or 'Z' not in d:
            # warn if missing counterpart
            missing = 'T' if 'T' not in d else 'Z'
            print(f"[{prefix}] WARNING: missing counterpart ({missing}). Skipping.")
            skipped += 1
            continue

        try:
            process_pair(prefix, d['T'], d['Z'], output_dir, detector, is_sift, overlay=overlay)
            total += 1
        except Exception as ex:
            print(f"[{prefix}] ERROR: Exception while processing: {ex}")
            skipped += 1

    print("----- Summary -----")
    print(f"Processed pairs: {total}")
    print(f"Skipped pairs:   {skipped}")
    print(f"Output folder:   {os.path.abspath(output_dir)}")


if __name__ == "__main__":
    main()
