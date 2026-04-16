import os

try:
    from google import genai as google_genai
except ImportError:
    google_genai = None

try:
    import google.generativeai as legacy_genai
except ImportError:
    legacy_genai = None


def generate_dmca_notice(user_id: str) -> str:
    """
    Generate a professional DMCA takedown notice using Google Gemini.

    Args:
        user_id: ID of the user associated with the violating content.

    Returns:
        Generated DMCA notice text as a string.
    """
    # --- API configuration ---
    # Set your key before running:
    # export GEMINI_API_KEY="your_api_key"
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY environment variable.")

    prompt = f"""
Generate an AI incident report in the exact style below.

Output format requirements (must follow this structure exactly):
- Start with: --- BEGIN AI INCIDENT REPORT ---
- Title line: Incident Report: Digital Rights Management Violation
- Include sections in this order:
  1) Date
  2) Subject
  3) File ID
  4) Watermarked File URL (use placeholder if unknown)
  5) Violation
  6) Recommended Action
- End with: --- END AI INCIDENT REPORT ---

Content requirements:
- Responsible user/file ID is: {user_id}
- Tone should be concise, formal, and incident-response style.
- Mention unauthorized public distribution and watermark attribution.
- Recommended action should include DMCA takedown request and follow-up investigation.
- Keep it short and demo-friendly.

If a value is unknown (for example URL), use: N/A
"""

    try:
        if google_genai is not None:
            client = google_genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            text = getattr(response, "text", None)
        elif legacy_genai is not None:
            legacy_genai.configure(api_key=api_key)
            model = legacy_genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            text = getattr(response, "text", None)
        else:
            raise RuntimeError(
                "No supported Gemini SDK found. Install google-genai or google-generativeai."
            )

        # Basic guard in case response structure is empty
        if not text:
            raise RuntimeError("Gemini returned an empty response.")

        # Return only generated notice text
        return text.strip()

    except Exception as e:
        # Basic API error handling for MVP
        raise RuntimeError(f"Failed to generate DMCA notice: {e}")