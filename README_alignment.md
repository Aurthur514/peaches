# 🚁 Drone Image Alignment Tool

A robust Python application for aligning thermal and RGB images captured simultaneously from drone-mounted cameras with different Fields of View (FOV) and physical positions.

## 📋 Overview

This tool solves the perspective alignment problem between thermal and RGB cameras mounted on drones. Due to physical offset and different FOVs, thermal images don't naturally overlay on RGB images. The tool uses computer vision techniques to automatically detect features and apply perspective transformation for precise alignment.

## ✨ Features

- **Multi-Algorithm Support**: SIFT, ORB, and AKAZE feature detectors
- **Robust Matching**: Lowe's ratio test for reliable feature matching
- **Perspective Correction**: Homography-based transformation with RANSAC
- **Batch Processing**: Automatic processing of multiple image pairs
- **Error Handling**: Comprehensive error handling and logging
- **Flexible Configuration**: Adjustable parameters for different scenarios
- **Detailed Logging**: Complete processing statistics and debugging info

## 🚀 Quick Start

### Installation

1. **Clone or download the repository**
2. **Install dependencies**:
   ```bash
   pip install -r cv_requirements.txt
   ```
   Or manually:
   ```bash
   pip install opencv-python numpy pathlib2
   ```

### Basic Usage

```bash
python task_1_code.py input_folder [output_folder]
```

**Example**:
```bash
python task_1_code.py drone_images task_1_output
```

## 📂 Input Format

Organize your drone images in pairs with specific naming convention:

```
input_folder/
├── DJI_0001_T.JPG  # Thermal image
├── DJI_0001_Z.JPG  # RGB image (same position)
├── DJI_0002_T.JPG
├── DJI_0002_Z.JPG
├── DJI_0003_T.JPG
├── DJI_0003_Z.JPG
└── ...
```

**Naming Rules**:
- Thermal images: `[UNIQUE_ID]_T.JPG`
- RGB images: `[UNIQUE_ID]_Z.JPG`
- The `UNIQUE_ID` must match between paired images

## 📤 Output Format

The tool generates aligned images in the output folder:

```
task_1_output/
├── DJI_0001_AT.JPG # Aligned thermal image
├── DJI_0001_Z.JPG  # Original RGB image (copied)
├── DJI_0002_AT.JPG
├── DJI_0002_Z.JPG
└── ...
```

**Output Files**:
- `*_AT.JPG`: Aligned thermal images (transformed to RGB coordinate system)
- `*_Z.JPG`: Original RGB images (copied for reference)
- `image_alignment.log`: Detailed processing log

## ⚙️ Advanced Configuration

### Command Line Options

```bash
python task_1_code.py input_folder output_folder [OPTIONS]

OPTIONS:
  --detector {SIFT,ORB,AKAZE}  Feature detector algorithm (default: SIFT)
  --ratio FLOAT               Lowe's ratio test threshold (default: 0.75)
  --min-matches INT           Minimum matches for homography (default: 10)
  --verbose                   Enable detailed console logging
  --help                      Show help message
```

### Algorithm Selection Guide

| Algorithm | Speed | Accuracy | Best For |
|-----------|-------|----------|----------|
| **SIFT** (default) | Slow | Highest | Best quality, handles scale/rotation |
| **ORB** | Fast | Good | Real-time applications, limited computation |
| **AKAZE** | Medium | Very Good | Balanced performance, handles blur |

### Parameter Tuning

#### Match Ratio (`--ratio`)
- **0.5-0.7**: Strict matching, fewer false positives, may miss valid matches
- **0.7-0.9**: More permissive, more matches but less reliable
- **Default 0.75**: Good balance for most scenarios

#### Minimum Matches (`--min-matches`)
- **Higher values (15-20)**: More reliable transformation, may fail on sparse scenes
- **Lower values (5-10)**: Works with fewer features, less reliable transformation
- **Default 10**: Suitable for typical drone imagery

## 💡 Usage Examples

### Basic Processing
```bash
# Process with default settings
python task_1_code.py drone_images

# Custom output folder
python task_1_code.py drone_images aligned_results
```

### Algorithm Selection
```bash
# Use ORB for faster processing
python task_1_code.py drone_images output --detector ORB

# Use AKAZE for balanced performance
python task_1_code.py drone_images output --detector AKAZE
```

