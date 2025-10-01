# 🚀 Getting Started with EthicalDRM

Welcome to EthicalDRM! This guide will help you get up and running quickly with content protection for indie creators.

## 📋 Prerequisites

- Python 3.8 or higher
- FFmpeg installed on your system
- A video file to test with (recommended: short test video, 10-30 seconds)

## 🛠️ Installation

### Option 1: Install from PyPI (Recommended)
```bash
pip install ethicaldrm
```

### Option 2: Install from Source
```bash
git clone https://github.com/ramijraj/ethicaldrm.git
cd ethicaldrm
pip install -e .
```

### Option 3: Development Setup
```bash
git clone https://github.com/ramijraj/ethicaldrm.git
cd ethicaldrm
pip install -r requirements.txt
pip install -e .[dev]
```

## 🎬 Your First Watermark

Let's start by adding a watermark to a video file:

### 1. Prepare a Test Video
Create or download a short video file named `test_video.mp4`.

### 2. Basic Watermarking
```python
from ethicaldrm import Watermarker

# Create watermarker for a user
watermarker = Watermarker(user_id="demo_user_123")

# Embed watermark
result = watermarker.embed("test_video.mp4", "watermarked_video.mp4")

if result['success']:
    print(f"✅ Watermark embedded!")
    print(f"Signature: {result['signature']}")
    print(f"Processed: {result['watermarked_frames']} frames")
else:
    print(f"❌ Failed: {result['error']}")
```

### 3. Verify the Watermark
```python
# Extract watermark to verify
extracted = watermarker.extract_watermark("watermarked_video.mp4")

if extracted:
    print(f"✅ Found watermark for user: {extracted['user_id']}")
    print(f"Signature: {extracted['signature']}")
else:
    print("❌ No watermark found")
```

## 🔍 Leak Detection Basics

### 1. Set Up a Scanner
```python
from ethicaldrm import LeakScanner
import asyncio

async def detect_leaks():
    # Create scanner for your content
    scanner = LeakScanner("watermarked_video.mp4", similarity_threshold=0.85)
    
    # Configure platforms to scan
    scanner.configure_platform('reddit', {
        'enabled': True,
        'subreddits': ['test', 'videos']  # Start with safe subreddits
    })
    
    # Run a scan
    results = await scanner.run_full_scan()
    
    print(f"Scan completed in {results['scan_duration']:.2f} seconds")
    print(f"Detections: {results['total_detections']}")
    
    return results

# Run the scan
results = asyncio.run(detect_leaks())
```

## 🛡️ Screen Recording Detection

### 1. Basic Detection
```python
from ethicaldrm import ScreenRecorderDetector
import time

def on_recorder_found(recorders):
    print("⚠️ Screen recorder detected!")
    for recorder in recorders:
        print(f"Process: {recorder['name']}")

# Create detector
detector = ScreenRecorderDetector(on_detection=on_recorder_found)

# Start monitoring
detector.start_monitoring()

# Monitor for 30 seconds
print("Monitoring for screen recorders... (try opening OBS)")
time.sleep(30)

# Stop monitoring
detector.stop_monitoring()
print("Monitoring stopped")
```

## 🌐 Using the REST API

### 1. Start the API Server
```bash
# Command line
ethicaldrm api --host localhost --port 5000

# Or in Python
from ethicaldrm.api.app import create_app

app = create_app()
app.run(host='localhost', port=5000)
```

### 2. Test API Endpoints
```bash
# Health check
curl http://localhost:5000/health

# Embed watermark (replace with your video file)
curl -X POST \
  -F "file=@test_video.mp4" \
  -F "user_id=api_test_user" \
  -F "method=lsb" \
  http://localhost:5000/watermark/embed
```

### 3. Using Python Requests
```python
import requests

# Upload and watermark a video
with open('test_video.mp4', 'rb') as f:
    files = {'file': f}
    data = {'user_id': 'api_test_user', 'method': 'lsb'}
    
    response = requests.post(
        'http://localhost:5000/watermark/embed',
        files=files,
        data=data
    )
    
    result = response.json()
    print(f"API Result: {result}")
```

