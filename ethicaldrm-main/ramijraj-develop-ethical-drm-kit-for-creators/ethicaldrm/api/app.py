"""
Flask REST API for EthicalDRM
Provides HTTP endpoints for a web-based watermarking demo and includes
the structure for future features like leak detection and screen monitoring.
"""

import os
import sqlite3
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import google.generativeai as genai
import requests
import threading
import tempfile
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from flask import Flask, jsonify, request, render_template, send_from_directory, current_app
from ethicaldrm.video.watermark import Watermarker
from PIL import Image
import cv2

# --- Logger Setup ---
logger = logging.getLogger(__name__)
# (Code starting on line 27)

# --- Database Helper ---
# This function is defined first so it can be called correctly during app creation.
def init_database(app):
    """Initializes the SQLite database and creates tables if they don't exist."""
    with sqlite3.connect(app.config['DATABASE']) as conn:
        cursor = conn.cursor()
        
        # This table supports all necessary logging for the working demo.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watermark_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                input_file TEXT,
                output_file TEXT NOT NULL,
                watermark_signature TEXT,
                method TEXT,
                status TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                file_size INTEGER,
                total_frames INTEGER,
                watermarked_frames INTEGER,
                metadata TEXT
            )
        ''')
        
        # --- FIX ---
        # The schemas for your future features are kept to show your full vision.
        # A simple 'id' column is used to prevent any SQL syntax errors during the demo.
        cursor.execute('''CREATE TABLE IF NOT EXISTS leak_detections (id INTEGER PRIMARY KEY)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS recording_events (id INTEGER PRIMARY KEY)''')
        # --- END FIX ---
        
        conn.commit()
    print("✅ Database initialized successfully.")

# (Code starting on line 66)

def generate_ai_report(user_id, leak_url):
    """
    Calls the Gemini API to generate a professional incident report.
    """
    model = current_app.gemini_model
    if not model:
        return "Gemini model not initialized. Report generation failed."

    print(f"[Leakbot] Calling Gemini 1.5 Flash for user '{user_id}'...")
    
    prompt_content = (
        f"You are a digital rights management analyst. A file watermarked with the ID '{user_id}' "
        f"was discovered and automatically downloaded from the following URL: {leak_url}. "
        "Generate a concise, professional incident report including the user ID, the violation, "
        "and a recommended action (like drafting a DMCA notice)."
    )

    try:
        response = model.generate_content(prompt_content)
        return response.text
    except Exception as e:
        print(f"[Leakbot] Error connecting to Gemini API: {e}")
        return f"Error connecting to Gemini API: {e}"

def scan_page_internal(target_url, app):
    """
    This is the core LEAKBOT logic. It now correctly handles both images and videos.
    """
    print(f"\n--- [Leakbot] Starting Background Scan on: {target_url} ---")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        response = requests.get(target_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[Leakbot] Failed to fetch URL: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    media_links = set()
    
    # Find images and media links
    for img_tag in soup.find_all('img'):
        if src := img_tag.get('src'):
            media_links.add(urljoin(target_url, src))
            
    for a_tag in soup.find_all('a'):
        if href := a_tag.get('href'):
            if any(href.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.mp4', '.avi']):
                media_links.add(urljoin(target_url, href))

    if not media_links:
        print("[Leakbot] No media files found on this page.")
        return

    print(f"[Leakbot] Found {len(media_links)} potential files. Scanning...")

    # We only need one instance of the Watermarker class for all detections
    detector = Watermarker(user_id="leak_detector_instance")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        for link in media_links:
            try:
                parsed_link = urlparse(link)
                filename = os.path.basename(parsed_link.path)
                if not filename: continue

                print(f"[Leakbot] Scanning file: {link}")
                media_response = requests.get(link, headers=headers, timeout=10, stream=True)
                media_response.raise_for_status()
                
                temp_filepath = os.path.join(tmpdir, filename)
                with open(temp_filepath, 'wb') as f:
                    for chunk in media_response.iter_content(chunk_size=8192):
                        f.write(chunk)

                # --- NEW DETECTION LOGIC ---
                file_ext = os.path.splitext(filename)[1].lower()
                image_extensions = ['.png', '.jpg', '.jpeg', '.bmp']
                watermark_info = None

                if file_ext in image_extensions:
                    # It's an image: read the frame and call the LSB extractor
                    frame = cv2.imread(temp_filepath)
                    if frame is not None:
                        watermark_info = detector._extract_lsb_watermark(frame)
                else:
                    # Assume it's a video: call the public video extractor
                    watermark_info = detector.extract_watermark(temp_filepath)
                # --- END NEW LOGIC ---
                
                if watermark_info and watermark_info.get('user_id'):
                    user_id = watermark_info['user_id']
                    print(f"!!!!!!!!!!!!!! [Leakbot] LEAK DETECTED !!!!!!!!!!!!!!")
                    print(f"  File: {link}")
                    print(f"  Source User ID: {user_id}")
                    
                    with app.app_context():
                       # This context makes 'current_app' (used by the AI function) work inside the thread
                        report = generate_ai_report(user_id, link)
                    print("\n--- BEGIN AI INCIDENT REPORT ---")
                    print(report)
                    print("--- END AI INCIDENT REPORT ---\n")
                else:
                    print(f"[Leakbot] File scanned. No watermark found.")

            except Exception as e:
                print(f"[Leakbot] Could not scan file {link}. Error: {e}")
                
    print(f"--- [Leakbot] Scan Complete for {target_url} ---")

# (This code ends, and the next line should be line 68: def create_app(...):)
# --- Application Factory ---
def create_app(config: Optional[Dict[str, Any]] = None) -> Flask:
    """
    This is the main Application Factory. It creates, configures,
    and returns the Flask application instance.
    """
    
    app = Flask(__name__, template_folder='templates')

    # --- Configuration ---
    base_dir = os.path.dirname(__file__)
    app.config.update({
        'DATABASE': os.path.join(base_dir, 'ethicaldrm.db'),
        'UPLOAD_FOLDER': os.path.join(base_dir, 'uploads'),
        'OUTPUT_FOLDER': os.path.join(base_dir, 'outputs'),
        'MAX_CONTENT_LENGTH': 500 * 1024 * 1024,
        'SECRET_KEY': 'a-strong-secret-key-for-production'
    })

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
# --- Initialize Gemini Client ---
    # We do this INSIDE the factory so it runs AFTER load_dotenv
    # and has access to the environment variables.
    try:
        GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY') # This is the correct way
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable not found.")
        
        genai.configure(api_key=GOOGLE_API_KEY)
        # IMPORTANT: We attach the model to the Flask 'app' object
        app.gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest') 
        print("✅ Gemini client initialized successfully.")
    except Exception as e:
        print(f"Error initializing Gemini: {e}")
        # Also attach None to the app object on failure
        app.gemini_model = None
    # Initialize the database when the app starts
    with app.app_context():
        init_database(app)

    # --- Main Routes ---

    @app.route("/")
    def index():
        """Serves the main frontend user interface."""
        return render_template("index.html")

    @app.route("/watermark/embed", methods=['POST'])
    def embed_watermark():
        """Handles file upload, calls the watermarking engine, and logs the result."""
        try:
            user_id = request.form.get('user_id')
            method = request.form.get('method', 'lsb')
            strength = float(request.form.get('strength', 0.1))
            
            if 'file' not in request.files or not user_id or not request.files['file'].filename:
                return jsonify({'error': 'User ID and a selected file are required'}), 400

            file = request.files['file']
            
            base_name, input_ext = os.path.splitext(file.filename)
            unique_filename = f"{base_name}_{int(time.time())}{input_ext}"
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(input_path)

            image_extensions = ['.png', '.jpg', '.jpeg', '.bmp']
            output_ext = '.png' if input_ext.lower() in image_extensions else '.avi'
            output_filename = f"{base_name}_{int(time.time())}_watermarked{output_ext}"
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

            watermarker = Watermarker(user_id, method, strength)
            result = watermarker.embed(input_path, output_path)

            if result.get('success'):
                with sqlite3.connect(app.config['DATABASE']) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO watermark_sessions (user_id, input_file, output_file, watermark_signature, method, status, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (user_id, unique_filename, output_filename, result.get('signature'), method, 'completed', json.dumps(result))
                    )
                    conn.commit()
                
                result['download_url'] = f'/download/{output_filename}'
                return jsonify(result)
            else:
                return jsonify({'error': result.get('error', 'Watermarking failed')}), 500
                
        except Exception as e:
            logger.error(f"Watermark embedding failed: {str(e)}")
            return jsonify({'error': str(e)}), 500

    # In api/app.py, find and replace the history() function

    @app.route("/history")
    def history_page():
        """Serves the main history.html page."""
        return render_template("history.html")

    @app.route("/api/history")
    def history_api():
        """This is the new API endpoint that the webpage will call."""
        with sqlite3.connect(app.config['DATABASE']) as conn:
            conn.row_factory = sqlite3.Row
            sessions = conn.execute('SELECT id, user_id, output_file, watermark_signature, timestamp FROM watermark_sessions ORDER BY timestamp DESC LIMIT 50').fetchall()
            return jsonify([dict(session) for session in sessions])
    

    @app.route('/download/<filename>')
    def download_file(filename):
        """Allows users to download their watermarked files."""
        return send_from_directory(app.config["OUTPUT_FOLDER"], filename, as_attachment=True)
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({'error': 'An internal server error occurred'}), 500
    
    # (Code starting on line 189)

    @app.route('/run-scan', methods=['POST'])
    def run_scan_endpoint():
        """
        Triggers the leakbot scan in a new thread.
        Returns an immediate response so the browser doesn't time out.
        """
        url_to_scan = request.json.get('url')
        if not url_to_scan:
            return jsonify({"error": "No URL provided"}), 400

        # Run the scan in a background thread so the browser doesn't time out.
        # We must pass the REAL app object (not the proxy 'current_app') to the new thread
        real_app = current_app._get_current_object()
        scan_thread = threading.Thread(target=scan_page_internal, args=(url_to_scan, real_app))
        scan_thread.start()
        
        print(f"Scan thread started for {url_to_scan}.")
        return jsonify({"message": f"Scan started for {url_to_scan}. Check your terminal for results."})

# (This new code ends, and the next lines should be line 190: logger.info(...),
#  and line 192: return app)

    logger.info("✅ EthicalDRM API initialized successfully")
    
    return app