### Fine-tuning
```bash
# Strict matching for high-quality results
python task_1_code.py drone_images output --ratio 0.6 --min-matches 15

# Permissive matching for difficult scenes
python task_1_code.py drone_images output --ratio 0.8 --min-matches 8

# Enable verbose logging for debugging
python task_1_code.py drone_images output --verbose
```

## 🔧 Utility Scripts

### Check Input Structure
```bash
python usage_example.py --check your_input_folder
```

### Create Sample Structure
```bash
python usage_example.py --create-sample
```

### Run Tests
```bash
python test_alignment.py
```

## 🚨 Troubleshooting

### Common Issues

#### "Insufficient matches" Error
**Cause**: Not enough matching features found between images
**Solutions**:
- Try different detector: `--detector ORB` or `--detector AKAZE`
- Increase ratio threshold: `--ratio 0.85`
- Decrease minimum matches: `--min-matches 5`
- Verify images show overlapping scene content

#### "Homography computation failed" Error
**Cause**: Unable to compute valid transformation matrix
**Solutions**:
- Check image quality and overlap
- Try different feature detector
- Verify images are from same location/time

#### Poor Alignment Quality
**Solutions**:
- Use stricter matching: `--ratio 0.65`
- Increase minimum matches: `--min-matches 15`
- Use SIFT detector: `--detector SIFT`
- Check for sufficient scene overlap

### Performance Tips

1. **For Speed**: Use ORB detector with lower match requirements
2. **For Accuracy**: Use SIFT with higher match thresholds
3. **For Balance**: Use AKAZE with default settings
4. **Memory Issues**: Process smaller batches or reduce image resolution

## 📊 Algorithm Details

### Processing Pipeline

1. **Image Loading**: Load thermal (source) and RGB (target) image pairs
2. **Preprocessing**: 
   - Convert to grayscale
   - Apply histogram equalization (thermal)
   - Enhance contrast (RGB)
3. **Feature Detection**: Detect keypoints using selected algorithm
4. **Feature Matching**: Match features using nearest neighbor search
5. **Match Filtering**: Apply Lowe's ratio test to filter good matches
6. **Homography Estimation**: Compute transformation matrix using RANSAC
7. **Image Warping**: Apply perspective transformation to thermal image
8. **Output Generation**: Save aligned thermal image and copy RGB reference

### Technical Specifications

- **Input Formats**: JPG, JPEG (other formats supported by OpenCV)
- **Output Format**: JPG (preserves original quality)
- **Transformation**: Perspective transformation (homography)
- **Interpolation**: Cubic interpolation for smooth results
- **Border Handling**: Black padding where thermal doesn't cover RGB canvas

## 📈 Performance Metrics

The tool provides comprehensive statistics:

- **Processing Statistics**: Total processed, successful, failed
- **Match Quality**: Number of matches, inlier ratios
- **Error Analysis**: Categorized failure reasons
- **Processing Time**: Per-image and total processing time

## 🛠️ Development

### Project Structure
```
├── task_1_code.py          # Main alignment tool
├── usage_example.py        # Usage guide and utilities
├── test_alignment.py       # Test suite
├── cv_requirements.txt     # Dependencies
└── README.md              # This file
```

### Dependencies
- **OpenCV**: Computer vision operations
- **NumPy**: Numerical computations
- **pathlib2**: Path handling (compatibility)

## 📄 License

This project is provided as-is for educational and commercial use. Please ensure proper attribution when using or modifying the code.

## 🤝 Support

For technical support or feature requests:

1. Check the troubleshooting section above
2. Review the detailed logs in `image_alignment.log`
3. Test with the provided test suite
4. Verify input format compliance

## 🏆 Best Practices

1. **Image Quality**: Use high-quality images with clear features
2. **Scene Overlap**: Ensure significant overlap between thermal and RGB views
3. **Consistent Naming**: Follow the exact naming convention
4. **Batch Processing**: Process similar scenes together for consistency
5. **Parameter Tuning**: Adjust parameters based on your specific hardware setup
6. **Quality Control**: Review alignment results and adjust parameters as needed

---

**Happy Aligning!** 🎯