import os
import cv2
import numpy as np
from collections import defaultdict

ROOT = os.getcwd()
INPUT = os.path.join(ROOT, 'input_images')
OUT_DIR = os.path.join(ROOT, 'sample-output', 'matches')
os.makedirs(OUT_DIR, exist_ok=True)

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}

def is_image_file(fname):
    _, ext = os.path.splitext(fname)
    return ext.lower() in IMAGE_EXTS

# collect pairs with flexible timestamp matching similar to task_1_code
thermal_files = {}
rgb_files = {}
for fname in os.listdir(INPUT):
    if not is_image_file(fname):
        continue
    name, _ = os.path.splitext(fname)
    if name.lower().endswith('_t'):
        thermal_files[name[:-2]] = os.path.join(INPUT, fname)
    elif name.lower().endswith('_z'):
        rgb_files[name[:-2]] = os.path.join(INPUT, fname)

pairs = []
for t_prefix, t_path in thermal_files.items():
    # exact
    if t_prefix in rgb_files:
        pairs.append((t_prefix, t_path, rgb_files[t_prefix]))
        continue
    parts = t_prefix.split('_')
    if len(parts) >= 3:
        dji_prefix, timestamp, number = parts[0], parts[1], parts[2]
        best = None
        min_diff = float('inf')
        for r_prefix, r_path in rgb_files.items():
            r_parts = r_prefix.split('_')
            if len(r_parts) >= 3 and r_parts[0] == dji_prefix and r_parts[2] == number:
                try:
                    diff = abs(int(r_parts[1]) - int(timestamp))
                    if diff < min_diff and diff <= 10:
                        min_diff = diff
                        best = r_prefix
                except Exception:
                    continue
        if best:
            pairs.append((t_prefix, t_path, rgb_files[best]))

print(f"Found {len(pairs)} pairs to visualize")

# Create detector similar to task_1_code
try:
    detector = cv2.SIFT_create(nfeatures=10000, contrastThreshold=0.04, edgeThreshold=10)
    is_sift = True
except Exception:
    try:
        detector = cv2.ORB_create(nfeatures=10000)
        is_sift = False
    except Exception:
        detector = cv2.AKAZE_create()
        is_sift = False

# BF matcher config
def make_bf(desc1):
    if desc1 is None:
        return None
    if desc1.dtype == np.uint8:
        return cv2.BFMatcher(cv2.NORM_HAMMING)
    else:
        return cv2.BFMatcher(cv2.NORM_L2)

for prefix, t_path, z_path in pairs:
    print('Vis:', prefix)
    t_img = cv2.imdecode(np.fromfile(t_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    z_img = cv2.imdecode(np.fromfile(z_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if t_img is None or z_img is None:
        continue
    # grayscale
    if len(t_img.shape) == 3 and t_img.shape[2] == 3:
        t_gray = cv2.cvtColor(t_img, cv2.COLOR_BGR2GRAY)
    elif len(t_img.shape) == 3 and t_img.shape[2] == 4:
        t_gray = cv2.cvtColor(t_img, cv2.COLOR_BGRA2GRAY)
    else:
        t_gray = t_img.copy() if len(t_img.shape) == 2 else cv2.cvtColor(t_img, cv2.COLOR_BGR2GRAY)
    z_gray = cv2.cvtColor(z_img, cv2.COLOR_BGR2GRAY)

    # detect
    kp1, des1 = detector.detectAndCompute(t_gray, None)
    kp2, des2 = detector.detectAndCompute(z_gray, None)
    if des1 is None or des2 is None:
        print('  no descriptors')
        continue
    bf = make_bf(des1)
    if bf is None:
        continue
    # knn
    matches = bf.knnMatch(des1, des2, k=2)
    good = []
    for m_n in matches:
        if len(m_n) != 2:
            continue
        m, n = m_n
        if m.distance < 0.8 * n.distance:
            good.append(m)
    good_sorted = sorted(good, key=lambda x: x.distance)[:200]

    # draw top matches
    try:
        match_img = cv2.drawMatches(t_img if len(t_img.shape)==3 else cv2.cvtColor(t_img, cv2.COLOR_GRAY2BGR), kp1,
                                    z_img, kp2, good_sorted, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
        out_m = os.path.join(OUT_DIR, f"{prefix}_MATCHES.JPG")
        _, enc = cv2.imencode('.jpg', match_img, [int(cv2.IMWRITE_JPEG_QUALITY),90])
        enc.tofile(out_m)
    except Exception as e:
        print('  draw matches failed', e)

    # compute homography from good matches and draw inliers
    if len(good_sorted) >= 4:
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good_sorted]).reshape(-1,1,2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_sorted]).reshape(-1,1,2)
        H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        if H is not None and mask is not None:
            inlier_matches = [m for i,m in enumerate(good_sorted) if mask[i]]
            inlier_img = cv2.drawMatches(t_img if len(t_img.shape)==3 else cv2.cvtColor(t_img, cv2.COLOR_GRAY2BGR), kp1,
                                         z_img, kp2, inlier_matches, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
            out_i = os.path.join(OUT_DIR, f"{prefix}_INLIERS.JPG")
            try:
                _, enc = cv2.imencode('.jpg', inlier_img, [int(cv2.IMWRITE_JPEG_QUALITY),90])
                enc.tofile(out_i)
            except Exception as e:
                print('  save inliers failed', e)
    print('  saved', prefix)

print('Done.')
