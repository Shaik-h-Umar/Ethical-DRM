# demo.py - Your Final Hackathon Submission Script

import numpy as np
import cv2
import os
import time
import openai

# --- IMPORTANT SETUP ---
# Make sure to set your OpenAI API key in your environment variables
# For example: export OPENAI_API_KEY='your-key-here'
# openai.api_key = os.getenv("OPENAI_API_KEY")
# If the above doesn't work, uncomment and paste your key here for the demo:
# openai.api_key = "sk-..."


# Import your Watermarker class
from ethicaldrm.video.watermark import Watermarker

# --- DEMO SCRIPT ---

print("--- ETHICAL DRM HACKATHON DEMO ---")
print("="*40)

# --- Stage 1: Watermarking (In Memory) ---
print("\n[STAGE 1: EMBEDDING]")
print("Initializing the watermarker for 'demo_user__952'...")
user_id = "demo_user_952"
watermarker = Watermarker(user_id=user_id, method="lsb")

print("Creating a sample video frame in memory...")
# Create a single, black video frame (as a numpy array)
sample_frame = np.zeros((480, 640, 3), dtype=np.uint8)
watermark_data_to_embed = f"{watermarker.user_id}:{watermarker.watermark_signature}:0"

print(f"Embedding the following data into the frame:\n  '{watermark_data_to_embed}'")
watermarked_frame = watermarker._embed_lsb_watermark(sample_frame, watermark_data_to_embed)
print("✅ Watermark embedded successfully in memory.")
print("-"*40)

# --- Stage 2: Leak Detection (In Memory) ---
print("\n[STAGE 2: LEAK DETECTION]")
print("Simulating that the watermarked frame has been found on a public site.")
print("Running extraction logic on the frame...")

extracted_data = watermarker._extract_lsb_watermark(watermarked_frame)

if extracted_data:
    print("✅ Watermark extracted successfully!")
    print(f"  - Extracted User ID: {extracted_data.get('user_id')}")
    print(f"  - Extracted Signature: {extracted_data.get('signature')}")
    print("-"*40)

    # --- STAGE 3: AI ANALYSIS & TAKEDOWN DRAFT (using Google Gemini) ---
print("\n[STAGE 3: AI ANALYSIS & TAKEDOWN DRAFT]")
leak_source_url = "https://example-pirate-site.com/leaked-video.avi"

try:
    import google.generativeai as genai

    # --- IMPORTANT SETUP ---
    # Paste the Google AI API Key you created.
    GOOGLE_API_KEY = "AIzaSyAcFSssf-53mVzWHyWgG6yQsCCjkUVjQQg"
    genai.configure(api_key=GOOGLE_API_KEY)

    # Initialize the Gemini Pro model
    # Initialize the Gemini Pro model
    model = genai.GenerativeModel('gemini-1.5-flash-latest') # <-- Use the latest fast model
    
    # --- Part A: AI Incident Report ---
    print("Sending extracted data to Google's Gemini API to generate an incident report...")
    report_prompt = (
        f"You are a digital rights management analyst. A video frame watermarked with the user ID '{extracted_data.get('user_id')}' "
        f"and signature '{extracted_data.get('signature')}' was discovered at the URL: {leak_source_url}. "
        "Generate a concise, professional incident report including the user ID, the potential policy violation, and a recommended action."
    )
    
    report_response = model.generate_content(report_prompt)
    incident_report = report_response.text
    
    print("✅ AI Incident Report Generated:\n")
    print("--- INCIDENT REPORT ---")
    print(incident_report)
    print("-----------------------")

    # --- Part B: AI Takedown Draft ---
    print("\nSending incident report to Gemini API to draft a DMCA takedown notice...")
    takedown_prompt = (
        f"Based on the following incident report, draft a formal but concise DMCA takedown notice addressed to the hosting provider of the website '{leak_source_url}'. "
        "The notice should be firm and request immediate removal of the content.\n\n"
        f"INCIDENT REPORT:\n{incident_report}"
    )

    takedown_response = model.generate_content(takedown_prompt)
    takedown_notice = takedown_response.text

    print("✅ AI Takedown Notice Drafted:\n")
    print("--- DMCA TAKEDOWN DRAFT ---")
    print(takedown_notice)
    print("---------------------------")

except ImportError:
    print("\n❌ ERROR: The 'google-generativeai' library is not installed.")
    print("   Please run: pip install google-generativeai")
except Exception as e:
    print(f"\n❌ ERROR: Could not connect to the Google AI API. Please check your API key.")
    print(f"   Details: {e}")