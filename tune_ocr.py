#!/usr/bin/env python3
"""
Advanced OCR Tuning Script for SoBored Image Processing

Interactive tool for testing and optimizing OCR settings with advanced preprocessing.

Usage:
    python tune_ocr.py --image ./test_image.jpg
    python tune_ocr.py --multi-strategy ./test_image.jpg
    python tune_ocr.py --compare-all ./test_image.jpg
    python tune_ocr.py --interactive
    python tune_ocr.py --batch ./test_images/
"""

import os
import sys
import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Import OCR tools after path setup
from langgraph.agents.tools.ocr_tool import (
    extract_text_from_image, 
    extract_text_with_multiple_strategies,
    validate_ocr_quality
)

def test_advanced_ocr(image_path: str, strategy: str = "auto") -> Dict[str, Any]:
    """Test OCR with advanced preprocessing strategies"""
    try:
        print(f"\n🔍 Testing advanced OCR on: {image_path}")
        print(f"📋 Strategy: {strategy}")
        
        if strategy == "multi":
            # Use multi-strategy approach
            result = extract_text_with_multiple_strategies.invoke({
                "image_data": image_path, 
                "image_format": "file"
            })
            if result.get("success"):
                print(f"\n✅ Best strategy: {result['best_strategy']}")
                print(f"📊 Quality score: {result['quality_score']:.3f}")
                print(f"🎯 Confidence: {result['confidence']:.1f}%")
                print(f"📝 Word count: {result['word_count']}")
                print(f"\n📄 Extracted text:")
                print("-" * 50)
                print(result['extracted_text'])
                print("-" * 50)
                
                print(f"\n📈 All strategy results:")
                for res in result['all_results']:
                    print(f"  {res['strategy']:15} | Conf: {res['confidence']:5.1f}% | Words: {res['word_count']:3d} | Quality: {res['quality_score']:.3f}")
                
                return result
            else:
                print(f"❌ Multi-strategy OCR failed: {result.get('error')}")
                return result
        
        else:
            # Use single strategy
            use_advanced = strategy != "basic"
            result = extract_text_from_image.invoke({
                "image_data": image_path,
                "image_format": "file", 
                "use_advanced_preprocessing": use_advanced
            })
            
            if result.get("success"):
                print(f"🎯 Confidence: {result['confidence']:.1f}%")
                print(f"📝 Word count: {result['word_count']}")
                print(f"\n📄 Extracted text:")
                print("-" * 50)
                print(result['extracted_text'])
                print("-" * 50)
                
                # Validate quality
                validation = validate_ocr_quality.invoke({
                    "ocr_result": result,
                    "min_confidence": 70.0
                })
                print(f"\n🔍 Quality validation:")
                print(f"  Reliable: {validation['is_reliable']}")
                print(f"  Recommendation: {validation['recommendation']}")
                print(f"  Reason: {validation['reason']}")
                
                return result
            else:
                print(f"❌ OCR failed: {result.get('error')}")
                return result
                
    except Exception as e:
        error_result = {"success": False, "error": str(e)}
        print(f"❌ Error during OCR testing: {e}")
        return error_result

