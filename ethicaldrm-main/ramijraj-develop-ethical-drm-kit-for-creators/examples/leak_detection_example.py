#!/usr/bin/env python3
"""
Leak Detection Example for EthicalDRM

This example demonstrates how to:
1. Set up a leak scanner for content
2. Configure platform scanning
3. Run scans and analyze results
4. Generate takedown notices
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ethicaldrm import LeakScanner


async def main():
    print("🔍 EthicalDRM Leak Detection Example")
    print("=" * 50)
    
    # Example configuration
    original_content = "protected_lecture.mp4"  # Your protected content
    similarity_threshold = 0.85  # 85% similarity required for detection
    
    print(f"🎬 Protected Content: {original_content}")
    print(f"📊 Similarity Threshold: {similarity_threshold:.0%}")
    print()
    
    # Create leak scanner
    scanner = LeakScanner(
        original_content_path=original_content,
        similarity_threshold=similarity_threshold,
        scan_interval_hours=24  # Scan every 24 hours
    )
    
    print(f"✅ Scanner created with {len(scanner.reference_hashes)} reference hashes")
    print()
    
    # Configure platforms to scan
    print("⚙️ Configuring scan platforms...")
    
    # Configure Reddit scanning
    scanner.configure_platform('reddit', {
        'enabled': True,
        'subreddits': ['learnprogramming', 'freecourses', 'programming']
    })
    
    # Configure YouTube scanning  
    scanner.configure_platform('youtube', {
        'enabled': True,
        'keywords': ['programming tutorial', 'free course', 'lecture']
    })
    
    # Configure Telegram scanning (requires API setup)
    scanner.configure_platform('telegram', {
        'enabled': False,  # Disabled for demo
        'channels': ['@freecourses', '@programmingcourses']
    })
    
    print("✅ Platforms configured")
    print("   📱 Reddit: ✅ Enabled")
    print("   📺 YouTube: ✅ Enabled") 
    print("   💬 Telegram: ❌ Disabled (requires API setup)")
    print()
    
    # Run a scan
    print("🔄 Running leak detection scan...")
    scan_results = await scanner.run_full_scan()
    
    if 'error' in scan_results:
        print(f"❌ Scan failed: {scan_results['error']}")
        return
    
    # Display results
    print("📊 Scan Results:")
    print(f"   Duration: {scan_results['scan_duration']:.2f} seconds")
    print(f"   Total detections: {scan_results['total_detections']}")
    print(f"   High confidence: {scan_results['high_confidence_detections']}")
    print(f"   Platforms scanned: {', '.join(scan_results['platforms_scanned'])}")
    print()
    
    # Show detailed detections
    if scan_results['detections']:
        print("⚠️ Potential leaks detected:")
        for i, detection in enumerate(scan_results['detections'], 1):
            print(f"   {i}. Platform: {detection['platform']}")
            print(f"      URL: {detection.get('url', 'N/A')}")
            print(f"      Similarity: {detection.get('similarity_score', 0):.1%}")
            print(f"      Status: {detection.get('status', 'unknown')}")
            
            # Generate takedown notice for high-confidence detections
            if detection.get('similarity_score', 0) > 0.9:
                print("      📄 Generating takedown notice...")
                notice = scanner.generate_takedown_notice(detection)
                print(f"      📝 Notice preview: {notice[:100]}...")
            
            print()
    else:
        print("✅ No leaks detected - your content appears to be secure!")
    
    # Export results
    print("💾 Exporting scan results...")
    scanner.export_results("leak_scan_results.json", format="json")
    print("✅ Results exported to: leak_scan_results.json")
    print()
    
    # Schedule automated scanning (example)
    print("⏰ Setting up automated scanning...")
    scanner.start_scheduled_scanning()
    print("✅ Automated scanning scheduled every 24 hours")
    print("   (In production, this would run continuously)")
    
    # Stop scheduling for demo
    scanner.stop_scheduled_scanning()
    
    print()
    print("🎉 Leak detection example completed!")
    print("💡 In production, you would:")
    print("   1. Set up API keys for Telegram, YouTube etc.")
    print("   2. Configure more specific keywords and channels")
    print("   3. Set up automated takedown workflows")
    print("   4. Monitor results via the web dashboard")


if __name__ == "__main__":
    asyncio.run(main())