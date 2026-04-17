# EthicalDRM
### Track Piracy Without Punishing Users

> EthicalDRM is a forensic DRM system that tracks who leaked content and where it spread - without restricting user experience.

EthicalDRM is a Streamlit-based DRM prototype that helps creators trace unauthorized redistribution of media while preserving user freedom.
Instead of blocking access, it focuses on **forensic attribution**, **confidence-based detection**, and **automated legal response drafts**.

Demo Video: [Watch Project Demo](https://drive.google.com/file/d/1_XUQ_5QQgbjEvfCxvM1mFgR9ZbOaDqj_/view?usp=sharing)

---

## 1. Problem Statement

Digital creators lose control of their content once it is redistributed publicly.
Traditional DRM systems attempt to prevent piracy by locking down content - introducing constant verification, access restrictions, and degraded user experience.

However:
- These systems frustrate genuine users
- They still fail to completely stop piracy
- They provide little insight into *who actually leaked the content*

### Why This Matters

- Traditional DRM harms honest users more than pirates
- Creators lack visibility into where leaks spread
- There is no accountability for redistribution

EthicalDRM addresses all three.

---

## 2. Solution Overview

EthicalDRM takes a fundamentally different approach.

Instead of restricting access, it embeds lightweight, invisible watermarks into distributed content.
Each watermark contains a unique user identity, allowing traceability without impacting user experience.

When a leak occurs, the system:
- scans leaked files or URLs
- detects embedded watermark or perceptual match
- identifies the likely source
- assigns a confidence score
- generates an AI-powered DMCA-style report

The same approach works for both **video and image content**.

---

## What Makes EthicalDRM Different?

- No heavy restrictions or forced authentication
- Focus on forensic tracking, not access control
- Confidence-based leak attribution
- Multi-source leak tracking (crawler-assisted)
- AI-powered legal response generation

> We do not prevent piracy - we make it traceable.

---

## 3. Key Features

| Feature | Description | Status |
|---|---|---|
| Video Watermarking | OpenCV-based watermark embedding for distributed copies | Implemented |
| Image Watermarking | Pixel-level watermark embedding for image tracing | Implemented |
| Perceptual Hashing | Robust hash generation for media comparison | Implemented |
| Leak Detection | User/source matching with confidence scoring | Implemented |
| DMCA Report Generation | Gemini-powered AI draft generation with fallback template | Implemented |
| Web Crawler | Lightweight crawler using `requests + BeautifulSoup` | Implemented |
| Public Link Scanning | Extracts media links and verifies leaks | Implemented |
| Multi-Platform Simulation | Simulates Telegram/YouTube/Torrent leak environments | Implemented |
| Telegram Crawling | Direct production crawler using APIs | Conceptual |

---

## Demo Preview

The system demonstrates a complete pipeline:

[Watch Full Demo](https://drive.google.com/file/d/1_XUQ_5QQgbjEvfCxvM1mFgR9ZbOaDqj_/view?usp=sharing)

**Protect -> Leak -> Detect -> Trace -> Respond**

Upload -> Watermark -> Simulate leak -> Scan -> Identify -> Generate report

---

## 4. Demo Workflow (Step-by-Step)

1. Upload original media in the app
2. Apply watermark for a user-specific copy
3. Generate perceptual hashes
4. Simulate or upload leaked content
5. Scan file or URL using crawler
6. Detect source user + confidence score
7. Generate AI DMCA incident report

---

## 5. System Architecture

EthicalDRM uses a modular Streamlit-based architecture:

- **UI Layer**
	- Streamlit (`app.py`)

- **Core Processing**
	- Watermark embedding
	- Perceptual hashing
	- Leak detection
	- Crawler-based scanning

- **AI Layer**
	- DMCA report generation (`dmca_generator.py`)

- **Storage**
	- Original media
	- Watermarked outputs
	- Simulated leaks

---

## 6. Tech Stack

- **Frontend/UI**: Streamlit
- **Media Processing**: OpenCV, Pillow
- **Hashing/Detection**: ImageHash
- **Crawler**: requests, BeautifulSoup
- **AI Integration**: Google Gemini API
- **Language**: Python

---

## 7. Project Structure

```bash
ethical_drm/
├── app.py
├── README.md
├── requirements.txt
├── core/
│   ├── watermark.py
│   ├── image_watermark.py
│   ├── hashing.py
│   ├── detector.py
│   ├── crawler.py
│   └── utils.py
├── ai/
│   └── dmca_generator.py
├── database/
│   └── db.py
└── storage/
		├── original_videos/
		├── watermarked_videos/
		└── simulated_leaks/
```

---

## 8. How It Works (Pipeline)

### Media Protection
- Content is uploaded and watermarked per user
- Fingerprints (hashes) are generated

### Leak Detection
- Leaked content is scanned
- Hashes compared with stored fingerprints
- Output:
	- User ID
	- Confidence score

### Legal Response
- AI generates DMCA-style report
- Fallback template ensures reliability

---

## 9. Crawler Explanation (Important)

EthicalDRM includes a lightweight crawler:

- Crawls public webpages
- Extracts media links (`.mp4`, `.jpg`, `.png`)
- Downloads limited files
- Runs detection pipeline

Example output:

```json
{
	"platform": "Web",
	"url": "https://example.com/video",
	"user": "user_123",
	"confidence": 87.5
}
```

### Notes

- Built using `requests + BeautifulSoup`
- Optimized for demo reliability
- Designed as a scalable base for future crawlers

Telegram crawling is currently conceptual (API-based extension planned)

---

## 10. AI Integration (DMCA Generation)

- Uses Gemini API
- Generates incident-style reports
- Includes fallback system if API fails

---

## 11. Installation & Setup

```bash
git clone <your-repo-url>
cd Ethical\ DRM

python -m venv .venv
source .venv/bin/activate

pip install -r ethical_drm/requirements.txt
```

### Optional (AI)

```bash
export GEMINI_API_KEY="your_api_key"
```

---

## 12. Usage

```bash
streamlit run ethical_drm/app.py
```

Steps:

1. Protect media
2. Simulate/upload leak
3. Scan (file or URL)
4. Detect source
5. Generate report

---

## 13. Example Demo Flow

1. Upload `original.mp4`
2. Watermark for `user_007`
3. Simulate leak
4. Scan URL
5. View:
	 - Platform
	 - Confidence
	 - User
6. Generate report

---

## Current Limitations

- Crawler works on public pages only
- Telegram integration is conceptual
- Confidence is heuristic-based

---

## 14. Future Scope

- Full Telegram crawler (API-based)
- Advanced detection (ML-based)
- Batch scanning system
- Analytics dashboard
- SaaS platform

---

## 15. Ethical Philosophy

> **Accountability over control.**

- No harsh restrictions
- No degraded experience
- Focus on traceability

---

## 16. Contributing

```bash
git checkout -b feature/your-feature
git commit -m "feat: ..."
git push origin feature/your-feature
```

---

## 17. Contact

- Maintainer: Shaikh Umar
- GitHub: [https://github.com/Shaik-h-Umar/Ethical-DRM](https://github.com/Shaik-h-Umar/Ethical-DRM)

---

## 18. License

Use MIT / Apache-2.0 before production deployment.
