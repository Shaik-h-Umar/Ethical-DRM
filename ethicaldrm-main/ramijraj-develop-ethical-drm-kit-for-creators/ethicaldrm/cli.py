#!/usr/bin/env python3
"""
Command-line interface for EthicalDRM.

Provides easy access to watermarking, leak detection, and screen recording
detection functionality through a unified CLI.
"""

import argparse
import sys
import os
import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

from .video.watermark import Watermarker
from .leakbot.scanner import LeakScanner
from .recorder.detect import ScreenRecorderDetector
from .api.app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_watermark_parser(subparsers):
    """Set up watermark subcommand parsers."""
    watermark_parser = subparsers.add_parser(
        'watermark',
        help='Watermark operations'
    )
    watermark_subparsers = watermark_parser.add_subparsers(
        dest='watermark_action',
        help='Watermark actions'
    )
    
    # Embed watermark
    embed_parser = watermark_subparsers.add_parser(
        'embed',
        help='Embed watermark in video'
    )
    embed_parser.add_argument('input', help='Input video file')
    embed_parser.add_argument('output', help='Output video file')
    embed_parser.add_argument('--user-id', required=True, help='User ID for watermark')
    embed_parser.add_argument('--method', choices=['lsb', 'motion_blur'], default='lsb',
                             help='Watermarking method')
    embed_parser.add_argument('--strength', type=float, default=0.1,
                             help='Watermark strength (0.0-1.0)')
    embed_parser.add_argument('--frame-interval', type=int, default=30,
                             help='Watermark every N frames')
    
    # Extract watermark
    extract_parser = watermark_subparsers.add_parser(
        'extract',
        help='Extract watermark from video'
    )
    extract_parser.add_argument('input', help='Input video file')
    extract_parser.add_argument('--method', choices=['lsb', 'motion_blur'], default='lsb',
                               help='Extraction method')
    
    # Verify watermark
    verify_parser = watermark_subparsers.add_parser(
        'verify',
        help='Verify watermark integrity'
    )
    verify_parser.add_argument('input', help='Input video file')
    verify_parser.add_argument('--user-id', required=True, help='User ID to verify')


def setup_scanner_parser(subparsers):
    """Set up leak scanner subcommand parsers."""
    scanner_parser = subparsers.add_parser(
        'scan',
        help='Leak detection operations'
    )
    scanner_parser.add_argument('content', help='Original content file path')
    scanner_parser.add_argument('--threshold', type=float, default=0.85,
                               help='Similarity threshold (0.0-1.0)')
    scanner_parser.add_argument('--platforms', nargs='+',
                               choices=['reddit', 'youtube', 'telegram'],
                               default=['reddit', 'youtube'],
                               help='Platforms to scan')
    scanner_parser.add_argument('--reddit-subreddits', nargs='+',
                               default=['learnprogramming', 'freecourses'],
                               help='Reddit subreddits to scan')
    scanner_parser.add_argument('--youtube-keywords', nargs='+',
                               default=['tutorial', 'course'],
                               help='YouTube search keywords')
    scanner_parser.add_argument('--telegram-channels', nargs='+',
                               default=[],
                               help='Telegram channels to scan')
    scanner_parser.add_argument('--output', '-o', help='Output file for results')


def setup_detector_parser(subparsers):
    """Set up screen recording detector subcommand parsers."""
    detector_parser = subparsers.add_parser(
        'detect',
        help='Screen recording detection'
    )
    detector_parser.add_argument('--duration', type=int, default=30,
                                help='Monitoring duration in seconds')
    detector_parser.add_argument('--interval', type=float, default=2.0,
                                help='Check interval in seconds')
    detector_parser.add_argument('--strict', action='store_true',
                                help='Enable strict mode detection')
    detector_parser.add_argument('--list-known', action='store_true',
                                help='List known recording software')


def setup_api_parser(subparsers):
    """Set up API server subcommand parser."""
    api_parser = subparsers.add_parser(
        'api',
        help='Start API server'
    )
    api_parser.add_argument('--host', default='0.0.0.0',
                           help='Server host')
    api_parser.add_argument('--port', type=int, default=5000,
                           help='Server port')
    api_parser.add_argument('--debug', action='store_true',
                           help='Enable debug mode')


def handle_watermark_embed(args):
    """Handle watermark embedding."""
    print(f"🔄 Embedding watermark for user '{args.user_id}'...")
    
    watermarker = Watermarker(
        user_id=args.user_id,
        method=args.method,
        strength=args.strength
    )
    
    result = watermarker.embed(
        input_path=args.input,
        output_path=args.output,
        frame_interval=args.frame_interval
    )
    
    if result['success']:
        print("✅ Watermark embedded successfully!")
        print(f"   Output: {result['output_path']}")
        print(f"   Signature: {result['signature']}")
        print(f"   Frames processed: {result['watermarked_frames']}/{result['total_frames']}")
        return 0
    else:
        print(f"❌ Watermarking failed: {result.get('error', 'Unknown error')}")
        return 1


def handle_watermark_extract(args):
    """Handle watermark extraction."""
    print(f"🔍 Extracting watermark from '{args.input}'...")
    
    watermarker = Watermarker("temp")  # Temporary instance
    extracted = watermarker.extract_watermark(args.input, args.method)
    
    if extracted:
        print("✅ Watermark found!")
        print(f"   User ID: {extracted['user_id']}")
        print(f"   Signature: {extracted['signature']}")
        print(f"   Frame: {extracted['frame_number']}")
        return 0
    else:
        print("❌ No watermark detected")
        return 1


