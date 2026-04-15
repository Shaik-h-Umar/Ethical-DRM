import os
import shutil
import subprocess

import cv2


def probe_video(video_path: str) -> tuple[bool, dict]:
    """Quick integrity probe: can OpenCV open and decode at least one frame?"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return False, {"error": "cannot_open"}

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    ret, frame = cap.read()
    cap.release()

    ok = ret and frame is not None and width > 0 and height > 0
    return ok, {
        "fps": fps,
        "width": width,
        "height": height,
        "frame_count": frame_count,
        "first_frame_ok": bool(ret and frame is not None),
    }


def embed_watermark(input_path: str, output_path: str, user_id: str) -> str:
    cap = cv2.VideoCapture(input_path)

    if not cap.isOpened():
        raise Exception("Error opening video")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"[DEBUG] Input metadata: fps={fps}, width={width}, height={height}, frame_count={frame_count}")

    # FORCE SAFE FPS
    if fps <= 0:
        fps = 24

    if width <= 0 or height <= 0:
        cap.release()
        raise ValueError("Invalid input resolution")

    # Write an intermediate MP4 first; we may transcode to H.264 after writing.
    raw_output_path = f"{output_path}.raw.mp4"

    # Browser/Streamlit-friendly fallback codec when ffmpeg is unavailable.
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(raw_output_path, fourcc, fps, (width, height))
    if not out.isOpened():
        cap.release()
        raise RuntimeError(f"Cannot open output writer: {raw_output_path}")

    overlay_alpha = 0.1  # LOW OPACITY
    written_frames = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame is None:
            continue

        # Add subtle watermark overlay.
        overlay = frame.copy()
        cv2.putText(
            overlay,
            f"{user_id}",
            (width - 200, height - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        frame = cv2.addWeighted(overlay, overlay_alpha, frame, 1 - overlay_alpha, 0)

        out.write(frame)
        written_frames += 1

    cap.release()
    out.release()

    # Prefer H.264 output for browser playback if ffmpeg is available.
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        command = [
            ffmpeg_path,
            "-y",
            "-i",
            raw_output_path,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            output_path,
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0 and os.path.exists(output_path):
            os.remove(raw_output_path)
        else:
            if os.path.exists(output_path):
                os.remove(output_path)
            os.replace(raw_output_path, output_path)
    else:
        os.replace(raw_output_path, output_path)

    exists = os.path.exists(output_path)
    size = os.path.getsize(output_path) if exists else 0
    print(f"[DEBUG] Output path: {output_path}")
    print(f"[DEBUG] Output exists: {exists}")
    print(f"[DEBUG] Output file size: {size}")
    print(f"[DEBUG] Frames written: {written_frames}")

    if not exists or size <= 0 or written_frames == 0:
        raise RuntimeError("Watermark output is empty or invalid")

    valid, meta = probe_video(output_path)
    print(f"[DEBUG] Output probe: {meta}")
    if not valid:
        raise RuntimeError("Output video probe failed")

    print("Saved:", output_path)

    return output_path