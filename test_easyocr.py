#!/usr/bin/env python3
"""
EasyOCR Testing Script for SoBored Image Processing

Test and compare EasyOCR vs Tesseract for optimal text extraction.

Usage:
    python test_easyocr.py --image ./test_image.jpg
    python test_easyocr.py --compare ./test_image.jpg
    python test_easyocr.py --hybrid ./test_image.jpg
"""

import os
import sys
import argparse
import json
import time
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_easyocr_only(image_path: str):
    """Test EasyOCR only"""
    try:
        from langgraph.agents.tools.easyocr_tool import extract_text_with_easyocr
        
        print(f"🔍 Testing EasyOCR on: {image_path}")
        print("=" * 60)
        
        result = extract_text_with_easyocr.invoke({
            "image_data": image_path,
            "image_format": "file"
        })
        
        if result.get("success"):
            print(f"✅ EasyOCR Results:")
            print(f"  Confidence: {result['confidence']:.1f}%")
            print(f"  Word Count: {result['word_count']}")
            print(f"  Text Regions: {result['region_count']}")
            print(f"  Processing Time: {result['processing_time']:.2f}s")
            print(f"\n📄 Extracted Text:")
            print("-" * 50)
            print(result['extracted_text'])
            print("-" * 50)
            
            if result.get('text_regions'):
                print(f"\n📋 Individual Text Regions:")
                for i, region in enumerate(result['text_regions'], 1):
                    print(f"  {i:2d}. \"{region['text']}\" (conf: {region['confidence']:.1f}%)")
        else:
            print(f"❌ EasyOCR failed: {result.get('error')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing EasyOCR: {e}")
        return {"success": False, "error": str(e)}

def compare_ocr_engines(image_path: str):
    """Compare Tesseract vs EasyOCR"""
    try:
        from langgraph.agents.tools.easyocr_tool import compare_ocr_engines
        
        print(f"🔬 Comparing OCR Engines on: {image_path}")
        print("=" * 80)
        
        result = compare_ocr_engines.invoke({
            "image_data": image_path,
            "image_format": "file"
        })
        
        if not result.get("success"):
            print(f"❌ Comparison failed: {result.get('error')}")
            return result
        
        tesseract = result['tesseract']
        easyocr = result['easyocr']
        comparison = result['comparison']
        
        print(f"\n📊 Results Comparison:")
        print(f"{'Metric':<20} | {'Tesseract':<15} | {'EasyOCR':<15} | {'Winner'}")
        print("-" * 70)
        
        # Success rate
        t_success = "✅ Success" if tesseract.get('success') else "❌ Failed"
        e_success = "✅ Success" if easyocr.get('success') else "❌ Failed"
        winner_success = "Tie" if tesseract.get('success') == easyocr.get('success') else (
            "EasyOCR" if easyocr.get('success') else "Tesseract"
        )
        print(f"{'Success':<20} | {t_success:<15} | {e_success:<15} | {winner_success}")
        
        if tesseract.get('success') and easyocr.get('success'):
            # Confidence
            t_conf = f"{tesseract.get('confidence', 0):.1f}%"
            e_conf = f"{easyocr.get('confidence', 0):.1f}%"
            winner_conf = "EasyOCR" if easyocr.get('confidence', 0) > tesseract.get('confidence', 0) else "Tesseract"
            print(f"{'Confidence':<20} | {t_conf:<15} | {e_conf:<15} | {winner_conf}")
            
            # Word count
            t_words = str(tesseract.get('word_count', 0))
            e_words = str(easyocr.get('word_count', 0))
            winner_words = "EasyOCR" if easyocr.get('word_count', 0) > tesseract.get('word_count', 0) else "Tesseract"
            print(f"{'Word Count':<20} | {t_words:<15} | {e_words:<15} | {winner_words}")
            
            # Quality score
            t_quality = f"{tesseract.get('quality_score', 0):.3f}"
            e_quality = f"{easyocr.get('quality_score', 0):.3f}"
            winner_quality = comparison['winner']
            print(f"{'Quality Score':<20} | {t_quality:<15} | {e_quality:<15} | {winner_quality}")
        
        print("-" * 70)
        print(f"🏆 Overall Winner: {comparison['winner']}")
        
        # Show text results
        print(f"\n📄 Text Extraction Results:")
        
        if tesseract.get('success'):
            print(f"\n🔧 Tesseract Text:")
            print("-" * 30)
            print(tesseract.get('extracted_text', 'No text'))
            print("-" * 30)
        
        if easyocr.get('success'):
            print(f"\n🎯 EasyOCR Text:")
            print("-" * 30)
            print(easyocr.get('extracted_text', 'No text'))
            print("-" * 30)
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if comparison['winner'] == 'EasyOCR':
            print("  ✅ EasyOCR performs better for this image type")
            print("  💡 Consider using EasyOCR for similar event flyers")
        else:
            print("  ✅ Tesseract performs better for this image")
            print("  💡 The image may be well-suited for traditional OCR")
        
        if comparison.get('confidence_difference', 0) > 20:
            print(f"  ⚠️  Large confidence difference ({comparison['confidence_difference']:.1f}%) - significant quality gap")
        
        if comparison.get('word_count_difference', 0) > 5:
            print(f"  ⚠️  Large word count difference ({comparison['word_count_difference']}) - one engine may be missing text")
        
        return result
        
    except Exception as e:
        print(f"❌ Error comparing engines: {e}")
        return {"success": False, "error": str(e)}

