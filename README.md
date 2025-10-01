# �️ EthicalDRM - Ethical Digital Rights Management Kit

**Version:** 1.0 | **Author:** Shaikh Umar| **Status:** Working Prototype  
**Project Codename:** EthicalDRM

A lightweight, pluggable DRM (Digital Rights Management) kit built for independent creators, teachers, and small studios who want to protect their content — ethically and efficiently.

EthicalDRM enables content tracking, piracy deterrence, and watermark-based leak detection proactively monitor the web for leaks, and automatically respond to piracy using Generative AI — without ruining the experience for genuine users.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Status: Beta](https://img.shields.io/badge/status-beta-orange.svg)](https://github.com/Shaik-h-Umar/Ethical-DRM)

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
| ✅ **Invisible Watermarking** | Embeds a unique UserID:Signature:Frame# into images/videos using LSB Steganography | ✅ Done |
| 🛑 **Screen Recording Block** | Detect & block tools like OBS, Snagit, Bandicam (Windows/Mac) | ✅ Done |
| 🖼️ **Web Interface**	   | A polished, drag-and-drop UI (built with Tailwind CSS) for watermarking files | ✅ Done|
| ✅ **Database Logging**  |	All sessions are logged to a persistent SQLite database |  ✅ Done |
| 🧠 **AI Leak Detection** | Scene-matching via perceptual hashing (video/audio) | ✅ Beta |
| � **Leak Traceback** | Pinpoint which user leaked based on watermark or signature | ✅ Done |
| ✅ **History Dashboard** |	A second frontend page that reads the database and displays all watermark history | ✅ Done|
| 🤖 **Leakbot Scanner** | A web scraper (Requests/BS4) that scans a target URL for all media. | ✅ Done |
| ⚙️ **Easy Integration** | Add via Python/JS SDK or REST API in 10 minutes | ✅ Done |
| 🧠 **AI-Powered Response** | Automatically sends the detected User ID to the Google Gemini API to generate a full incident report. | ✅ Done |
| 🌐 **Web Crawler Bot** | Scans public sites, Telegram groups, YouTube, torrents for leaks | 🔄 half done |
| 👥 **User-Friendly** | No forced encryption, easy opt-out for users with older devices | ✅ Done |

## 🚀 The Full Demo
    This project is 100% functional. This demo video shows the complete, end-to-end workflow:

    Protect: A creator uses our web UI to upload a file and watermark it with a unique ID .

    Log: The session is instantly logged to our SQLite database.

    Leak: The watermarked file is "leaked" (uploaded) to a public image-hosting site.

     Monitor: Our app's "Leakbot Dashboard" is given the public URL.

    Detect & Respond: The bot scrapes the page, finds all media, downloads them, and runs our detector. 
    It correctly filters the "garbage" files, finds the real watermark, extracts the  ID, and then        
    automatically calls the Gemini AI to generate a full incident report and DMCA takedown draft, all live in the terminal.

➡️https://drive.google.com/file/d/1UHWGVAk518GfRBLaFKzHJXLOFHymrcmx/view?usp=sharing⬅️

## 🏗️ Architecture


    [ User Browser (Frontend: HTML, Tailwind CSS) ]
      |
      v
    [ Flask Web Server (Waitress) ] <--- [ run.py ]
      |
    ------------------------------------------------------
    |  Web UI (index.html, history.html)                 |
    |  Flask API Endpoints (/watermark, /api/history)    |
    |  Leakbot Scanner Logic (/run-scan, runs in thread) |
    |  Google Gemini API Client                          |
    ------------------------------------------------------
          |                            |
    [ SQLite Database ]         [ Watermarking Engine ]
    (ethicaldrm.db)           (OpenCV, PIL, Hashlib)

## 🚀 Quick Start

### 1. Install SDK

    # Clone the repository
    git clone https://github.com/devils-advocate1/ethicaldrm.git
    cd [PROJECT_FOLDER_NAME]

    # Create a Python virtual environment
     python -m venv venv
    .\venv\Scripts\Activate.ps1

    # Create a .env file in the root directory and add your API key
    GOOGLE_API_KEY=AIzaSy...your_key_here...



    #  Install the project in "editable mode" (this fixes all Python import paths)
        pip install -e .

    #  Install all required libraries
        pip install -r requirements.txt

     # Run the application using the main entry script
     python run.py

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
│   └── app.py           # Flask REST API server
│   └──template
|   |    └──index.html
|   |    └──history.html
|   └──run.py            #starting the server
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

📅 Future Roadmap (The Full Vision)

phase 1: Infrastructure & Bot Scaling
Expand to Telegram & Social Media: Evolve the Leakbot from a simple web scraper into a multi-platform monitor. I will build a dedicated module using Telethon to scan public and private Telegram channels and integrate with the YouTube API to find pirated content.

Distributed Architecture: Re-architect the bot into a distributed, event-driven microservice. This involves using a message queue (like RabbitMQ) to manage scan jobs for a pool of containerized Docker workers, enabling concurrent scanning of thousands of target sites simultaneously.

Phase 2: Advanced Forensic Detection
AI-Powered Perceptual Hashing: Move beyond simple file matching. I will train a custom Computer Vision model (like a Siamese Network). This will allow the bot to find leaked content even if it has been re-compressed, cropped, filtered, or screen-recorded from a phone.

Forensic Audio Watermarking: Expand the service to include spread-spectrum audio watermarking for podcasters and musicians, ensuring that even audio-only rips remain traceable.

Active Screen-Recorder Blocking: Build the planned C++/JavaScript module to proactively detect and block known screen-recording processes (like OBS and ShareX) at the client level, stopping leaks before they even happen.

Phase 3: Fully Automated Response & Analytics
Robo-DMCA (Full Automation): Evolve the "AI Report" into a fully automated takedown system. I will build direct API integrations with major cloud hosts (AWS, Cloudflare, Azure) and content platforms (YouTube, Vimeo) to auto-dispatch DMCA notices the instant a confirmed leak is detected, requiring zero human action.

Viral Leak Analysis (Graph DB): Implement a graph database (like Neo4j) to track the spread of a leak. When the bot finds a leak, it will also trace all outbound links on that page to map its viral spread across the internet, providing creators with a stunning visual dashboard of their content's exposure.

Full SaaS Platform: Launch the entire system as a tiered Software-as-a-Service (SaaS) platform, providing a central dashboard for creators to manage protected assets, view real-time leak analytics, and control their automated security responses.

## 🤝 Contributing

We welcome contributions! To contribute:

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Submit a Pull Request

## 📬 Contact & Support

For support, feedback, or business inquiries:

- 📧 **Email:** shaik.h.umar@gmail.com
- 🌐 **GitHub:** [github.com/Shaik-h-Umar/Ethical-DRM](https://github.com/Shaik-h-Umar/Ethical-DRM)
- 🐦 **Twitter:** [@umar2906](https://twitter.com/@umar2906)

## 🙏 Acknowledgments

- OpenCV team for computer vision tools
- Flask team for the web framework
- All contributors who help make content protection ethical and accessible

---

**Made with ❤️ for indie creators who want to protect their work without punishing their audience.**
