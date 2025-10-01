#!/usr/bin/env python3
"""
Screen Recording Detection Example for EthicalDRM

This example demonstrates how to:
1. Set up screen recording detection
2. Monitor for recording software
3. Handle detection events
4. Get system information
"""

import time
import sys
from pathlib import Path

# Add parent directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ethicaldrm import ScreenRecorderDetector


def on_recorder_detected(detected_recorders):
    """Callback function when screen recorders are detected."""
    print("\n⚠️ SCREEN RECORDER DETECTED!")
    print("=" * 40)
    
    for recorder in detected_recorders:
        print(f"📹 Process: {recorder['name']}")
        print(f"🆔 PID: {recorder['pid']}")
        print(f"🔍 Detection method: {recorder['recorder_type']}")
        print(f"⚡ Severity: {recorder['severity']}")
        print(f"📁 Executable: {recorder.get('exe', 'N/A')}")
        print("-" * 30)
    
    print("🛡️ Recommended actions:")
    print("   1. Pause content playback")
    print("   2. Display warning to user")
    print("   3. Log security event")
    print("   4. Optional: Request recorder to be closed")
    print()


def main():
    print("🛡️ EthicalDRM Screen Recording Detection Example")
    print("=" * 55)
    
    # Display system information
    print("💻 System Information:")
    system_info = ScreenRecorderDetector.get_system_info()
    for key, value in system_info.items():
        print(f"   {key.replace('_', ' ').title()}: {value}")
    print()
    
    # Create detector with custom settings
    detector = ScreenRecorderDetector(
        check_interval=2.0,          # Check every 2 seconds
        on_detection=on_recorder_detected,  # Callback function
        strict_mode=True             # Enable heuristic detection
    )
    
    print("⚙️ Detector Configuration:")
    print(f"   Check interval: {detector.check_interval} seconds")
    print(f"   Strict mode: {'✅' if detector.strict_mode else '❌'}")
    print(f"   Platform: {detector.platform}")
    print(f"   Known recorders: {len(detector.known_processes)}")
    print()
    
    # Show some known recorders for current platform
    print(f"🔍 Known screen recorders for {detector.platform}:")
    for i, recorder in enumerate(detector.known_processes[:10], 1):
        print(f"   {i}. {recorder}")
    if len(detector.known_processes) > 10:
        print(f"   ... and {len(detector.known_processes) - 10} more")
    print()
    
    # Perform immediate scan
    print("🔄 Performing initial scan...")
    detected = detector.detect_recording_software()
    
    if detected:
        print(f"⚠️ Found {len(detected)} active recording processes:")
        for recorder in detected:
            print(f"   📹 {recorder['name']} (PID: {recorder['pid']})")
    else:
        print("✅ No screen recording software detected")
    print()
    
    # Start continuous monitoring
    print("🚀 Starting continuous monitoring...")
    success = detector.start_monitoring()
    
    if success:
        print("✅ Monitoring started successfully")
        print("⏱️ Monitoring for 30 seconds (try opening OBS, Bandicam, etc.)")
        print("🛑 Press Ctrl+C to stop")
        print()
        
        try:
            # Monitor for 30 seconds
            for i in range(30):
                time.sleep(1)
                
                # Show status every 10 seconds
                if (i + 1) % 10 == 0:
                    status = detector.get_detection_status()
                    print(f"📊 Status update ({i+1}s):")
                    print(f"   Active: {'✅' if status['monitoring_active'] else '❌'}")
                    print(f"   Currently detected: {status['currently_detected']}")
                    if status['detected_processes']:
                        for proc in status['detected_processes']:
                            print(f"   - {proc['name']} ({proc['severity']})")
                    print()
                    
        except KeyboardInterrupt:
            print("\n🛑 Monitoring interrupted by user")
        
        # Stop monitoring
        print("⏹️ Stopping monitoring...")
        detector.stop_monitoring()
        print("✅ Monitoring stopped")
        
    else:
        print("❌ Failed to start monitoring")
    
    print()
    
    # Demonstrate custom recorder addition
    print("➕ Adding custom recorder to detection list...")
    detector.add_custom_recorder("my_custom_recorder.exe")
    print("✅ Custom recorder added")
    print()
    
    # Final status
    final_status = detector.get_detection_status()
    print("📋 Final Status:")
    print(f"   Known recorders: {final_status['known_recorders_count']}")
    print(f"   Platform: {final_status['platform']}")
    print(f"   Check interval: {final_status['check_interval']}s")
    print()
    
    print("🎉 Screen recording detection example completed!")
    print()
    print("💡 Integration tips:")
    print("   1. Call detector.start_monitoring() when content starts playing")
    print("   2. Use the callback to pause playback when recorders detected")
    print("   3. Call detector.stop_monitoring() when content stops")
    print("   4. Customize the known_processes list for your specific needs")
    print("   5. Use strict_mode=False to reduce false positives")


if __name__ == "__main__":
    main()