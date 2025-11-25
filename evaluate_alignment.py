import os
import cv2
import numpy as np
import csv
from math import isnan

try:
    from skimage.metrics import structural_similarity as ssim
    HAVE_SSIM = True
except Exception:
    HAVE_SSIM = False

OUTPUT_DIR = os.path.join(os.getcwd(), 'task_1_output')
SAMPLE_DIR = os.path.join(os.getcwd(), 'sample-output')
os.makedirs(SAMPLE_DIR, exist_ok=True)

pairs = []
for fname in os.listdir(OUTPUT_DIR):
    if fname.endswith('_AT.JPG') or fname.endswith('_AT.jpg'):
        prefix = fname[:-7]
        at_path = os.path.join(OUTPUT_DIR, fname)
        z_name = prefix + '_Z.JPG'
        z_path = os.path.join(OUTPUT_DIR, z_name)
        if os.path.exists(z_path):
            pairs.append((prefix, at_path, z_path))

report_rows = []
for prefix, at_path, z_path in pairs:
    a = cv2.imdecode(np.fromfile(at_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    z = cv2.imdecode(np.fromfile(z_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if a is None or z is None:
        continue
    # Resize if needed to exact same shape
    if a.shape != z.shape:
        z_resized = cv2.resize(z, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_LINEAR)
    else:
        z_resized = z
    # Convert to grayscale for comparison
    a_gray = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
    z_gray = cv2.cvtColor(z_resized, cv2.COLOR_BGR2GRAY)
    # Compute MSE
    mse = float(np.mean((a_gray.astype(np.float32) - z_gray.astype(np.float32))**2))
    # NCC (Pearson correlation)
    a_flat = a_gray.flatten().astype(np.float32)
    z_flat = z_gray.flatten().astype(np.float32)
    # normalize
    if np.std(a_flat) == 0 or np.std(z_flat) == 0:
        ncc = float('nan')
    else:
        ncc = float(np.corrcoef(a_flat, z_flat)[0,1])
    # SSIM if available
    s = None
    if HAVE_SSIM:
        try:
            s = float(ssim(a_gray, z_gray, data_range=255))
        except Exception:
            s = None
    # Save diff heatmap
    diff = cv2.absdiff(a_gray, z_gray)
    norm = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    heat = cv2.applyColorMap(norm, cv2.COLORMAP_JET)
    heat_path = os.path.join(SAMPLE_DIR, f"{prefix}_DIFF.JPG")
    _, enc = cv2.imencode('.jpg', heat, [int(cv2.IMWRITE_JPEG_QUALITY),90])
    enc.tofile(heat_path)

    report_rows.append({'prefix': prefix, 'mse': mse, 'ncc': ncc, 'ssim': s, 'diff_path': heat_path})

# Write CSV
csv_path = os.path.join(SAMPLE_DIR, 'alignment_report.csv')
with open(csv_path, 'w', newline='') as csvfile:
    fieldnames = ['prefix','mse','ncc','ssim','diff_path']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for r in report_rows:
        writer.writerow({k: ('' if v is None else v) for k,v in r.items()})

print(f"Evaluated {len(report_rows)} pairs. Report saved to {csv_path} and diffs to {SAMPLE_DIR}.")
if not HAVE_SSIM:
    print('Note: skimage SSIM not available; install scikit-image to enable SSIM metric.')
