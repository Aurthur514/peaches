import cv2
import numpy as np
import os
import shutil
from glob import glob

# --- Configuration ---
# Adjust these paths based on where you keep your raw data
INPUT_FOLDER = "input_images"   # Folder containing your original _Z.JPG and _T.JPG pairs
OUTPUT_FOLDER = "task_1_output" # The required submission folder [cite: 60]

def align_images(img_rgb, img_thermal):
    """
    Aligns the thermal image to the RGB image using ORB feature matching 
    and Homography to correct perspective and aspect ratio.
    """
    # 1. Convert to grayscale
    gray_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
    gray_thermal = cv2.cvtColor(img_thermal, cv2.COLOR_BGR2GRAY)

    # 2. Detect ORB features (Increase max_features for better accuracy on complex scenes like towers)
    orb = cv2.ORB_create(max_features=10000)
    keypoints1, descriptors1 = orb.detectAndCompute(gray_rgb, None)
    keypoints2, descriptors2 = orb.detectAndCompute(gray_thermal, None)

    # 3. Match features using Hamming distance
    matcher = cv2.DescriptorMatcher_create(cv2.DESCRIPTOR_MATCHER_BRUTEFORCE_HAMMING)
    matches = matcher.match(descriptors1, descriptors2, None)

    # 4. Sort matches by score (lower distance is better)
    matches.sort(key=lambda x: x.distance, reverse=False)
    
    # Keep top 15% of matches to reduce noise
    keep_percent = 0.15
    num_good_matches = int(len(matches) * keep_percent)
    good_matches = matches[:num_good_matches]

    # Need at least 4 points to find Homography
    if len(good_matches) < 4:
        print("  ! Not enough matches found. Outputting original thermal image.")
        return img_thermal

    # 5. Extract location of good matches
    points_rgb = np.zeros((len(good_matches), 2), dtype=np.float32)
    points_thermal = np.zeros((len(good_matches), 2), dtype=np.float32)

    for i, match in enumerate(good_matches):
        points_rgb[i, :] = keypoints1[match.queryIdx].pt
        points_thermal[i, :] = keypoints2[match.trainIdx].pt

    # 6. Find Homography
    # RANSAC is crucial here to ignore outliers (mismatched points)
    h, mask = cv2.findHomography(points_thermal, points_rgb, cv2.RANSAC, 5.0)

    # 7. Warp Thermal image to match RGB perspective
    height, width, channels = img_rgb.shape
    aligned_thermal = cv2.warpPerspective(img_thermal, h, (width, height))

    return aligned_thermal

def main():
    # Ensure output directory exists
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    # Get all RGB images [cite: 17]
    rgb_files = glob(os.path.join(INPUT_FOLDER, "*_Z.JPG"))
    print(f"Found {len(rgb_files)} image pairs to process in '{INPUT_FOLDER}'...")

    for rgb_path in rgb_files:
        # Construct filename for Thermal (_T) and Output (_AT)
        base_name = os.path.basename(rgb_path)
        thermal_path = rgb_path.replace("_Z.JPG", "_T.JPG") # [cite: 16]
        output_at_name = base_name.replace("_Z.JPG", "_AT.JPG") # [cite: 62]
        output_at_path = os.path.join(OUTPUT_FOLDER, output_at_name)
        output_z_path = os.path.join(OUTPUT_FOLDER, base_name)

        if not os.path.exists(thermal_path):
            print(f"Skipping {base_name}: Thermal pair not found.")
            continue

        print(f"Processing: {base_name}...")

        # Load Images
        img_rgb = cv2.imread(rgb_path)
        img_thermal = cv2.imread(thermal_path)

        try:
            # Run Alignment
            aligned_img = align_images(img_rgb, img_thermal)

            # Save Adjusted Thermal Image (_AT.JPG) [cite: 62]
            cv2.imwrite(output_at_path, aligned_img)

            # Copy the original RGB Image (_Z.JPG) to output folder as required [cite: 61]
            shutil.copy2(rgb_path, output_z_path)

        except Exception as e:
            print(f"  ! Error processing {base_name}: {e}")

    print(f"\nTask 1 Complete. Files saved to '{OUTPUT_FOLDER}'.")
    print("Note: Check 'task_1_output' to ensure _T.JPG files are NOT present, as per submission guidelines.")

if __name__ == "__main__":
    main()