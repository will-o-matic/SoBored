#!/usr/bin/env python3
"""
Direct test of advanced OCR preprocessing without LangChain wrapper
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_advanced_ocr_directly():
    """Test advanced OCR functions directly"""
    
    # Import the internal functions directly
    from langgraph.agents.tools.ocr_tool import (
        _load_image, 
        _preprocess_image, 
        _basic_preprocess_image,
        _high_contrast_preprocess,
        _text_focused_preprocess,
        _poster_optimized_preprocess,
        _clean_extracted_text,
        _calculate_average_confidence,
        _calculate_quality_score
    )
    
    import pytesseract
    
    image_path = "PreservationFallFestTestImage.png"
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    print(f"🔬 Testing Advanced OCR Preprocessing")
    print(f"📁 Image: {image_path}")
    print("=" * 80)
    
    # Load the image
    image = _load_image(image_path, "file")
    if image is None:
        print("❌ Failed to load image")
        return
    
    print(f"📐 Image size: {image.size[0]}x{image.size[1]}")
    
    # Test different preprocessing strategies
    strategies = [
        ("Basic", _basic_preprocess_image),
        ("Advanced", _preprocess_image),
        ("High Contrast", _high_contrast_preprocess),
        ("Text Focused", _text_focused_preprocess),
        ("Poster Optimized", _poster_optimized_preprocess)
    ]
    
    results = []
    tesseract_config = '--oem 1 --psm 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,&@:/-() '
    
    print(f"\n📊 Testing {len(strategies)} preprocessing strategies:")
    print(f"{'Strategy':<20} | {'Confidence':<10} | {'Words':<6} | {'Quality':<8} | {'Text Preview':<40}")
    print("-" * 110)
    
    for strategy_name, preprocess_func in strategies:
        try:
            start_time = time.time()
            
            # Preprocess image
            processed_image = preprocess_func(image)
            
            # Extract text
            extracted_text = pytesseract.image_to_string(processed_image, lang='eng', config=tesseract_config)
            
            # Get confidence
            confidence_data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT, config=tesseract_config)
            confidence = _calculate_average_confidence(confidence_data)
            
            # Clean text
            cleaned_text = _clean_extracted_text(extracted_text)
            
            # Calculate quality
            quality_score = _calculate_quality_score(cleaned_text, confidence)
            
            processing_time = time.time() - start_time
            word_count = len(cleaned_text.split())
            
            # Preview text (first 40 chars)
            preview = cleaned_text[:37] + "..." if len(cleaned_text) > 40 else cleaned_text
            preview = preview.replace('\n', ' ').replace('\r', ' ')
            
            result = {
                "strategy": strategy_name,
                "confidence": confidence,
                "word_count": word_count,
                "quality_score": quality_score,
                "cleaned_text": cleaned_text,
                "processing_time": processing_time,
                "preview": preview
            }
            
            results.append(result)
            
            print(f"{strategy_name:<20} | {confidence:>8.1f}% | {word_count:>4d} | {quality_score:>6.3f} | {preview}")
            
        except Exception as e:
            print(f"{strategy_name:<20} | {'ERROR':<10} | {'N/A':<6} | {'N/A':<8} | {str(e)[:40]}")
            continue
    
    if not results:
        print("❌ All strategies failed")
        return
    
    # Find best result
    best_result = max(results, key=lambda x: x['quality_score'])
    
    print("-" * 110)
    print(f"🏆 Best Strategy: {best_result['strategy']} (Quality: {best_result['quality_score']:.3f})")
    
    # Show detailed results
    print(f"\n📄 Best Result Details:")
    print(f"  Strategy: {best_result['strategy']}")
    print(f"  Confidence: {best_result['confidence']:.1f}%")
    print(f"  Quality Score: {best_result['quality_score']:.3f}")
    print(f"  Word Count: {best_result['word_count']}")
    print(f"  Processing Time: {best_result['processing_time']:.2f}s")
    
    print(f"\n📝 Full extracted text:")
    print("=" * 50)
    print(best_result['cleaned_text'])
    print("=" * 50)
    
    # Compare with expected text
    expected_text = "5th annual preservation fall fest featuring Joe Hertler & the Rainbow Seekers with Pajamas and Same Eyes live at Homes Campus Ann Arbor, MI Saturday, September 13 all ages doors at 6pm tickets at joehertler.com"
    
    print(f"\n🎯 Expected vs Actual Comparison:")
    print(f"Expected: {expected_text}")
    print(f"Actual:   {best_result['cleaned_text']}")
    
    # Calculate similarity metrics
    expected_words = set(expected_text.lower().split())
    actual_words = set(best_result['cleaned_text'].lower().split())
    
    if expected_words:
        word_overlap = len(expected_words.intersection(actual_words))
        word_precision = word_overlap / len(actual_words) if actual_words else 0
        word_recall = word_overlap / len(expected_words)
        word_f1 = 2 * (word_precision * word_recall) / (word_precision + word_recall) if (word_precision + word_recall) > 0 else 0
        
        print(f"\n📈 Accuracy Metrics:")
        print(f"  Word Overlap: {word_overlap}/{len(expected_words)} expected words found")
        print(f"  Precision: {word_precision:.1%} (correct words / total extracted)")
        print(f"  Recall: {word_recall:.1%} (found words / expected words)")
        print(f"  F1 Score: {word_f1:.1%}")
    
    # Performance summary
    print(f"\n⚡ Performance Summary:")
    avg_confidence = sum(r['confidence'] for r in results) / len(results)
    avg_quality = sum(r['quality_score'] for r in results) / len(results)
    print(f"  Average Confidence: {avg_confidence:.1f}%")
    print(f"  Average Quality: {avg_quality:.3f}")
    print(f"  Best Confidence: {max(r['confidence'] for r in results):.1f}%")
    print(f"  Best Quality: {max(r['quality_score'] for r in results):.3f}")

if __name__ == "__main__":
    test_advanced_ocr_directly()