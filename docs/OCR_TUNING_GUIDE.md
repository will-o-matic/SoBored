# Advanced OCR Text Extraction Tuning Guide

This guide helps you optimize text extraction from event flyers and images in the SoBored system using advanced preprocessing techniques.

## 📋 Quick Start Checklist

### ✅ **Test Current Performance**
```bash
# Test with advanced preprocessing (default)
python tune_ocr.py --image ./your_image.jpg

# Compare all preprocessing strategies
python tune_ocr.py --compare-all ./your_image.jpg

# Multi-strategy approach (automatic best selection)
python tune_ocr.py --multi-strategy ./your_image.jpg

# Interactive testing mode
python tune_ocr.py --interactive --image ./your_image.jpg
```

### 🎯 **Performance Targets**
- **OCR Confidence**: Target >80% for reliable extraction
- **Quality Score**: Target >0.6 for good results
- **Text Length**: Minimum 10 words for meaningful content
- **Processing Time**: <5 seconds for advanced preprocessing

---

## 🔬 Advanced Preprocessing Strategies

The system now includes 5 preprocessing strategies, each optimized for different image types:

### **1. Basic Preprocessing** (`basic`)
- Simple resize and contrast enhancement
- Fastest processing
- Good for high-quality, clear images

### **2. Advanced Preprocessing** (`advanced`) ⭐ **Default**
- CLAHE contrast enhancement
- Bilateral noise filtering
- Background removal
- Automatic deskewing
- Adaptive + Otsu binarization
- Morphological text cleanup

### **3. High Contrast** (`high_contrast`)
- Extreme contrast enhancement (2x)
- Image sharpening
- Auto-level adjustment
- Best for faded or low-contrast images

### **4. Text Focused** (`text_focused`)
- Larger resize for text clarity (1400px)
- Unsharp masking
- Adaptive thresholding optimized for text
- Morphological text connection

### **5. Poster Optimized** (`poster_optimized`)
- LAB color space processing
- Aggressive background removal
- Designed for complex backgrounds with gradients
- Otsu binarization

## 🔧 Advanced Configuration Features

### **Multi-Strategy Testing**
The system automatically tests all strategies and selects the best result:

```python
# Quality score combines multiple factors:
# - OCR confidence (primary)
# - Word count bonus
# - Event-specific keywords
# - Readability patterns
# - Text length validation
```

### **Automatic Image Analysis**
- **Deskewing**: Automatically detects and corrects text rotation
- **Background Removal**: Separates text from complex backgrounds
- **Noise Filtering**: Bilateral filter removes noise while preserving edges
- **Binarization**: Combines adaptive and Otsu methods for optimal results

## 🛠️ Tesseract Configuration

Optimized settings for event flyers:

```python
tesseract_config = '--oem 1 --psm 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,&@:/-() '
```

**Parameters:**
- `--oem 1`: LSTM neural engine (most accurate)
- `--psm 3`: Fully automatic page segmentation
- Character whitelist: Optimized for event text
```

**Advanced Configuration Options:**

```python
# Custom Tesseract config for better event flyer recognition
custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,!?@:/-() '