def handle_watermark_verify(args):
    """Handle watermark verification."""
    print(f"🔒 Verifying watermark for user '{args.user_id}'...")
    
    watermarker = Watermarker(args.user_id)
    verification = watermarker.verify_integrity(args.input)
    
    print(f"   File exists: {'✅' if verification['file_exists'] else '❌'}")
    print(f"   Watermark found: {'✅' if verification['watermark_found'] else '❌'}")
    print(f"   User verified: {'✅' if verification['user_verified'] else '❌'}")
    print(f"   Integrity score: {verification['integrity_score']:.2f}")
    
    return 0 if verification['user_verified'] else 1


async def handle_scanner(args):
    """Handle leak scanning."""
    print(f"🔍 Setting up leak scanner for '{args.content}'...")
    
    scanner = LeakScanner(
        original_content_path=args.content,
        similarity_threshold=args.threshold
    )
    
    print(f"✅ Scanner created with {len(scanner.reference_hashes)} reference hashes")
    
    # Configure platforms
    if 'reddit' in args.platforms:
        scanner.configure_platform('reddit', {
            'enabled': True,
            'subreddits': args.reddit_subreddits
        })
        print(f"📱 Reddit configured: {args.reddit_subreddits}")
    
    if 'youtube' in args.platforms:
        scanner.configure_platform('youtube', {
            'enabled': True,
            'keywords': args.youtube_keywords
        })
        print(f"📺 YouTube configured: {args.youtube_keywords}")
    
    if 'telegram' in args.platforms:
        scanner.configure_platform('telegram', {
            'enabled': True,
            'channels': args.telegram_channels
        })
        print(f"💬 Telegram configured: {args.telegram_channels}")
    
    # Run scan
    print("🔄 Running leak detection scan...")
    results = await scanner.run_full_scan()
    
    if 'error' in results:
        print(f"❌ Scan failed: {results['error']}")
        return 1
    
    print("📊 Scan Results:")
    print(f"   Duration: {results['scan_duration']:.2f} seconds")
    print(f"   Total detections: {results['total_detections']}")
    print(f"   High confidence: {results['high_confidence_detections']}")
    
    if results['detections']:
        print("\n⚠️ Potential leaks detected:")
        for i, detection in enumerate(results['detections'], 1):
            print(f"   {i}. {detection['platform']}: {detection.get('url', 'N/A')}")
            print(f"      Similarity: {detection.get('similarity_score', 0):.1%}")
    else:
        print("✅ No leaks detected!")
    
    # Save results if output specified
    if args.output:
        scanner.export_results(args.output, format='json')
        print(f"💾 Results saved to: {args.output}")
    
    return 0


def handle_detector(args):
    """Handle screen recording detection."""
    print("🛡️ Setting up screen recording detection...")
    
    def on_detection(detections):
        print("\n⚠️ SCREEN RECORDER DETECTED!")
        for detection in detections:
            print(f"   📹 {detection['name']} (PID: {detection['pid']})")
    
    detector = ScreenRecorderDetector(
        check_interval=args.interval,
        on_detection=on_detection,
        strict_mode=args.strict
    )
    
    if args.list_known:
        print(f"🔍 Known screen recorders for {detector.platform}:")
        for i, recorder in enumerate(detector.known_processes, 1):
            print(f"   {i}. {recorder}")
        return 0
    
    print(f"⚙️ Configuration:")
    print(f"   Platform: {detector.platform}")
    print(f"   Check interval: {args.interval}s")
    print(f"   Strict mode: {'✅' if args.strict else '❌'}")
    print(f"   Duration: {args.duration}s")
    
    # Perform initial scan
    detected = detector.detect_recording_software()
    if detected:
        print(f"\n⚠️ Found {len(detected)} active recorders:")
        for d in detected:
            print(f"   📹 {d['name']} (PID: {d['pid']})")
    else:
        print("\n✅ No recording software detected")
    
    # Start monitoring
    print(f"\n🚀 Starting {args.duration}s monitoring...")
    success = detector.start_monitoring()
    
    if success:
        try:
            import time
            time.sleep(args.duration)
        except KeyboardInterrupt:
            print("\n🛑 Monitoring interrupted")
        finally:
            detector.stop_monitoring()
            print("⏹️ Monitoring stopped")
    else:
        print("❌ Failed to start monitoring")
        return 1
    
    return 0


def handle_api(args):
    """Handle API server startup."""
    print(f"🌐 Starting EthicalDRM API server...")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Debug: {'✅' if args.debug else '❌'}")
    
    app = create_app()
    
    try:
        app.run(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed: {str(e)}")
        return 1
    
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='EthicalDRM - Ethical Digital Rights Management for Indie Creators',
        epilog='For more information, visit: https://github.com/ramijraj/ethicaldrm'
    )
    
    parser.add_argument('--version', action='version', version='EthicalDRM 1.0.0')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Set up subcommand parsers
    setup_watermark_parser(subparsers)
    setup_scanner_parser(subparsers)
    setup_detector_parser(subparsers)
    setup_api_parser(subparsers)
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle commands
    try:
        if args.command == 'watermark':
            if args.watermark_action == 'embed':
                return handle_watermark_embed(args)
            elif args.watermark_action == 'extract':
                return handle_watermark_extract(args)
            elif args.watermark_action == 'verify':
                return handle_watermark_verify(args)
            else:
                print("❌ No watermark action specified")
                return 1
        
        elif args.command == 'scan':
            return asyncio.run(handle_scanner(args))
        
        elif args.command == 'detect':
            return handle_detector(args)
        
        elif args.command == 'api':
            return handle_api(args)
        
        else:
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())