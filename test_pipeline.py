from pathlib import Path
import shutil

import cv2
import numpy as np

from ethical_drm.core import watermark, hashing, detector
from ethical_drm.ai import dmca_generator


def print_step(step_no: int, message: str) -> None:
	print(f"\n[{step_no}] {message}")


def build_fallback_dmca_notice(user_id: str) -> str:
	return f"""Subject: DMCA Takedown Notice - Unauthorized Distribution (User ID: {user_id})

To Whom It May Concern,

I am writing to report unauthorized distribution of copyrighted content associated with user ID {user_id}.
This content is being shared without permission and constitutes copyright infringement.

Please remove or disable access to the infringing material immediately.

I have a good-faith belief that the use of the copyrighted material described above is not authorized by
the copyright owner, its agent, or the law. I swear, under penalty of perjury, that the information in
this notice is accurate and that I am authorized to act on behalf of the copyright owner.

Sincerely,
EthicalDRM Demo Team
"""


def create_sample_video(sample_path: Path) -> None:
	"""Create a tiny sample video so the pipeline is runnable out-of-the-box."""
	sample_path.parent.mkdir(parents=True, exist_ok=True)

	fps = 24
	width, height = 640, 360
	duration_seconds = 3
	total_frames = fps * duration_seconds

	fourcc = cv2.VideoWriter_fourcc(*"mp4v")
	writer = cv2.VideoWriter(str(sample_path), fourcc, fps, (width, height))
	if not writer.isOpened():
		raise RuntimeError(f"Could not create sample video at: {sample_path}")

	try:
		for i in range(total_frames):
			frame = np.zeros((height, width, 3), dtype=np.uint8)
			frame[:] = (20, 40, 70)

			x = 30 + (i * 6) % (width - 120)
			cv2.rectangle(frame, (x, 90), (x + 90, 200), (40, 190, 250), -1)
			cv2.putText(
				frame,
				"EthicalDRM Demo",
				(20, 40),
				cv2.FONT_HERSHEY_SIMPLEX,
				1,
				(255, 255, 255),
				2,
				cv2.LINE_AA,
			)
			cv2.putText(
				frame,
				f"Frame {i + 1}",
				(20, height - 20),
				cv2.FONT_HERSHEY_SIMPLEX,
				0.7,
				(200, 220, 255),
				2,
				cv2.LINE_AA,
			)
			writer.write(frame)
	finally:
		writer.release()


def main() -> None:
	base_dir = Path("ethical_drm") / "storage"
	original_dir = base_dir / "original_videos"
	watermarked_dir = base_dir / "watermarked_videos"
	leaks_dir = base_dir / "simulated_leaks"

	original_dir.mkdir(parents=True, exist_ok=True)
	watermarked_dir.mkdir(parents=True, exist_ok=True)
	leaks_dir.mkdir(parents=True, exist_ok=True)

	user_id = "user_007"
	sample_input = original_dir / "sample_input.mp4"
	watermarked_output = watermarked_dir / f"watermarked_{user_id}.mp4"
	leaked_copy = leaks_dir / "leaked_video.mp4"

	print("=== EthicalDRM Hackathon Test Pipeline ===")

	# 1 + 2: import modules and prepare sample input video
	print_step(1, "Importing watermark, hashing, detector, and AI DMCA modules")
	print("Modules loaded successfully.")

	print_step(2, "Preparing sample video input")
	if not sample_input.exists():
		create_sample_video(sample_input)
		print(f"Created sample video: {sample_input}")
	else:
		print(f"Using existing sample video: {sample_input}")

	# 3: apply watermark
	print_step(3, f"Applying watermark with user_id='{user_id}'")
	result_path = watermark.embed_watermark(str(sample_input), str(watermarked_output), user_id)
	print(f"Watermarked video saved: {result_path}")

	# 4: hash + fake DB
	print_step(4, "Generating hashes and storing in fake database")
	hashes = hashing.get_video_hashes(str(watermarked_output))
	fake_database = [{"user_id": user_id, "hashes": hashes}]
	print(f"Generated {len(hashes)} hashes for {user_id}")
	print(f"Fake DB records: {len(fake_database)}")

	# 5: simulate leak
	print_step(5, "Simulating leak using the same watermarked video")
	shutil.copy2(watermarked_output, leaked_copy)
	print(f"Leaked file simulated at: {leaked_copy}")

	# 6: detect leak
	print_step(6, "Detecting leaked video and identifying user")
	detected_user = detector.detect_leak(str(leaked_copy), fake_database)
	if detected_user:
		print(f"Detected responsible user: {detected_user}")
	else:
		print("No user detected from leaked video.")

	# 7: generate DMCA notice
	print_step(7, "Generating DMCA notice for detected user")
	if detected_user:
		try:
			dmca_text = dmca_generator.generate_dmca_notice(detected_user)
			print("Generated DMCA notice using AI module.")
		except Exception as exc:
			print(f"AI DMCA generation failed ({exc}). Using fallback template.")
			dmca_text = build_fallback_dmca_notice(detected_user)
		print("\n--- DMCA NOTICE ---")
		print(dmca_text)
		print("--- END NOTICE ---")
	else:
		print("Skipped DMCA generation because no user was detected.")

	# 8: clear finish message
	print_step(8, "Pipeline complete")
	print("Demo finished successfully.")


if __name__ == "__main__":
	main()