def compare_all_strategies(image_path: str) -> None:
    """Compare all available preprocessing strategies"""
    print(f"\n🔬 Comprehensive strategy comparison for: {image_path}")
    print("=" * 80)
    
    try:
        # Test multi-strategy
        result = extract_text_with_multiple_strategies.invoke({
            "image_data": image_path,
            "image_format": "file"
        })
        
        if not result.get("success"):
            print(f"❌ Failed to run comparison: {result.get('error')}")
            return
        
        # Display results table
        print(f"\n📊 Strategy Performance Comparison:")
        print(f"{'Strategy':<15} | {'Confidence':<10} | {'Words':<6} | {'Quality':<8} | {'Text Preview':<30}")
        print("-" * 85)
        
        for res in result['all_results']:
            preview = res['extracted_text'][:27] + "..." if len(res['extracted_text']) > 30 else res['extracted_text']
            preview = preview.replace('\n', ' ').replace('\r', ' ')
            print(f"{res['strategy']:<15} | {res['confidence']:>8.1f}% | {res['word_count']:>4d} | {res['quality_score']:>6.3f} | {preview}")
        
        print("-" * 85)
        print(f"🏆 Winner: {result['best_strategy']} (Quality: {result['quality_score']:.3f})")
        
        # Show full text of best result
        print(f"\n📄 Best result full text:")
        print("=" * 50)
        print(result['extracted_text'])
        print("=" * 50)
        
        # Analysis
        print(f"\n🔍 Analysis:")
        confidence_scores = [r['confidence'] for r in result['all_results']]
        quality_scores = [r['quality_score'] for r in result['all_results']]
        
        print(f"  Average confidence: {sum(confidence_scores)/len(confidence_scores):.1f}%")
        print(f"  Confidence range: {min(confidence_scores):.1f}% - {max(confidence_scores):.1f}%")
        print(f"  Average quality: {sum(quality_scores)/len(quality_scores):.3f}")
        print(f"  Quality range: {min(quality_scores):.3f} - {max(quality_scores):.3f}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if result['quality_score'] > 0.8:
            print("  ✅ Excellent OCR quality - text should be highly accurate")
        elif result['quality_score'] > 0.6:
            print("  ⚠️  Good OCR quality - minor errors possible")
        elif result['quality_score'] > 0.4:
            print("  ⚠️  Moderate OCR quality - manual review recommended")
        else:
            print("  ❌ Poor OCR quality - consider image quality improvements")
            
        if result['confidence'] < 70:
            print("  💡 Low confidence detected - try improving image resolution or contrast")
            
        if result['word_count'] < 5:
            print("  💡 Few words detected - verify image contains readable text")
        
    except Exception as e:
        print(f"❌ Error during comparison: {e}")

def test_ocr_config(image_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Test OCR with specific configuration (legacy function for compatibility)"""
    try:
        import pytesseract
        from PIL import Image, ImageEnhance, ImageFilter
        
        # Load and preprocess image
        img = Image.open(image_path)
        
        # Apply preprocessing based on config
        if config.get("resize", True):
            width, height = img.size
            target_width = config.get("target_width", 1000)
            if width < target_width:
                scale_factor = target_width / width
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        if config.get("enhance_contrast", False):
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(config.get("contrast_factor", 1.2))
        
        if config.get("sharpen", False):
            img = img.filter(ImageFilter.SHARPEN)
        
        if config.get("grayscale", False):
            img = img.convert('L')
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Build tesseract config string
        tesseract_config = f"--oem {config.get('oem', 3)} --psm {config.get('psm', 6)}"
        
        if config.get("whitelist"):
            tesseract_config += f" -c tessedit_char_whitelist={config['whitelist']}"
        
        # Extract text
        start_time = time.time()
        extracted_text = pytesseract.image_to_string(img, config=tesseract_config)
        extraction_time = time.time() - start_time
        
        # Get confidence data
        confidence_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config=tesseract_config)
        confidences = [int(conf) for conf in confidence_data['conf'] if int(conf) > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Clean text
        cleaned_text = ' '.join(extracted_text.split())
        word_count = len(cleaned_text.split())
        
        return {
            "success": True,
            "extracted_text": cleaned_text,
            "confidence": avg_confidence,
            "word_count": word_count,
            "char_count": len(cleaned_text),
            "extraction_time": extraction_time,
            "config_used": config
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "confidence": 0.0,
            "word_count": 0,
            "char_count": 0,
            "extraction_time": 0.0,
            "config_used": config
        }

def get_preset_configs() -> Dict[str, Dict[str, Any]]:
    """Get preset OCR configurations for testing"""
    return {
        "default": {
            "name": "Default Settings",
            "psm": 6,
            "oem": 3,
            "resize": True,
            "target_width": 1000,
            "enhance_contrast": False,
            "sharpen": False,
            "grayscale": False
        },
        "high_accuracy": {
            "name": "High Accuracy (Slow)",
            "psm": 6,
            "oem": 1,  # LSTM engine
            "resize": True,
            "target_width": 1200,
            "enhance_contrast": True,
            "contrast_factor": 1.3,
            "sharpen": True,
            "grayscale": False
        },
        "fast": {
            "name": "Fast Processing",
            "psm": 7,  # Single text line
            "oem": 0,  # Legacy engine
            "resize": True,
            "target_width": 800,
            "enhance_contrast": False,
            "sharpen": False,
            "grayscale": True
        },
        "event_flyer": {
            "name": "Event Flyer Optimized",
            "psm": 6,
            "oem": 3,
            "resize": True,
            "target_width": 1200,
            "enhance_contrast": True,
            "contrast_factor": 1.2,
            "sharpen": True,
            "grayscale": False,
            "whitelist": "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,!?@:/-() "
        },
        "poster": {
            "name": "Poster/Banner Optimized",
            "psm": 3,  # Fully automatic
            "oem": 3,
            "resize": True,
            "target_width": 1000,
            "enhance_contrast": True,
            "contrast_factor": 1.4,
            "sharpen": False,
            "grayscale": False
        },
        "minimal_text": {
            "name": "Minimal Text (Logos, etc.)",
            "psm": 8,  # Single word
            "oem": 3,
            "resize": True,
            "target_width": 1500,
            "enhance_contrast": True,
            "contrast_factor": 1.5,
            "sharpen": True,
            "grayscale": True
        }
    }

def compare_configs(image_path: str, configs: Dict[str, Dict]) -> List[Dict]:
    """Compare multiple OCR configurations on the same image"""
    results = []
    
    print(f"🔍 Testing OCR configurations on: {os.path.basename(image_path)}")
    print("=" * 60)
    
    for config_name, config in configs.items():
        print(f"Testing {config['name']}...")
        result = test_ocr_config(image_path, config)
        result["config_name"] = config_name
        results.append(result)
        
        if result["success"]:
            print(f"  ✅ Confidence: {result['confidence']:.1f}% | Words: {result['word_count']} | Time: {result['extraction_time']:.2f}s")
        else:
            print(f"  ❌ Failed: {result['error']}")
    
    # Sort by confidence
    results.sort(key=lambda x: x.get('confidence', 0), reverse=True)
    
    print("\n" + "=" * 60)
    print("🏆 RESULTS RANKING:")
    for i, result in enumerate(results, 1):
        if result["success"]:
            config_name = result["config_name"]
            config_display = configs[config_name]["name"]
            print(f"{i}. {config_display}: {result['confidence']:.1f}% confidence")
        else:
            print(f"{i}. {result['config_name']}: FAILED")
    
    return results

def interactive_tuning(image_path: str):
    """Interactive OCR tuning session"""
    print(f"🎯 Interactive OCR Tuning for: {os.path.basename(image_path)}")
    print("Type 'help' for commands, 'quit' to exit")
    
    # Start with default config
    current_config = get_preset_configs()["default"].copy()
    
    while True:
        try:
            command = input("\n> ").strip().lower()
            
            if command == 'quit' or command == 'exit':
                break
            elif command == 'help':
                print_help()
            elif command == 'test':
                result = test_ocr_config(image_path, current_config)
                display_result(result)
            elif command == 'show':
                print_config(current_config)
            elif command == 'presets':
                test_presets(image_path)
            elif command.startswith('set '):
                set_config_value(current_config, command)
            elif command == 'reset':
                current_config = get_preset_configs()["default"].copy()
                print("✅ Reset to default configuration")
            elif command.startswith('load '):
                preset_name = command.split(' ', 1)[1]
                if preset_name in get_preset_configs():
                    current_config = get_preset_configs()[preset_name].copy()
                    print(f"✅ Loaded preset: {current_config['name']}")
                else:
                    print(f"❌ Unknown preset: {preset_name}")
                    print("Available presets:", list(get_preset_configs().keys()))
            else:
                print("❌ Unknown command. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def print_help():
    """Print help for interactive mode"""
    help_text = """
🎯 Interactive OCR Tuning Commands:

📊 Testing:
  test          - Test current configuration
  presets       - Test all preset configurations
  show          - Show current configuration

⚙️ Configuration:
  set psm 6     - Set page segmentation mode (0-13)
  set oem 3     - Set OCR engine mode (0-3)
  set width 1200 - Set target width for resizing
  set contrast 1.3 - Set contrast enhancement factor
  set sharpen true - Enable/disable sharpening
  set grayscale false - Enable/disable grayscale conversion

📋 Presets:
  load default       - Load default settings
  load high_accuracy - Load high accuracy settings
  load fast         - Load fast processing settings
  load event_flyer  - Load event flyer optimized settings
  reset             - Reset to default configuration

🚪 Exit:
  quit, exit        - Exit interactive mode

📚 OCR Parameters:
  PSM (Page Segmentation Mode):
    3 = Fully automatic page segmentation (default)
    6 = Uniform block of text (good for flyers)
    7 = Single text line
    8 = Single word
   11 = Sparse text

  OEM (OCR Engine Mode):
    0 = Legacy engine (fast)
    1 = Neural nets LSTM engine (accurate)
    2 = Legacy + LSTM engines
    3 = Default, based on what's available
"""
    print(help_text)

def print_config(config: Dict[str, Any]):
    """Print current configuration"""
    print("\n📋 Current Configuration:")
    print(f"  Name: {config.get('name', 'Custom')}")
    print(f"  PSM (Page Segmentation): {config.get('psm', 6)}")
    print(f"  OEM (OCR Engine): {config.get('oem', 3)}")
    print(f"  Target Width: {config.get('target_width', 1000)}px")
    print(f"  Enhance Contrast: {config.get('enhance_contrast', False)}")
    if config.get('enhance_contrast'):
        print(f"    Contrast Factor: {config.get('contrast_factor', 1.2)}")
    print(f"  Sharpen: {config.get('sharpen', False)}")
    print(f"  Grayscale: {config.get('grayscale', False)}")
    if config.get('whitelist'):
        print(f"  Character Whitelist: {config.get('whitelist', 'None')[:50]}...")

def display_result(result: Dict[str, Any]):
    """Display OCR test result"""
    if result["success"]:
        print(f"\n✅ OCR Results:")
        print(f"  Confidence: {result['confidence']:.1f}%")
        print(f"  Words: {result['word_count']}")
        print(f"  Characters: {result['char_count']}")
        print(f"  Processing Time: {result['extraction_time']:.2f}s")
        print(f"  Extracted Text Preview:")
        text_preview = result['extracted_text'][:200]
        print(f"    \"{text_preview}{'...' if len(result['extracted_text']) > 200 else ''}\"")
    else:
        print(f"\n❌ OCR Failed: {result['error']}")

def set_config_value(config: Dict[str, Any], command: str):
    """Set configuration value from command"""
    try:
        parts = command.split()
        if len(parts) < 3:
            print("❌ Usage: set <parameter> <value>")
            return
        
        param = parts[1]
        value = parts[2]
        
        if param == 'psm':
            config['psm'] = int(value)
            print(f"✅ Set PSM to {value}")
        elif param == 'oem':
            config['oem'] = int(value)
            print(f"✅ Set OEM to {value}")
        elif param == 'width':
            config['target_width'] = int(value)
            print(f"✅ Set target width to {value}px")
        elif param == 'contrast':
            config['contrast_factor'] = float(value)
            config['enhance_contrast'] = True
            print(f"✅ Set contrast factor to {value}")
        elif param == 'sharpen':
            config['sharpen'] = value.lower() in ['true', '1', 'yes']
            print(f"✅ Set sharpen to {config['sharpen']}")
        elif param == 'grayscale':
            config['grayscale'] = value.lower() in ['true', '1', 'yes']
            print(f"✅ Set grayscale to {config['grayscale']}")
        else:
            print(f"❌ Unknown parameter: {param}")
            print("Available parameters: psm, oem, width, contrast, sharpen, grayscale")
    
    except ValueError as e:
        print(f"❌ Invalid value: {e}")

def test_presets(image_path: str):
    """Test all preset configurations"""
    presets = get_preset_configs()
    results = compare_configs(image_path, presets)
    
    print("\n📊 Detailed Results:")
    for result in results:
        if result["success"]:
            config_name = result["config_name"]
            config = presets[config_name]
            print(f"\n🔧 {config['name']}:")
            print(f"  Settings: PSM={config['psm']}, OEM={config['oem']}, Width={config.get('target_width', 1000)}")
            print(f"  Results: {result['confidence']:.1f}% confidence, {result['word_count']} words, {result['extraction_time']:.2f}s")
            if result['word_count'] > 0:
                text_preview = result['extracted_text'][:100]
                print(f"  Text: \"{text_preview}{'...' if len(result['extracted_text']) > 100 else ''}\"")

def batch_test(directory: str):
    """Test OCR on multiple images in a directory"""
    image_dir = Path(directory)
    if not image_dir.exists():
        print(f"❌ Directory not found: {directory}")
        return
    
    image_files = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.jpeg")) + list(image_dir.glob("*.png"))
    
    if not image_files:
        print(f"❌ No image files found in: {directory}")
        return
    
    print(f"🧪 Batch testing {len(image_files)} images with preset configurations")
    
    presets = get_preset_configs()
    all_results = []
    
    for image_path in image_files:
        print(f"\n📁 Testing: {image_path.name}")
        results = compare_configs(str(image_path), presets)
        
        # Find best result for this image
        best_result = max(results, key=lambda x: x.get('confidence', 0))
        if best_result["success"]:
            all_results.append({
                "image": image_path.name,
                "best_config": best_result["config_name"],
                "confidence": best_result["confidence"],
                "word_count": best_result["word_count"]
            })
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("📊 BATCH TEST SUMMARY")
    print("=" * 60)
    
    if all_results:
        avg_confidence = sum(r["confidence"] for r in all_results) / len(all_results)
        total_words = sum(r["word_count"] for r in all_results)
        
        print(f"Images tested: {len(all_results)}")
        print(f"Average confidence: {avg_confidence:.1f}%")
        print(f"Total words extracted: {total_words}")
        
        # Config usage summary
        config_counts = {}
        for result in all_results:
            config = result["best_config"]
            config_counts[config] = config_counts.get(config, 0) + 1
        
        print(f"\nBest configuration by usage:")
        for config, count in sorted(config_counts.items(), key=lambda x: x[1], reverse=True):
            config_name = presets[config]["name"]
            print(f"  {config_name}: {count} images ({count/len(all_results)*100:.1f}%)")

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Advanced OCR Tuning Tool for SoBored")
    parser.add_argument("--image", help="Path to test image")
    parser.add_argument("--multi-strategy", help="Test image with multi-strategy approach")
    parser.add_argument("--compare-all", help="Compare all preprocessing strategies")
    parser.add_argument("--strategy", choices=["basic", "advanced", "multi"], default="advanced", 
                       help="Preprocessing strategy to use")
    parser.add_argument("--interactive", action="store_true", help="Interactive tuning mode")
    parser.add_argument("--batch", help="Batch test directory")
    parser.add_argument("--presets-only", action="store_true", help="Test presets only")
    
    args = parser.parse_args()
    
    if args.multi_strategy:
        if not os.path.exists(args.multi_strategy):
            print(f"❌ Image file not found: {args.multi_strategy}")
            return
        test_advanced_ocr(args.multi_strategy, "multi")
        
    elif args.compare_all:
        if not os.path.exists(args.compare_all):
            print(f"❌ Image file not found: {args.compare_all}")
            return
        compare_all_strategies(args.compare_all)
        
    elif args.batch:
        batch_test(args.batch)
        
    elif args.interactive:
        if not args.image:
            print("❌ --image required for interactive mode")
            return
        if not os.path.exists(args.image):
            print(f"❌ Image file not found: {args.image}")
            return
        interactive_tuning(args.image)
        
    elif args.image:
        if not os.path.exists(args.image):
            print(f"❌ Image file not found: {args.image}")
            return
        
        if args.presets_only:
            test_presets(args.image)
        else:
            print("🎯 Advanced OCR Tuning Tool")
            print(f"Image: {args.image}")
            print(f"Strategy: {args.strategy}")
            
            # Test with specified strategy
            test_advanced_ocr(args.image, args.strategy)
            
            print(f"\n💡 Pro tips:")
            print(f"  Multi-strategy: python {sys.argv[0]} --multi-strategy {args.image}")
            print(f"  Compare all:    python {sys.argv[0]} --compare-all {args.image}")
            print(f"  Interactive:    python {sys.argv[0]} --interactive --image {args.image}")
    else:
        print("❌ Please specify an option")
        print("\n🔧 Quick start examples:")
        print("  python tune_ocr.py --image test.jpg --strategy advanced")
        print("  python tune_ocr.py --multi-strategy test.jpg")
        print("  python tune_ocr.py --compare-all test.jpg")
        print()
        parser.print_help()

if __name__ == "__main__":
    main()