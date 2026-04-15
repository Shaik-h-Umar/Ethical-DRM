from pathlib import Path
import os
import uuid
from uuid import uuid4

import streamlit as st

from ai.dmca_generator import generate_dmca_notice
from core import detector, hashing, watermark


APP_TITLE = "EthicalDRM"


def base_storage_dir() -> Path:
	return Path(__file__).resolve().parent / "storage"


def init_state() -> None:
	if "user_id" not in st.session_state:
		st.session_state.user_id = f"User_{str(uuid4())[:6].upper()}"
	if "fake_db" not in st.session_state:
		st.session_state.fake_db = []
	if "protected_video_path" not in st.session_state:
		st.session_state.protected_video_path = None
	if "source_video_path" not in st.session_state:
		st.session_state.source_video_path = None
	if "source_upload_token" not in st.session_state:
		st.session_state.source_upload_token = None
	if "detected_user" not in st.session_state:
		st.session_state.detected_user = None
	if "confidence" not in st.session_state:
		st.session_state.confidence = 0.0
	if "dmca_notice" not in st.session_state:
		st.session_state.dmca_notice = ""


def ensure_storage_dirs() -> dict:
	storage = base_storage_dir()
	dirs = {
		"original": storage / "original_videos",
		"watermarked": storage / "watermarked_videos",
		"leaks": storage / "simulated_leaks",
	}
	for path in dirs.values():
		path.mkdir(parents=True, exist_ok=True)
	return dirs


def inject_styles() -> None:
	st.markdown(
		"""
		<style>
		.stApp {
			background: radial-gradient(circle at 10% 20%, #11273b 0%, #0b1422 55%, #05090f 100%);
			color: #e8f6ff;
		}
		.block-container {
			max-width: 1200px;
			padding-top: 1rem;
			padding-bottom: 2rem;
		}
		.panel {
			background: linear-gradient(135deg, rgba(20, 31, 49, 0.95), rgba(8, 16, 28, 0.92));
			border: 1px solid rgba(98, 180, 255, 0.22);
			border-radius: 14px;
			padding: 16px;
			box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
			margin-bottom: 12px;
		}
		.panel h4 {
			margin: 0 0 8px 0;
			color: #a8e3ff;
		}
		.small-muted {
			color: #9bc3dc;
			font-size: 0.9rem;
			opacity: 0.9;
		}
		.header-card {
			background: linear-gradient(90deg, rgba(21,35,56,0.95), rgba(15,55,88,0.85));
			border: 1px solid rgba(118, 208, 255, 0.35);
			border-radius: 14px;
			padding: 16px;
			margin-bottom: 12px;
		}
		.badge {
			display: inline-block;
			padding: 6px 12px;
			border-radius: 999px;
			font-size: 0.8rem;
			background: rgba(30, 164, 110, 0.25);
			border: 1px solid rgba(75, 255, 175, 0.5);
			color: #8fffc2;
			font-weight: 600;
		}
		.flow-step {
			background: rgba(22, 53, 83, 0.85);
			border: 1px solid rgba(105, 190, 255, 0.4);
			border-radius: 12px;
			padding: 10px;
			text-align: center;
			font-weight: 600;
			margin-bottom: 10px;
		}
		.notice-box {
			background: rgba(11, 29, 44, 0.9);
			border: 1px solid rgba(93, 181, 255, 0.3);
			border-radius: 10px;
			padding: 14px;
			white-space: pre-wrap;
			color: #dceffd;
			line-height: 1.45;
		}
		</style>
		""",
		unsafe_allow_html=True,
	)


def render_sidebar() -> str:
	st.sidebar.title(APP_TITLE)
	st.sidebar.caption("Hackathon Demo Flow")
	nav = st.sidebar.radio(
		"Navigation",
		options=["Dashboard", "Protect Video", "Leak Detection", "Reports (DMCA)", "Image DRM", "Logout"],
	)
	st.sidebar.markdown("---")
	st.sidebar.success("Monitoring Enabled")
	return nav