# Usage in OCR tool
extracted_text = pytesseract.image_to_string(
    processed_image, 
    lang='eng',
    config=custom_config
)
```

#### **Page Segmentation Modes (PSM)**

| PSM | Description | Best For |
|-----|-------------|----------|
| 3 | Fully automatic page segmentation (default) | Mixed content |
| 6 | Uniform block of text | Event flyers with clear text blocks |
| 7 | Single text line | Banner-style event titles |
| 8 | Single word | Logo text extraction |
| 11 | Sparse text | Minimal text on busy backgrounds |
| 13 | Raw line (no layout analysis) | Simple text extraction |

#### **OCR Engine Modes (OEM)**

| OEM | Description | Performance |
|-----|-------------|-------------|
| 0 | Legacy engine only | Fast, lower accuracy |
| 1 | Neural nets LSTM engine only | Slower, higher accuracy |
| 2 | Legacy + LSTM engines | Balanced |
| 3 | Default (based on what's available) | Recommended |

---

## 🖼️ Image Quality Optimization

### **1. Ideal Image Characteristics**

**✅ Good for OCR:**
- **Resolution**: 300+ DPI, 1000+ pixels width
- **Contrast**: High contrast between text and background
- **Format**: PNG or high-quality JPEG
- **Orientation**: Upright, minimal rotation
- **Lighting**: Even lighting, no shadows
- **Focus**: Sharp, clear text

**❌ Challenging for OCR:**
- Low resolution (<600 pixels width)
- Low contrast (light text on light background)
- Heavy JPEG compression artifacts
- Rotated or skewed text
- Shadows, glare, or uneven lighting
- Blurry or out-of-focus text

### **2. Preprocessing Improvements**

#### **Current Implementation:**
```python
def _preprocess_image(image: Image.Image) -> Image.Image:
    # Convert to RGB
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize if too small
    width, height = image.size
    min_dimension = 800
    
    if width < min_dimension or height < min_dimension:
        scale_factor = min_dimension / min(width, height)
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    return image
```

#### **Enhanced Preprocessing Options:**

You can extend the preprocessing function with these improvements:

```python
def _preprocess_image_enhanced(image: Image.Image) -> Image.Image:
    """Enhanced preprocessing for better OCR results"""
    from PIL import ImageEnhance, ImageFilter
    
    # Convert to RGB first
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # 1. Resize for optimal OCR
    width, height = image.size
    target_width = 1200  # Increased for better accuracy
    
    if width < target_width:
        scale_factor = target_width / width
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # 2. Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.2)  # Increase contrast by 20%
    
    # 3. Sharpen image
    image = image.filter(ImageFilter.SHARPEN)
    
    # 4. Optional: Convert to grayscale for better OCR
    # image = image.convert('L')
    
    return image
```

---

## 📊 Monitoring OCR Performance

### **1. Built-in Metrics**

The system tracks these metrics automatically:

```python
# Check OCR statistics
processor = ImageProcessor()
stats = processor.get_ocr_stats()
print(stats)
```

**Key Metrics:**
- `ocr_success_rate`: Percentage of successful extractions
- `average_ocr_confidence`: Average confidence score
- `ocr_failure_rate`: Percentage of failed attempts

### **2. Quality Thresholds**

Current confidence thresholds in `validate_ocr_quality()`:

```python
min_confidence = 70.0  # Minimum for reliable extraction
```

**Recommended Thresholds by Use Case:**

| Use Case | Min Confidence | Action |
|----------|----------------|--------|
| Auto-save | 85% | Save automatically |
| Confirm first | 60-84% | Request user confirmation |
| Manual entry | <60% | Ask user to type details |

### **3. Quality Checks**

The system performs these quality validations:

```python
# Confidence check
if confidence >= min_confidence:
    quality_checks.append("high_confidence")

# Text length check  
if word_count >= 5:
    quality_checks.append("sufficient_text")

# Readable patterns check
if _has_readable_patterns(extracted_text):
    quality_checks.append("readable_patterns")
```

---

## 🔧 Configuration Tuning

### **1. Environment Variables**

Add these to your `.env` file for advanced tuning:

```bash
# OCR Configuration
OCR_MIN_CONFIDENCE=70
OCR_MIN_DIMENSION=800
OCR_TESSERACT_CONFIG="--oem 3 --psm 6"
OCR_ENABLE_PREPROCESSING=true
OCR_LANGUAGE=eng