def test_hybrid_ocr(image_path: str):
    """Test hybrid OCR approach"""
    try:
        from langgraph.agents.tools.easyocr_tool import extract_text_with_hybrid_ocr
        
        print(f"🤖 Testing Hybrid OCR on: {image_path}")
        print("=" * 60)
        
        result = extract_text_with_hybrid_ocr.invoke({
            "image_data": image_path,
            "image_format": "file"
        })
        
        if result.get("success"):
            print(f"✅ Hybrid OCR Results:")
            print(f"  Selected Engine: {result.get('ocr_engine', 'Unknown')}")
            print(f"  Confidence: {result['confidence']:.1f}%")
            print(f"  Word Count: {result['word_count']}")
            
            analysis = result.get('hybrid_analysis', {})
            print(f"\n📊 Engine Comparison:")
            print(f"  Tesseract: {analysis.get('tesseract_confidence', 0):.1f}% conf, {analysis.get('tesseract_words', 0)} words")
            print(f"  EasyOCR:   {analysis.get('easyocr_confidence', 0):.1f}% conf, {analysis.get('easyocr_words', 0)} words")
            print(f"  Both succeeded: {analysis.get('both_succeeded', False)}")
            
            print(f"\n📄 Selected Text:")
            print("-" * 50)
            print(result['extracted_text'])
            print("-" * 50)
        else:
            print(f"❌ Hybrid OCR failed: {result.get('error')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing hybrid OCR: {e}")
        return {"success": False, "error": str(e)}

def install_dependencies():
    """Check and install EasyOCR dependencies"""
    try:
        import easyocr
        import torch
        print("✅ EasyOCR dependencies are already installed")
        return True
    except ImportError:
        print("📦 Installing EasyOCR dependencies...")
        import subprocess
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "easyocr", "torch", "torchvision"
            ])
            print("✅ EasyOCR dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            print("💡 Try manually: pip install easyocr torch torchvision")
            return False

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="EasyOCR Testing Tool for SoBored")
    parser.add_argument("--image", help="Path to test image")
    parser.add_argument("--compare", help="Compare Tesseract vs EasyOCR")
    parser.add_argument("--hybrid", help="Test hybrid OCR approach")
    parser.add_argument("--install", action="store_true", help="Install EasyOCR dependencies")
    
    args = parser.parse_args()
    
    if args.install:
        install_dependencies()
        return
    
    if args.compare:
        if not os.path.exists(args.compare):
            print(f"❌ Image file not found: {args.compare}")
            return
        compare_ocr_engines(args.compare)
        
    elif args.hybrid:
        if not os.path.exists(args.hybrid):
            print(f"❌ Image file not found: {args.hybrid}")
            return
        test_hybrid_ocr(args.hybrid)
        
    elif args.image:
        if not os.path.exists(args.image):
            print(f"❌ Image file not found: {args.image}")
            return
        test_easyocr_only(args.image)
        
    else:
        print("🎯 EasyOCR Testing Tool for SoBored")
        print("\n📚 Usage Examples:")
        print(f"  Test EasyOCR only:     python {sys.argv[0]} --image test.jpg")
        print(f"  Compare engines:       python {sys.argv[0]} --compare test.jpg")
        print(f"  Test hybrid approach:  python {sys.argv[0]} --hybrid test.jpg")
        print(f"  Install dependencies:  python {sys.argv[0]} --install")
        print()
        parser.print_help()

if __name__ == "__main__":
    main()