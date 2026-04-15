import cv2
from PIL import Image
import imagehash


def hash_video(video_path: str) -> list:
    """
    Generate perceptual hashes from a video by sampling every 30th frame.

    Args:
        video_path: Path to input video.

    Returns:
        List of perceptual hash strings (hex format).

    Raises:
        FileNotFoundError: If video cannot be opened.
    """
    sample_every_n = 30

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video_path}")

    hashes = []
    frame_idx = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % sample_every_n == 0:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)
                ph = imagehash.phash(pil_img)
                hashes.append(str(ph))

            frame_idx += 1

    finally:
        cap.release()

    return hashes


def get_video_hashes(video_path: str) -> list:
    """Backward-compatible alias used by existing app code."""
    return hash_video(video_path)