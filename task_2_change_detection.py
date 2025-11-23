"""
Task 2 - Change Detection

Find pairs named `X.jpg` and `X~2.jpg` in the input directory and detect missing
objects (present in `X.jpg` but missing in `X~2.jpg`). Saves annotated images,
binary masks, and a CSV report to the output directory.

Usage:
  python task_2_change_detection.py --input_dir ./input-images --output_dir ./task_2_output

The script focuses on "missing" objects by computing `before - after` differences.
"""
import argparse
import os
import re
import csv
import json
from pathlib import Path

import cv2
import numpy as np

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp'}


def find_pairs(input_dir):
    """Return list of (prefix, before_path, after_path) for files named X.jpg and X~2.jpg."""
    input_dir = Path(input_dir)
    files = [p for p in input_dir.iterdir() if p.is_file()]
    # map lowercase name -> path
    name_map = {p.name: p for p in files}
    pairs = []

    # Strategy: look for any "before" candidate and an "after" with '~2', '-2' or '_2' inserted
    for p in files:
        name = p.name
        if any(s in name.lower() for s in ('~2', '-2', '_2')):
            # skip files that look like after files in this pass
            continue
        stem = p.stem  # name without extension
        ext = p.suffix

        # Build expected after filename by inserting common suffixes before the extension
        after_candidates = [f"{stem}~2{ext}", f"{stem}-2{ext}", f"{stem}_2{ext}"]
        # Try exact match first (same extension)
        matched = False
        for after_name in after_candidates:
            if after_name in name_map:
                pairs.append((stem, str(name_map[name]), str(name_map[after_name])))
                matched = True
                break
        if matched:
            continue

        # Try different case (filesystem insensitive) and other typical extensions
        found = False
        for e in IMAGE_EXTS:
            candidate = f"{stem}~2{e}"
            if candidate in name_map:
                pairs.append((stem, str(name_map[name]), str(name_map[candidate])))
                found = True
                break
        if found:
            continue

        # If no after found for this before file, also check the reverse: maybe only after present
    # Also allow listing where after files exist but before files don't match the simple stem rule
    # (covers cases where user placed ~2 files without the before). We perform a secondary pass
        # also try matching other common after patterns
    pattern = re.compile(r'^(.+?)(?:~2|-2|_2)(\.[^.]+)$', re.IGNORECASE)
    for fname, after_path in name_map.items():
        m = pattern.match(fname)
        if not m:
            continue
        base = m.group(1)
        ext = m.group(2)
        before_candidates = []
        for e in IMAGE_EXTS:
            candidate = f"{base}{e}"
            if candidate in name_map:
                before_candidates.append(name_map[candidate])
        if before_candidates:
            before_path = before_candidates[0]
            prefix = base
            pairs.append((prefix, str(before_path), str(after_path)))

    # Deduplicate by prefix
    seen = set()
    unique = []
    for pref, b, a in pairs:
        if pref in seen:
            continue
        seen.add(pref)
        unique.append((pref, b, a))
    return unique


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def process_pair(prefix, before_path, after_path, out_dir, min_area=500, debug=False):
    out_dir = Path(out_dir)
    before = cv2.imdecode(np.fromfile(before_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    after = cv2.imdecode(np.fromfile(after_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if before is None or after is None:
        raise ValueError(f"Failed to read pair: {before_path}, {after_path}")

    # Normalize sizes: resize after to match before if necessary
    if before.shape[:2] != after.shape[:2]:
        after = cv2.resize(after, (before.shape[1], before.shape[0]), interpolation=cv2.INTER_LINEAR)

    before_gray = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
    after_gray = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)

    # Equalize histograms a bit to reduce global exposure differences
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    before_eq = clahe.apply(before_gray)
    after_eq = clahe.apply(after_gray)

    # Compute difference that highlights things present in before but missing in after
    diff = cv2.subtract(before_eq, after_eq)

    # Smooth and threshold (use Otsu to adapt)
    blur = cv2.GaussianBlur(diff, (5, 5), 0)
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Morphological clean-up
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    opened = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel, iterations=1)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Find contours
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    mask = np.zeros_like(closed)
    detections = []
    total_area = 0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.drawContours(mask, [cnt], -1, 255, -1)
        detections.append({'bbox': [int(x), int(y), int(w), int(h)], 'area': float(area)})
        total_area += area

    # Prepare annotated visualization (draw detections on after image)
    annotated = after.copy()
    # create a colored overlay for semi-transparent fills
    overlay = annotated.copy()
    color_fill = (0, 0, 255)  # red for missing objects
    for i, d in enumerate(detections, 1):
        x, y, w, h = d['bbox']
        # extract the contour area from mask to get polygon points
        # contour retrieval again to find matching contour by bbox
        # find contours that intersect bbox
        pts = None
        for cnt in contours:
            cx, cy, cw, ch = cv2.boundingRect(cnt)
            if cx == x and cy == y and cw == w and ch == h:
                pts = cnt
                break
        if pts is None:
            # fallback to rectangle if contour not found
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color_fill, 2)
            cv2.putText(annotated, f"#{i}", (x, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_fill, 2)
            continue

        # approximate polygon for nicer annotation
        epsilon = 0.01 * cv2.arcLength(pts, True)
        poly = cv2.approxPolyDP(pts, epsilon, True)
        # draw polygon outline on annotated
        cv2.polylines(annotated, [poly], True, color_fill, 2)
        # draw index label near polygon centroid
        M = cv2.moments(pts)
        if M['m00'] != 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
        else:
            cx, cy = x + 5, y + 5
        cv2.putText(annotated, f"#{i}", (cx, cy - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_fill, 2)
        # fill polygon on overlay
        cv2.drawContours(overlay, [poly], -1, color_fill, -1)
        # update detection with polygon coordinates
        poly_pts = poly.reshape(-1, 2).tolist()
        d['polygon'] = poly_pts

    # blend overlay with annotated (semi-transparent fill)
    annotated = cv2.addWeighted(annotated, 1.0, overlay, 0.4, 0)

    # Save outputs
    ensure_dir(out_dir)
    annotated_path = out_dir / f"{prefix}_CHANGES.JPG"
    mask_path = out_dir / f"{prefix}_MASK.PNG"

    # cv2.imwrite won't handle unicode or long Windows paths reliably; use imencode + tofile
    cv2.imencode('.jpg', annotated)[1].tofile(str(annotated_path))
    cv2.imencode('.png', mask)[1].tofile(str(mask_path))

    result = {
        'prefix': prefix,
        'before': before_path,
        'after': after_path,
        'num_changes': len(detections),
        'total_area': float(total_area),
        'detections': detections,
        'annotated': str(annotated_path),
        'mask': str(mask_path)
    }

    if debug:
        # also save the raw diff visualization and threshold
        diff_vis = cv2.applyColorMap(cv2.equalizeHist(diff), cv2.COLORMAP_JET)
        diff_path = out_dir / f"{prefix}_DIFF.JPG"
        th_path = out_dir / f"{prefix}_THRESH.JPG"
        cv2.imencode('.jpg', diff_vis)[1].tofile(str(diff_path))
        cv2.imencode('.jpg', closed)[1].tofile(str(th_path))
        result['diff_vis'] = str(diff_path)
        result['thresh'] = str(th_path)

    return result


def write_report(results, out_dir):
    out_dir = Path(out_dir)
    csv_path = out_dir / 'change_report.csv'
    fieldnames = ['prefix', 'before', 'after', 'num_changes', 'total_area', 'detections', 'annotated', 'mask']
    with open(csv_path, 'w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            row = {k: r.get(k, '') for k in fieldnames}
            row['detections'] = json.dumps(r.get('detections', []))
            writer.writerow(row)
    return str(csv_path)


def main():
    parser = argparse.ArgumentParser(description='Task 2 - Change Detection between X.jpg and X~2.jpg')
    parser.add_argument('--input_dir', type=str, default='./input-images', help='Input directory containing before/after image pairs')
    parser.add_argument('--output_dir', type=str, default='./task_2_output', help='Output directory to save results')
    parser.add_argument('--min_area', type=int, default=500, help='Minimum contour area (px) to consider a change')
    parser.add_argument('--debug', action='store_true', help='Save additional debug images (diff/threshold)')
    args = parser.parse_args()

    pairs = find_pairs(args.input_dir)
    if not pairs:
        print(f"No X~2 pairs found in {args.input_dir}. Looked for patterns like 'X~2.jpg'.")
        return

    ensure_dir(args.output_dir)
    results = []
    for prefix, before_path, after_path in pairs:
        try:
            print(f"Processing {prefix}...")
            res = process_pair(prefix, before_path, after_path, args.output_dir, min_area=args.min_area, debug=args.debug)
            results.append(res)
        except Exception as e:
            print(f"ERROR processing {prefix}: {e}")

    csv_path = write_report(results, args.output_dir)
    print(f"Done. Results: {len(results)} pairs processed. Report saved to {csv_path}")


if __name__ == '__main__':
    main()
