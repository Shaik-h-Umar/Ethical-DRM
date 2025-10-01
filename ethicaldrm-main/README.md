# �️ EthicalDRM - Ethical Digital Rights Management Kit

**Version:** 1.0 | **Author:** Ramij Raj | **License:** MIT | **Status:** Beta  
**Project Codename:** EthicalDRM

A lightweight, pluggable DRM (Digital Rights Management) kit built for independent creators, teachers, and small studios who want to protect their content — ethically and efficiently.

EthicalDRM enables content tracking, piracy deterrence, and watermark-based leak detection — without ruining the experience for genuine users.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Status: Beta](https://img.shields.io/badge/status-beta-orange.svg)](https://github.com/ramijraj/ethicaldrm)

## 🎯 Who It's For

| Role | Use Case |
|------|----------|
| 🎬 **Indie Filmmakers** | Protect short films released on your website or app |
| 👨‍🏫 **Online Educators** | Stop screen recording and unauthorized content sharing |
| 📦 **OTT Startups** | Track leaks and personalize video distribution securely |
| 📚 **eLearning Platforms** | Watermark PDFs/videos with student info |

## 🔧 Features

| Feature | Description | Status |
|---------|-------------|--------|
| ✅ **Invisible Watermarking** | Embed account or user ID into video/audio frames silently | ✅ Done |
| 🛑 **Screen Recording Block** | Detect & block tools like OBS, Snagit, Bandicam (Windows/Mac) | ✅ Done |
| 🧠 **AI Leak Detection** | Scene-matching via perceptual hashing (video/audio) | ✅ Beta |
| � **Leak Traceback** | Pinpoint which user leaked based on watermark or signature | ✅ Done |
| ⚙️ **Easy Integration** | Add via Python/JS SDK or REST API in 10 minutes | ✅ Done |
| 🌐 **Web Crawler Bot** | Scans public sites, Telegram groups, YouTube, torrents for leaks | 🔄 In Progress |
| 👥 **User-Friendly** | No forced encryption, easy opt-out for users with older devices | ✅ Done |

## 🏗️ Architecture

```
[ Your Platform ]
      |
[ EthicalDRM SDK ]
      |
-------------------------------
| Video Watermarker (Python)  |
| Screen Rec Detector (JS/C++)|
| Leak Scanner Bot (Python)   |
| REST API Interface (Flask)  |
-------------------------------
      |
[ MongoDB / SQLite Logging DB ]
```

## 🚀 Quick Start

### 1. Install SDK

```bash
pip install ethicaldrm
```

### 2. Embed Watermark in Video

```python
from ethicaldrm import Watermarker

wm = Watermarker(user_id="student_42")
wm.embed("lecture.mp4", "protected_lecture.mp4")
```

### 3. Detect Leaks from Telegram

```python
from ethicaldrm import LeakScanner

scanner = LeakScanner("protected_lecture.mp4")
scanner.scan_telegram_groups(["@piracychannel1", "@freecourseshub"])
```

### 4. Screen Recording Detection

```python
from ethicaldrm import ScreenRecorderDetector

detector = ScreenRecorderDetector()
detector.start_monitoring()
```

### 5. REST API Usage

```bash
# Start API server
ethicaldrm api --host 0.0.0.0 --port 5000

# Embed watermark via API
curl -X POST -F "file=@video.mp4" -F "user_id=student_42" \
  http://localhost:5000/watermark/embed
```

## � Project Structure

```
ethicaldrm/
│
├── video/
│   ├── watermark.py      # LSB & motion blur watermarking
│   └── utils.py          # Video processing utilities
├── recorder/
│   └── detect.py         # Screen recorder detection
├── leakbot/
│   └── scanner.py        # AI-powered leak detection
├── api/
│   └── app.py            # Flask REST API server
│
├── examples/             # Usage examples
├── tests/               # Test suite
├── requirements.txt     # Dependencies
├── setup.py            # Package installation
└── README.md           # This file
```

## ⚙️ Modules

### 📼 video.watermark
- Adds invisible pixel-level watermark using LSB encoding or motion blur patterns
- Per-user dynamic watermarks
- Minimal visual impact

### 🖥️ recorder.detect
- Detects screen recorders (Windows/macOS/Linux)
- Alerts or disables playback temporarily
- Configurable response actions

### 🧠 leakbot
- Uses perceptual hashing (pHash) for content matching
- Crawls public forums, torrents, Telegram, and compares against original files
- Automated takedown notice generation

### 🌐 api
- Provides REST endpoints for all functionality
- File upload/download support
- Session management and reporting

## 🧪 Testing

```bash
# Run test suite
pytest tests/

# Run with coverage
pytest tests/ --cov=ethicaldrm --cov-report=html
```

Test coverage includes:
- Watermark accuracy and extraction
- Leak scan matching algorithms
- Screen recorder detection across platforms

## 📚 Example Use Cases

### 🔐 Case 1: Online Course Creator
```python
# Watermark each video with student ID
watermarker = Watermarker(user_id="student_123")
result = watermarker.embed("lesson1.mp4", "lesson1_protected.mp4")

# If leak is found, traceback is immediate
if result['success']:
    print(f"Student {result['user_id']} can be traced if content leaks")
```

### 🎥 Case 2: Indie Filmmaker
```python
# Set up automated leak monitoring
scanner = LeakScanner("my_film_trailer.mp4", similarity_threshold=0.9)
scanner.configure_platform('youtube', {
    'enabled': True,
    'keywords': ['my film title', 'indie film']
})

# Bot scans every 24 hours
scanner.start_scheduled_scanning()
```

## 💬 Ethical Philosophy

We believe security shouldn't punish the honest user. Our goals:

- ✅ **No harsh encryption** - Content remains accessible
- ✅ **No device lockouts** - Works on older devices  
- ✅ **Only trace + notify** when a leak happens
- ✅ **Transparency over surveillance** - Users know what's happening

## 📅 Roadmap

| Feature | Status |
|---------|--------|
| Screen Recorder Blocking | ✅ Done |
| Telegram Leak Crawler | ✅ Beta |
| Auto Takedown Notice Generator | 🔄 In Progress |
| Google Drive Leak Detection | ⏳ Planned |
| JS SDK for Browser Videos | ⏳ Planned |
| GUI Dashboard | 🧪 Alpha |

## 🤝 Contributing

We welcome contributions! To contribute:

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Submit a Pull Request

## 📖 Documentation

- 📚 [API Documentation](https://github.com/ramijraj/ethicaldrm/wiki/API)
- 🎓 [Tutorial Videos](https://github.com/ramijraj/ethicaldrm/wiki/Tutorials)
- 💡 [Best Practices](https://github.com/ramijraj/ethicaldrm/wiki/Best-Practices)
- 🔧 [Integration Guide](https://github.com/ramijraj/ethicaldrm/wiki/Integration)

## 📬 Contact & Support

For support, feedback, or business inquiries:

- 📧 **Email:** ramijraj31@gmail.com
- 🌐 **GitHub:** [github.com/ramijraj/ethicaldrm](https://github.com/ramijraj/ethicaldrm)
- 💬 **Discord:** [Join our community](https://discord.gg/ethicaldrm)
- 🐦 **Twitter:** [@EthicalDRM](https://twitter.com/EthicalDRM)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenCV team for computer vision tools
- Flask team for the web framework
- All contributors who help make content protection ethical and accessible

---

**Made with ❤️ for indie creators who want to protect their work without punishing their audience.**