def render_top_header() -> None:
	user_id = st.session_state.user_id
	st.markdown(
		f"""
		<div class=\"header-card\">
			<h2 style=\"margin:0;\">Welcome, {user_id}</h2>
			<div class=\"small-muted\" style=\"margin-top:6px;\">Every distributed copy is uniquely traceable.</div>
		</div>
		""",
		unsafe_allow_html=True,
	)
	right_col = st.columns([4, 1])
	with right_col[1]:
		st.markdown('<span class="badge">Protected</span>', unsafe_allow_html=True)


def render_step_flow() -> None:
	st.subheader("Step Flow")
	cols = st.columns(4)
	steps = ["1. Upload", "2. Protect", "3. Detect", "4. Report"]
	for col, step in zip(cols, steps):
		with col:
			st.markdown(f'<div class="flow-step">{step}</div>', unsafe_allow_html=True)


def save_uploaded_file(uploaded_file, path: Path) -> Path:
	path.parent.mkdir(parents=True, exist_ok=True)
	with open(path, "wb") as file_obj:
		file_obj.write(uploaded_file.getbuffer())
	print(f"[DEBUG] Saved upload path: {path}")
	print(f"[DEBUG] Saved upload exists: {os.path.exists(path)}")
	return path


def load_video_bytes(path: str | Path) -> bytes:
	with open(path, "rb") as file_obj:
		return file_obj.read()


def calculate_confidence(leaked_hashes: list, db: list) -> tuple[float, str | None]:
	leaked_set = set(leaked_hashes)
	if not leaked_set or not db:
		return 0.0, None
    #if not leaked_set or not db: return 0 confidence and no user if we have no hashes or an empty database to compare against. This is a safeguard against division by zero and indicates that we cannot make any meaningful attribution without data.
	best_user = None
	best_ratio = 0.0
	for record in db:
		stored = set(record.get("hashes", []))
		if not stored:
			continue
		overlap = len(leaked_set.intersection(stored))
		ratio = overlap / max(len(leaked_set), 1)
		if ratio > best_ratio:
			best_ratio = ratio
			best_user = record.get("user_id")

	return best_ratio, best_user


def fallback_notice(user_id: str) -> str:
	return (
		"--- BEGIN AI INCIDENT REPORT ---\n"
		"Incident Report: Digital Rights Management Violation\n\n"
		"Date: N/A\n\n"
		"Subject: Unauthorized Access and Distribution of Watermarked File\n\n"
		f"File ID: {user_id}\n\n"
		"Watermarked File URL: N/A\n\n"
		f"Violation: Unauthorized distribution of a copyrighted file linked to user {user_id} "
		"has been detected via watermark attribution.\n\n"
		"Recommended Action: Draft and issue a DMCA takedown notice to the hosting platform, "
		"request immediate removal of infringing content, and initiate follow-up source investigation.\n\n"
		"--- END AI INCIDENT REPORT ---"
	)


def section_protect(dirs: dict) -> None:
	st.subheader("Protect Content")

	uploaded_file = st.file_uploader("Upload Video", type=["mp4"])
	source_path = dirs["original"] / "current_source.mp4"
	output_path = dirs["watermarked"] / "current_output.mp4"

	if uploaded_file:
		if os.path.exists(source_path):
			os.remove(source_path)

		with open(source_path, "wb") as f:
			f.write(uploaded_file.getbuffer())

		st.session_state.saved_source = str(source_path)
		st.session_state.source_video_path = str(source_path)
		st.session_state.protected_video = None
		st.session_state.protected_video_path = None

		st.success("Video uploaded")

	if st.button("Apply Protection"):
		if "saved_source" not in st.session_state:
			st.error("Upload video first")
		else:
			try:
				if os.path.exists(output_path):
					os.remove(output_path)

				watermark.embed_watermark(st.session_state.saved_source, str(output_path), st.session_state.user_id)
				valid_output, meta = watermark.probe_video(str(output_path))
				if not valid_output:
					raise RuntimeError(f"Output validation failed: {meta}")

				st.session_state.protected_video = str(output_path)
				st.session_state.protected_video_path = str(output_path)

				hashes = hashing.get_video_hashes(str(output_path))
				st.session_state.fake_db = [
					{"user_id": st.session_state.user_id, "hashes": hashes}
				]

				file_size = os.path.getsize(output_path)
				st.success(f"Watermark applied. Output ready: current_output.mp4 ({file_size} bytes)")
			except Exception as exc:
				st.error(f"Protection failed: {exc}")

	# ONLY ONE VIDEO PLAYER (CRITICAL)
	if "protected_video" in st.session_state and st.session_state.protected_video:
		path = st.session_state.protected_video

		if os.path.exists(path):
			st.video(path)
			video_bytes = load_video_bytes(path)
			st.download_button(
				label="Download Watermarked Video",
				data=video_bytes,
				file_name="current_output.mp4",
				mime="video/mp4",
				use_container_width=True,
			)
		else:
			st.error("Video not found")
	else:
		st.info("Apply protection to generate a watermarked file.")