# Image Processing
IMAGE_MAX_SIZE=2000
IMAGE_ENHANCE_CONTRAST=1.2
IMAGE_ENABLE_SHARPENING=true
```

### **2. Custom OCR Configuration**

Create a custom OCR configuration file `ocr_config.py`:

```python
# ocr_config.py
OCR_CONFIGS = {
    "event_flyers": {
        "psm": 6,  # Uniform block of text
        "oem": 3,  # Default engine
        "whitelist": "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,!?@:/-() ",
        "min_confidence": 75
    },
    "posters": {
        "psm": 3,  # Fully automatic
        "oem": 1,  # LSTM engine for better accuracy
        "min_confidence": 70
    },
    "business_cards": {
        "psm": 8,  # Single word
        "oem": 3,
        "min_confidence": 80
    }
}
```

### **3. Dynamic Tuning Based on Image Type**

```python
def get_optimal_ocr_config(image_path: str) -> dict:
    """Determine best OCR config based on image characteristics"""
    from PIL import Image
    
    img = Image.open(image_path)
    width, height = img.size
    aspect_ratio = width / height
    
    # Landscape event flyers
    if aspect_ratio > 1.3:
        return OCR_CONFIGS["event_flyers"]
    
    # Portrait posters
    elif aspect_ratio < 0.8:
        return OCR_CONFIGS["posters"]
    
    # Square or near-square
    else:
        return OCR_CONFIGS["event_flyers"]
```

---

## 🧪 Testing and Optimization

### **1. Test Image Collection**

Create a test suite with various image types:

```bash
mkdir test_images/
# Add these types:
# - event_flyers/ (landscape format)
# - posters/ (portrait format)  
# - business_cards/ (small text)
# - poor_quality/ (challenging images)
# - good_quality/ (reference images)
```

### **2. Batch Testing Script**

```python
# test_ocr_batch.py
import os
from pathlib import Path

def test_ocr_batch(image_dir: str):
    """Test OCR on multiple images and collect metrics"""
    results = []
    
    for image_path in Path(image_dir).glob("*.{jpg,jpeg,png}"):
        result = test_image_processing(str(image_path))
        results.append({
            "file": image_path.name,
            "confidence": result.get("confidence", 0),
            "word_count": result.get("word_count", 0),
            "success": result.get("success", False),
            "processing_time": result.get("processing_time", 0)
        })
    
    # Generate report
    avg_confidence = sum(r["confidence"] for r in results) / len(results)
    success_rate = sum(1 for r in results if r["success"]) / len(results) * 100
    
    print(f"Average Confidence: {avg_confidence:.1f}%")
    print(f"Success Rate: {success_rate:.1f}%")
    
    return results
```

### **3. A/B Testing Different Configurations**

```python
def compare_ocr_configs(image_path: str):
    """Compare different OCR configurations"""
    configs = [
        {"name": "Default", "psm": 3, "oem": 3},
        {"name": "Text Block", "psm": 6, "oem": 3},
        {"name": "High Accuracy", "psm": 6, "oem": 1},
    ]
    
    for config in configs:
        result = extract_with_config(image_path, config)
        print(f"{config['name']}: {result['confidence']:.1f}% confidence")
