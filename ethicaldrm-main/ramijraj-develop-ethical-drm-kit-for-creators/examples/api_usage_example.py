#!/usr/bin/env python3
"""
API Usage Example for EthicalDRM

This example demonstrates how to:
1. Start the EthicalDRM API server
2. Use the REST endpoints for watermarking
3. Create and manage leak scanners via API
4. Manage screen recording detection via API
"""

import requests
import time
import json
import threading
import sys
from pathlib import Path

# Add parent directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ethicaldrm.api.app import create_app


class EthicalDRMAPIClient:
    """Simple API client for EthicalDRM."""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self):
        """Check if API is healthy."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.json() if response.status_code == 200 else None
        except:
            return None
    
    def embed_watermark(self, file_path, user_id, method="lsb", strength=0.1):
        """Embed watermark via API."""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'user_id': user_id,
                'method': method,
                'strength': strength
            }
            
            response = self.session.post(
                f"{self.base_url}/watermark/embed",
                files=files,
                data=data
            )
            
            return response.json()
    
    def extract_watermark(self, file_path):
        """Extract watermark via API."""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            
            response = self.session.post(
                f"{self.base_url}/watermark/extract",
                files=files
            )
            
            return response.json()
    
    def create_scanner(self, original_content_path, similarity_threshold=0.85):
        """Create leak scanner via API."""
        data = {
            'original_content_path': original_content_path,
            'similarity_threshold': similarity_threshold,
            'scan_interval_hours': 24
        }
        
        response = self.session.post(
            f"{self.base_url}/scanner/create",
            json=data
        )
        
        return response.json()
    
    def start_detection(self, check_interval=2.0, strict_mode=False):
        """Start screen recording detection via API."""
        data = {
            'check_interval': check_interval,
            'strict_mode': strict_mode
        }
        
        response = self.session.post(
            f"{self.base_url}/detector/start",
            json=data
        )
        
        return response.json()
    
    def get_reports(self, report_type="watermarks", limit=10):
        """Get reports via API."""
        response = self.session.get(
            f"{self.base_url}/reports/{report_type}?limit={limit}"
        )
        
        return response.json()


def start_api_server():
    """Start the API server in a separate thread."""
    app = create_app()
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)


def main():
    print("🌐 EthicalDRM API Usage Example")
    print("=" * 45)
    
    # Start API server in background
    print("🚀 Starting API server...")
    server_thread = threading.Thread(target=start_api_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(3)
    
    # Create API client
    client = EthicalDRMAPIClient()
    
    # Health check
    print("🏥 Checking API health...")
    health = client.health_check()
    
    if health:
        print("✅ API is healthy!")
        print(f"   Version: {health['version']}")
        print(f"   Status: {health['status']}")
        print(f"   Timestamp: {health['timestamp']}")
    else:
        print("❌ API is not responding")
        return
    
    print()
    
    # Example 1: Watermarking via API
    print("1️⃣ Watermarking Example")
    print("-" * 30)
    
    # Note: You would need an actual video file for this to work
    sample_video = "sample.mp4"
    
    print(f"📹 Video file: {sample_video}")
    print("⚠️ Note: This example requires an actual video file")
    
    # Simulated watermarking (would work with real file)
    # result = client.embed_watermark(sample_video, "demo_user", "lsb", 0.1)
    # print(f"✅ Watermarking result: {result}")
    
    print("💡 To test watermarking:")
    print("   1. Place a video file named 'sample.mp4' in this directory")
    print("   2. Uncomment the watermarking code above")
    print("   3. Run the script again")
    print()
    
    # Example 2: Leak Scanner via API
    print("2️⃣ Leak Scanner Example")
    print("-" * 30)
    
    print("📡 Creating leak scanner...")
    scanner_result = client.create_scanner(
        original_content_path="protected_content.mp4",
        similarity_threshold=0.85
    )
    
    if scanner_result.get('success'):
        scanner_id = scanner_result['scanner_id']
        print(f"✅ Scanner created: {scanner_id}")
        print(f"   Reference hashes: {scanner_result['reference_hashes_count']}")
        print(f"   Threshold: {scanner_result['similarity_threshold']:.0%}")
    else:
        print(f"❌ Scanner creation failed: {scanner_result.get('error')}")
    
    print()
    
    # Example 3: Screen Recording Detection via API
    print("3️⃣ Screen Recording Detection Example")
    print("-" * 40)
    
    print("🛡️ Starting screen recording detection...")
    detection_result = client.start_detection(check_interval=2.0, strict_mode=True)
    
    if detection_result.get('success'):
        detector_id = detection_result['detector_id']
        print(f"✅ Detection started: {detector_id}")
        print(f"   Check interval: {detection_result['check_interval']}s")
        print(f"   Strict mode: {detection_result['strict_mode']}")
    else:
        print(f"❌ Detection start failed: {detection_result.get('error')}")
    
    print()
    
    # Example 4: Reports via API
    print("4️⃣ Reports Example")
    print("-" * 20)
    
    print("📊 Fetching watermark reports...")
    watermark_reports = client.get_reports("watermarks", limit=5)
    
    if watermark_reports.get('success'):
        sessions = watermark_reports['watermark_sessions']
        print(f"✅ Found {len(sessions)} watermarking sessions")
        for session in sessions[:3]:  # Show first 3
            print(f"   User: {session.get('user_id', 'N/A')}")
            print(f"   Method: {session.get('method', 'N/A')}")
            print(f"   Status: {session.get('status', 'N/A')}")
            print(f"   Timestamp: {session.get('timestamp', 'N/A')}")
            print()
    else:
        print("❌ No watermark reports available")
    
    print("📊 Fetching detection reports...")
    detection_reports = client.get_reports("detections", limit=5)
    
    if detection_reports.get('success'):
        detections = detection_reports['leak_detections']
        print(f"✅ Found {len(detections)} leak detections")
        if not detections:
            print("   (No leaks detected - that's good!)")
    else:
        print("❌ No detection reports available")
    
    print()
    
    # Example API endpoints summary
    print("📋 Available API Endpoints")
    print("-" * 30)
    endpoints = [
        "GET  /health - Health check",
        "POST /watermark/embed - Embed watermark",
        "POST /watermark/extract - Extract watermark", 
        "POST /watermark/verify - Verify watermark",
        "POST /scanner/create - Create leak scanner",
        "POST /scanner/scan - Run scan",
        "GET  /scanner/results/<id> - Get scan results",
        "POST /detector/start - Start recording detection",
        "POST /detector/stop/<id> - Stop detection",
        "GET  /detector/status/<id> - Get detection status",
        "GET  /reports/watermarks - Get watermark reports",
        "GET  /reports/detections - Get detection reports",
        "POST /reports/export - Export reports",
        "GET  /download/<filename> - Download files"
    ]
    
    for endpoint in endpoints:
        print(f"   {endpoint}")
    
    print()
    print("🎉 API usage example completed!")
    print()
    print("💡 Next steps:")
    print("   1. Explore the API with tools like Postman or curl")
    print("   2. Build a web frontend using these endpoints")
    print("   3. Integrate with your existing content delivery system")
    print("   4. Set up production deployment with gunicorn")
    print()
    print("📖 API Documentation:")
    print("   • Base URL: http://localhost:5000")
    print("   • Content-Type: application/json (for JSON requests)")
    print("   • File uploads: multipart/form-data")
    print("   • Max upload size: 500MB")


if __name__ == "__main__":
    main()