def section_detect(dirs: dict) -> None:
	st.markdown('<div class="panel">', unsafe_allow_html=True)
	st.subheader("Section 2: Leak Detection")
	st.caption("Upload a leaked clip and scan for hidden watermark traces.")

	col1, col2 = st.columns([1, 1.2])
	with col1:
		leaked_file = st.file_uploader(
			"Upload leaked video",
			type=["mp4", "mov", "mkv"],
			key="leak_upload",
		)

		if st.button("Scan Leak", use_container_width=True):
			if not leaked_file:
				st.error("Please upload a leaked video first.")
			elif not st.session_state.fake_db:
				st.error("No protected asset found. Run Section 1 first.")
			else:
				leaked_path = dirs["leaks"] / "leaked_scan.mp4"
				save_uploaded_file(leaked_file, leaked_path)

				try:
					detected, detector_confidence = detector.detect_leak(str(leaked_path), st.session_state.fake_db)
					leaked_hashes = detector.get_video_hashes(str(leaked_path))
					confidence, best_user = calculate_confidence(leaked_hashes, st.session_state.fake_db)
                    #thet thing which we are doing is we are calculating the confidence score based on the overlap of hashes between the leaked video and the database records. The confidence score is a ratio of matching hashes to total hashes, giving us an estimate of how likely it is that the leaked video belongs to a specific user in our database. We also identify the best matching user based on the highest confidence score.
					st.session_state.detected_user = detected or best_user
					st.session_state.confidence = max(confidence, detector_confidence / 100)

					if st.session_state.detected_user:
						st.success("Leak Detected")
					else:
						st.warning("No Leak Detected")
				except Exception as exc:
					st.error(f"Detection failed: {exc}")

	with col2:
		leak_found = bool(st.session_state.detected_user)
		status_text = "Leak Detected" if leak_found else "No Leak"
		st.markdown(f"### {status_text}")
		st.text_input("Responsible User ID", value=st.session_state.detected_user or "-", disabled=True)
		st.text_input("Leak Source", value="leaked_scan.mp4" if leak_found else "-", disabled=True)

		confidence_percent = int(st.session_state.confidence * 100)
		st.write(f"Confidence score: {confidence_percent}%")
		st.progress(confidence_percent)

	st.markdown('</div>', unsafe_allow_html=True)


def section_report() -> None:
	st.markdown('<div class="panel">', unsafe_allow_html=True)
	st.subheader("Section 3: DMCA Report")
	st.caption("Generate a legal action notice from detected watermark evidence.")

	if st.button("Generate Report"):
		if not st.session_state.detected_user:
			st.error("No detected user found. Run leak detection first.")
		else:
			try:
				st.session_state.dmca_notice = generate_dmca_notice(st.session_state.detected_user)
				st.success("DMCA notice generated using AI.")
			except Exception:
				st.session_state.dmca_notice = fallback_notice(st.session_state.detected_user)
				st.warning("AI notice unavailable. Fallback legal notice generated.")

	notice = st.session_state.dmca_notice or "No report generated yet."
	st.markdown(f'<div class="notice-box">{notice}</div>', unsafe_allow_html=True)

	c1, c2 = st.columns(2)
	with c1:
		if st.button("Copy"):
			st.info("Notice ready. Select text and copy.")
	with c2:
		st.download_button(
			label="Download",
			data=notice,
			file_name=f"dmca_notice_{st.session_state.user_id}.txt",
			mime="text/plain",
			use_container_width=True,
		)

	st.markdown('</div>', unsafe_allow_html=True)