```

---

## 🎯 Common Issues and Solutions

### **Issue 1: Low Confidence Scores**

**Symptoms:**
- OCR confidence consistently <70%
- Poor text extraction quality

**Solutions:**
1. **Increase image resolution** - Scale up to 1200px width minimum
2. **Enhance contrast** - Apply contrast enhancement (1.2-1.5x)
3. **Try different PSM modes** - Test PSM 6 for event flyers
4. **Use LSTM engine** - Set OEM to 1 for better accuracy

### **Issue 2: Missing Text**

**Symptoms:**
- Some text not extracted
- Empty results on good images

**Solutions:**
1. **Check character whitelist** - Ensure all needed characters are included
2. **Adjust PSM mode** - Try PSM 3 for mixed content
3. **Improve preprocessing** - Add sharpening and noise reduction
4. **Check image orientation** - Ensure text is upright

### **Issue 3: Slow Processing**

**Symptoms:**
- OCR takes >5 seconds per image
- Timeout errors

**Solutions:**
1. **Reduce image size** - Don't exceed 2000px width
2. **Use faster PSM modes** - PSM 7 or 8 for simple layouts
3. **Optimize preprocessing** - Remove unnecessary enhancement steps
4. **Use legacy engine** - Set OEM to 0 for speed over accuracy

### **Issue 4: False Text Detection**

**Symptoms:**
- Random characters extracted
- Garbage text in results

**Solutions:**
1. **Stricter character whitelist** - Limit to alphanumeric + basic punctuation
2. **Higher confidence threshold** - Increase minimum to 80%
3. **Word pattern validation** - Check for readable English patterns
4. **Text length filtering** - Ignore single character extractions

---

## 📈 Performance Optimization Tips

### **1. Image Upload Guidelines for Users**

Provide these tips to users:

```markdown
📸 **For Best Results:**
- Use good lighting (avoid shadows)
- Hold camera steady (avoid blur)
- Fill the frame with the flyer
- Ensure text is upright
- Use high resolution (>1000px width)
- Avoid flash glare
```

### **2. Real-time Quality Feedback**

Implement client-side image quality checks:

```javascript
// Check image dimensions before upload
function validateImageQuality(file) {
    const img = new Image();
    img.onload = function() {
        if (this.width < 600) {
            alert("Image too small. Use higher resolution for better text extraction.");
        }
    };
    img.src = URL.createObjectURL(file);
}
```

### **3. Progressive Enhancement**

```python
def progressive_ocr_extraction(image_path: str):
    """Try multiple OCR strategies progressively"""
    
    # Strategy 1: Fast, basic extraction
    result = extract_with_config(image_path, {"psm": 6, "oem": 3})
    if result["confidence"] > 85:
        return result
    
    # Strategy 2: Enhanced preprocessing
    result = extract_with_preprocessing(image_path, enhance=True)
    if result["confidence"] > 75:
        return result
    
    # Strategy 3: High accuracy mode
    result = extract_with_config(image_path, {"psm": 6, "oem": 1})
    return result
```

---

## 🔍 Troubleshooting Commands

### **Quick Diagnostic Commands**

```bash
# Test OCR installation
tesseract --version

# Test with specific image
python test_image_processing.py ./problem_image.jpg --ocr-only --verbose

# Check current OCR stats
python -c "
from langgraph.pipeline.processors.image_processor import ImageProcessor
processor = ImageProcessor()
print(processor.get_ocr_stats())
"

# Test different configurations
python test_image_processing.py ./image.jpg --interactive
```

### **Debug OCR Issues**

```python
# Debug OCR extraction step by step
from langgraph.agents.tools.ocr_tool import extract_text_from_image, validate_ocr_quality

# 1. Test basic extraction
result = extract_text_from_image.invoke({"image_data": "./test.jpg"})
print("OCR Result:", result)

# 2. Test quality validation
validation = validate_ocr_quality.invoke({"ocr_result": result})
print("Quality Assessment:", validation)

# 3. Check preprocessing
from PIL import Image
img = Image.open("./test.jpg")
print(f"Original size: {img.size}")
print(f"Mode: {img.mode}")
```

---

## 📚 Advanced Resources

### **Tesseract Documentation**
- [Official Tesseract Guide](https://tesseract-ocr.github.io/)
- [PSM and OEM Options](https://github.com/tesseract-ocr/tesseract/blob/main/doc/tesseract.1.asc)

### **Image Preprocessing Libraries**
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [OpenCV for advanced preprocessing](https://opencv.org/)

### **OCR Best Practices**
- [Google's OCR Guidelines](https://cloud.google.com/vision/docs/ocr)
- [Azure OCR Best Practices](https://docs.microsoft.com/en-us/azure/cognitive-services/computer-vision/concept-recognizing-text)

---

*This guide is part of the SoBored image processing system. For technical support, see the main README.md file.*