## 🔧 Command Line Interface

EthicalDRM includes a powerful CLI for all operations:

### Watermarking
```bash
# Embed watermark
ethicaldrm watermark embed input.mp4 output.mp4 --user-id "student_123"

# Extract watermark
ethicaldrm watermark extract watermarked.mp4

# Verify watermark
ethicaldrm watermark verify watermarked.mp4 --user-id "student_123"
```

### Leak Detection
```bash
# Scan for leaks
ethicaldrm scan protected_video.mp4 --platforms reddit youtube

# Scan specific subreddits
ethicaldrm scan video.mp4 --reddit-subreddits "test" "videos"
```

### Screen Recording Detection
```bash
# Monitor for 60 seconds
ethicaldrm detect --duration 60

# List known recording software
ethicaldrm detect --list-known

# Use strict mode
ethicaldrm detect --strict --duration 30
```

## 📊 Real-World Integration Example

Here's how you might integrate EthicalDRM into a learning platform:

```python
from ethicaldrm import Watermarker, ScreenRecorderDetector
import logging

class SecureVideoPlayer:
    def __init__(self, user_id):
        self.user_id = user_id
        self.watermarker = Watermarker(user_id)
        self.detector = ScreenRecorderDetector(
            on_detection=self.handle_recording_detected
        )
        
    def handle_recording_detected(self, recorders):
        """Called when screen recording is detected"""
        logging.warning(f"Recording detected for user {self.user_id}")
        # In a real app, you might:
        # - Pause video playback
        # - Show a warning message
        # - Log the security event
        print("⚠️ Please close screen recording software to continue")
    
    def play_protected_video(self, video_path):
        """Play video with protection enabled"""
        # Start screen recording detection
        self.detector.start_monitoring()
        
        # In a real app, you would:
        # 1. Watermark the video on-the-fly or serve pre-watermarked version
        # 2. Use your video player to display the content
        # 3. Stop detection when video ends
        
        print(f"Playing protected video for user {self.user_id}")
        print("Screen recording protection: ACTIVE")
        
        # Simulate video playback
        import time
        time.sleep(5)  # Simulate 5 seconds of video
        
        # Stop protection
        self.detector.stop_monitoring()
        print("Video playback completed")

# Usage
player = SecureVideoPlayer("student_456")
player.play_protected_video("lesson_video.mp4")
```

## 🎯 Next Steps

1. **Explore Examples**: Check out the `examples/` directory for more detailed use cases
2. **Run Tests**: Execute `pytest tests/` to ensure everything works
3. **Read Documentation**: Visit our [GitHub Wiki](https://github.com/ramijraj/ethicaldrm/wiki) for advanced features
4. **Join Community**: Connect with other users on our [Discord](https://discord.gg/ethicaldrm)

## ⚠️ Important Notes

- **Test with Small Files**: Start with short videos to learn the system
- **Backup Originals**: Always keep backup copies of your original content
- **Check Platform Policies**: Ensure leak detection complies with platform terms of service
- **Privacy Considerations**: Be transparent with users about watermarking

## 🆘 Troubleshooting

### Common Issues

1. **"Cannot open video file"**
   - Ensure FFmpeg is installed
   - Check video file format (MP4 recommended)
   - Verify file path is correct

2. **"No watermark detected"**
   - Video may have been re-encoded, removing watermark
   - Try increasing watermark strength
   - Check if correct extraction method is used

3. **"API server won't start"**
   - Port 5000 might be in use
   - Try a different port: `ethicaldrm api --port 8080`

4. **"Screen recording detection not working"**
   - Some platforms have limited process visibility
   - Try enabling strict mode
   - Check if you have necessary permissions

### Getting Help

- 📖 [Documentation](https://github.com/ramijraj/ethicaldrm/wiki)
- 🐛 [Report Issues](https://github.com/ramijraj/ethicaldrm/issues)
- 💬 [Discord Community](https://discord.gg/ethicaldrm)
- 📧 [Email Support](mailto:ramijraj.ethicaldrm@proton.me)

---

Welcome to the EthicalDRM community! We're excited to help you protect your content ethically and effectively. 🛡️✨