def section_image_protect() -> None:
	st.header("Image Protection")

	img_file = st.file_uploader("Upload Image", type=["jpg", "png"], key="img_upload")

	if img_file:
		path = "image_input.png"
		with open(path, "wb") as f:
			f.write(img_file.getbuffer())

		st.image(path)

		if st.button("Apply Image Protection"):
			from core.image_watermark import embed_image_watermark

			out = "image_output.png"
			embed_image_watermark(path, out, st.session_state.user_id)

			st.session_state.img_output = out
			st.success("Image Protected")

	if "img_output" in st.session_state:
		st.image(st.session_state.img_output)
		with open(st.session_state.img_output, "rb") as f:
			st.download_button(
				label="Download Watermarked Image",
				data=f.read(),
				file_name="watermarked_image.png",
				mime="image/png",
				use_container_width=True,
			)


def section_image_detect() -> None:
	st.header("Image Leak Detection")

	leak_img = st.file_uploader("Upload Leaked Image", type=["jpg", "png"], key="img_leak")

	if leak_img:
		path = "leak.png"
		with open(path, "wb") as f:
			f.write(leak_img.getbuffer())

		if st.button("Scan Image"):
			from core.image_watermark import extract_image_watermark

			user = extract_image_watermark(path)
			st.success(f"Leak Detected: {user}")


def section_image_report() -> None:
	st.markdown("---")
	st.subheader("Generate DMCA Report (Image)")

	if st.button("Generate Image DMCA Report"):
		try:
			user = st.session_state.user_id
			notice = generate_dmca_notice(user)
			st.session_state.image_dmca = notice
		except Exception:
			st.session_state.image_dmca = f"""
NOTICE OF COPYRIGHT INFRINGEMENT (DMCA)

This notice is regarding unauthorized distribution of protected image content.

Detected User ID: {st.session_state.user_id}

The image contains an embedded forensic watermark identifying the responsible user.

Action Requested:
- Immediate removal of the infringing content
- Investigation of the source

"""

	if "image_dmca" in st.session_state:
		st.text_area("DMCA Notice", st.session_state.image_dmca, height=300)

		st.download_button(
			label="Download Report",
			data=st.session_state.image_dmca,
			file_name="image_dmca.txt",
			mime="text/plain",
		)


def render_dashboard(dirs: dict) -> None:
	render_top_header()
	render_step_flow()
	section_protect(dirs)
	section_detect(dirs)
	section_report()


def main() -> None:
	st.set_page_config(page_title=APP_TITLE, page_icon="DRM", layout="wide")
	inject_styles()
	init_state()
	dirs = ensure_storage_dirs()

	nav = render_sidebar()

	if nav == "Dashboard":
		render_dashboard(dirs)

		st.markdown("---")
		st.header("Image Watermark (Experimental)")

		if "image_output_path" not in st.session_state:
			st.session_state.image_output_path = None

		image_file = st.file_uploader("Upload Image", type=["jpg", "png"], key="image_upload")

		if image_file:
			from core.image_watermark import embed_image_watermark

			img_path = "temp_image.png"
			with open(img_path, "wb") as f:
				f.write(image_file.getbuffer())

			st.image(img_path, caption="Original Image")

			if st.button("Apply Image Watermark"):
				out_path = "watermarked_image.png"
				embed_image_watermark(img_path, out_path, "A")
				st.session_state.image_output_path = out_path

		if st.session_state.image_output_path:
			st.image(st.session_state.image_output_path, caption="Watermarked Image")
			st.success("Image Watermarked")
	elif nav == "Protect Video":
		render_top_header()
		render_step_flow()
		section_protect(dirs)
	elif nav == "Leak Detection":
		render_top_header()
		render_step_flow()
		section_detect(dirs)
	elif nav == "Reports (DMCA)":
		render_top_header()
		render_step_flow()
		section_report()
	elif nav == "Image DRM":
		render_top_header()
		section_image_protect()
		section_image_detect()
		section_image_report()
	else:
		render_top_header()
		st.info("You are logged out in demo mode.")


if __name__ == "__main__":
	main()

