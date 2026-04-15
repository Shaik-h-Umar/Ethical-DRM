import os
from google import genai


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
    api_key = os.getenv("AIzaSyDUdiO1pH2Ap8PlyKJLym9XDP-Aa8JLz7I") or os.getenv("AIzaSyDUdiO1pH2Ap8PlyKJLym9XDP-Aa8JLz7I")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY environment variable.")

    client = genai.Client(api_key=api_key)

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
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )

        # Basic guard in case response structure is empty
        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("Gemini returned an empty response.")

        # Return only generated notice text
        return text.strip()

    except Exception as e:
        # Basic API error handling for MVP
        raise RuntimeError(f"Failed to generate DMCA notice: {e}")