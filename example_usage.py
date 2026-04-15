from pathlib import Path

from ethical_drm.core.watermark import embed_watermark
from ethical_drm.core.hashing import hash_video
from ethical_drm.core.detector import detect_leak


def main() -> None:
    user_id = "user_123"

    input_video = Path("ethical_drm/storage/original_videos/current_source.mp4")
    watermarked_video = Path("ethical_drm/storage/watermarked_videos/current_output.mp4")
    leaked_video = Path("ethical_drm/storage/simulated_leaks/leaked_scan.mp4")

    # 1) Watermark video
    embed_watermark(str(input_video), str(watermarked_video), user_id)

    # 2) Hash protected video
    hashes = hash_video(str(watermarked_video))

    # 3) Build simple in-memory DB
    database = [{"user_id": user_id, "hashes": hashes}]

    # 4) Detect leak and return responsible user + confidence
    matched_user, confidence = detect_leak(str(leaked_video), database)

    print("Matched user:", matched_user)
    print(f"Confidence: {confidence:.2f}%")


if __name__ == "__main__":
    main()
