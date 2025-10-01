#!/usr/bin/env python3
"""
Basic Watermarking Example for EthicalDRM

This example demonstrates how to:
1. Embed a watermark in a video file
2. Extract watermark information
3. Verify watermark integrity
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ethicaldrm import Watermarker


def main():
    # Example configuration
    user_id = "student_42"
    input_video = "sample_lecture.mp4"  # Replace with your video file
    output_video = "watermarked_lecture.mp4"
    
    print("🛡️ EthicalDRM Basic Watermarking Example")
    print("=" * 50)
    
    # Check if input file exists
    if not os.path.exists(input_video):
        print(f"❌ Input video '{input_video}' not found!")
        print("Please provide a valid video file.")
        return
    
    # Create watermarker instance
    watermarker = Watermarker(
        user_id=user_id,
        method="lsb",  # Use LSB (Least Significant Bit) method
        strength=0.1   # Subtle watermark strength
    )
    
    print(f"📝 User ID: {user_id}")
    print(f"🎬 Input Video: {input_video}")
    print(f"📊 Method: LSB Encoding")
    print(f"💪 Strength: 0.1 (subtle)")
    print()
    
    # Step 1: Embed watermark
    print("🔄 Embedding watermark...")
    result = watermarker.embed(input_video, output_video)
    
    if result['success']:
        print("✅ Watermark embedded successfully!")
        print(f"   Output file: {result['output_path']}")
        print(f"   Signature: {result['signature']}")
        print(f"   Total frames: {result['total_frames']}")
        print(f"   Watermarked frames: {result['watermarked_frames']}")
        print(f"   File size: {result['file_size']:,} bytes")
    else:
        print(f"❌ Watermarking failed: {result.get('error', 'Unknown error')}")
        return
    
    print()
    
    # Step 2: Extract watermark (verification)
    print("🔍 Extracting watermark for verification...")
    extracted = watermarker.extract_watermark(output_video)
    
    if extracted:
        print("✅ Watermark extracted successfully!")
        print(f"   Extracted User ID: {extracted['user_id']}")
        print(f"   Signature: {extracted['signature']}")
        print(f"   Frame: {extracted['frame_number']}")
        
        # Verify it's the correct user
        if extracted['user_id'] == user_id:
            print("✅ User verification: PASSED")
        else:
            print("⚠️ User verification: FAILED")
    else:
        print("❌ No watermark found in output video!")
    
    print()
    
    # Step 3: Full integrity check
    print("🔒 Performing integrity verification...")
    verification = watermarker.verify_integrity(output_video)
    
    print(f"   File exists: {'✅' if verification['file_exists'] else '❌'}")
    print(f"   Watermark found: {'✅' if verification['watermark_found'] else '❌'}")
    print(f"   User verified: {'✅' if verification['user_verified'] else '❌'}")
    print(f"   Integrity score: {verification['integrity_score']:.2f}")
    
    print()
    print("🎉 Basic watermarking example completed!")
    print(f"💡 Your watermarked video is ready: {output_video}")


if __name__ == "__main__":
    main()