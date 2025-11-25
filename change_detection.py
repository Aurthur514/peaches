import os
import cv2
import numpy as np
import csv

"""
change_detection.py

Detect missing objects between aligned before/after pairs:
- Before: X.jpg
- After:  X~2.jpg

Outputs:
- Annotated images saved to ./task_2_output (default)
- Per-pair CSV rows listing bounding boxes/polygon coordinates

Usage:
    python change_detection.py --input_dir ./input-images --output_dir ./task_2_output

"""

import argparse

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}


def is_image_file(fname):
    return os.path.splitext(fname)[1].lower() in IMAGE_EXTS


def find_pairs(input_dir):
    # map base name without suffix to paths
    files = [f for f in os.listdir(input_dir) if is_image_file(f)]
    before = {}
    after = {}
    for f in files:
        name, ext = os.path.splitext(f)
        if name.endswith('~2'):
            base = name[:-2]
            after[base] = os.path.join(input_dir, f)
        else:
            base = name
            before[base] = os.path.join(input_dir, f)
    # build pairs where both exist
    pairs = []
    for base, bpath in before.items():
        if base in after:
            pairs.append((base, bpath, after[base]))
    return pairs


def detect_changes(before_img, after_img, min_area=200, debug=False):
    # Convert to grayscale
    b = cv2.cvtColor(before_img, cv2.COLOR_BGR2GRAY) if len(before_img.shape) == 3 else before_img.copy()
    a = cv2.cvtColor(after_img, cv2.COLOR_BGR2GRAY) if len(after_img.shape) == 3 else after_img.copy()

    # Ensure same size
    if b.shape != a.shape:
        a = cv2.resize(a, (b.shape[1], b.shape[0]), interpolation=cv2.INTER_LINEAR)

    # Compute difference focusing on things present in before but missing in after
    diff = cv2.subtract(b, a)  # positive where before > after (possibly removed items or darker in after)

    # Blur to reduce noise
    diff_blur = cv2.GaussianBlur(diff, (5,5), 0)

    # Adaptive threshold or Otsu
    _, th = cv2.threshold(diff_blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Morphological cleaning
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
    th = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel, iterations=1)
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Find contours
    contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    regions = []
    mask = np.zeros_like(th)
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        # approximate polygon
        eps = 0.01 * cv2.arcLength(cnt, True)
        poly = cv2.approxPolyDP(cnt, eps, True)
        x,y,w,h = cv2.boundingRect(poly)
        regions.append({'poly': poly.reshape(-1,2).tolist(), 'bbox': (int(x),int(y),int(w),int(h)), 'area': float(area)})
        cv2.drawContours(mask, [poly], -1, 255, -1)

    return th, mask, regions


def annotate_and_save(after_img, regions, out_path, mask=None):
    vis = after_img.copy()
    for r in regions:
        poly = np.array(r['poly'], dtype=np.int32)
        cv2.polylines(vis, [poly], True, (0,0,255), 3)  # red polygon
        x,y,w,h = r['bbox']
        cv2.rectangle(vis, (x,y), (x+w, y+h), (0,255,0), 2)  # green bbox
    # overlay mask if provided
    if mask is not None:
        colored = cv2.applyColorMap(mask, cv2.COLORMAP_JET)
        vis = cv2.addWeighted(vis, 0.8, colored, 0.4, 0)
    # save with safe non-ascii
    _, enc = cv2.imencode('.jpg', vis, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    enc.tofile(out_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--input_dir', default=os.path.join(os.getcwd(),'input-images'))
    parser.add_argument('-o','--output_dir', default=os.path.join(os.getcwd(),'task_2_output'))
    parser.add_argument('--min_area', type=int, default=200)
    args = parser.parse_args()

    pairs = find_pairs(args.input_dir)
    os.makedirs(args.output_dir, exist_ok=True)

    report = []
    for base, before_p, after_p in pairs:
        print('Processing', base)
        bimg = cv2.imdecode(np.fromfile(before_p, dtype=np.uint8), cv2.IMREAD_COLOR)
        aimg = cv2.imdecode(np.fromfile(after_p, dtype=np.uint8), cv2.IMREAD_COLOR)
        if bimg is None or aimg is None:
            print('  failed to load')
            continue
        th, mask, regions = detect_changes(bimg, aimg, min_area=args.min_area)
        out_img = os.path.join(args.output_dir, f"{base}_CHANGES.JPG")
        out_mask = os.path.join(args.output_dir, f"{base}_MASK.JPG")
        annotate_and_save(aimg, regions, out_img, mask)
        _, enc = cv2.imencode('.jpg', mask, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        enc.tofile(out_mask)
        # record
        for r in regions:
            report.append({'prefix': base, 'bbox': r['bbox'], 'area': r['area']})
        if not regions:
            report.append({'prefix': base, 'bbox': '', 'area': 0})

    # write CSV
    csv_path = os.path.join(args.output_dir, 'change_report.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['prefix','bbox','area'])
        writer.writeheader()
        for row in report:
            writer.writerow(row)
    print('Done. Outputs in', args.output_dir)

if __name__ == '__main__':
    main()
