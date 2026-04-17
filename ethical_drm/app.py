from pathlib import Path
import os
from uuid import uuid4

import streamlit as st

from auth import (
    authenticate_user,
    create_login_session,
    logout_session,
    register_user,
    restore_login_from_token,
)
from database.db import init_db
from ai.dmca_generator import generate_dmca_notice
from core import detector, hashing, watermark
from core.crawler import scan_url, scan_platforms

from database.debug_db import debug_database

if st.button("Debug DB"):
    info = debug_database("drm.db")  # or "ethical_drm/drm.db"
    st.write("DB Path:", info["db_path"])
    st.write("Exists:", info["exists"])
    st.write("Connected:", info["connected"])
    st.write("Tables:", info["tables"])
    st.write("Errors:", info["errors"])

    for table, rows in info["data"].items():
        st.subheader(table)
        st.write(rows)


APP_TITLE = "EthicalDRM"
AUTH_QUERY_PARAM = "auth_token"

init_db()

def base_storage_dir() -> Path:
    return Path(__file__).resolve().parent / "storage"


def init_state() -> None:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "auth_username" not in st.session_state:
        st.session_state.auth_username = None

    if st.session_state.authenticated and st.session_state.auth_username:
        st.session_state.user_id = st.session_state.auth_username
    elif "user_id" not in st.session_state:
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
    if "image_known_users" not in st.session_state:
        st.session_state.image_known_users = []
    if "image_detected_user" not in st.session_state:
        st.session_state.image_detected_user = None
    if "current_image_id" not in st.session_state:
        st.session_state.current_image_id = None
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None


def logout_user() -> None:
    if st.session_state.auth_token:
        logout_session(st.session_state.auth_token)
    st.session_state.authenticated = False
    st.session_state.auth_username = None
    st.session_state.auth_token = None
    st.session_state.user_id = f"User_{str(uuid4())[:6].upper()}"
    if AUTH_QUERY_PARAM in st.query_params:
        del st.query_params[AUTH_QUERY_PARAM]


def _get_query_auth_token() -> str | None:
    token = st.query_params.get(AUTH_QUERY_PARAM)
    if isinstance(token, list):
        return token[0] if token else None
    return token


def _restore_login_if_possible() -> None:
    if st.session_state.authenticated:
        return

    token = _get_query_auth_token()
    if not token:
        return

    username = restore_login_from_token(token)
    if username:
        st.session_state.authenticated = True
        st.session_state.auth_username = username
        st.session_state.auth_token = token
        st.session_state.user_id = username
    else:
        if AUTH_QUERY_PARAM in st.query_params:
            del st.query_params[AUTH_QUERY_PARAM]


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
        .stTabs {
            --auth-size: min(90vw, 520px);
            width: var(--auth-size);
            margin: 0.75rem auto 0 auto;
            border: 1px solid rgba(118, 208, 255, 0.28);
            border-radius: 16px;
            padding: 14px;
            background: linear-gradient(145deg, rgba(16, 29, 46, 0.92), rgba(8, 15, 27, 0.9));
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
        }
        .stTabs [role="tabpanel"] {
            min-height: calc(var(--auth-size) - 100px);
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        @media (max-width: 640px) {
            .stTabs {
                --auth-size: min(94vw, 420px);
                padding: 12px;
            }
            .stTabs [role="tabpanel"] {
                min-height: calc(var(--auth-size) - 86px);
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_auth_page() -> None:
    st.title(APP_TITLE)
    st.subheader("Secure Login")
    st.caption("Sign in to access the DRM dashboard.")

    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            login_submitted = st.form_submit_button("Login", use_container_width=True)

        if login_submitted:
            if authenticate_user(username, password):
                username = username.strip()
                session_token = create_login_session(username)
                st.session_state.authenticated = True
                st.session_state.auth_username = username
                st.session_state.auth_token = session_token
                st.session_state.user_id = username
                st.query_params[AUTH_QUERY_PARAM] = session_token
                st.success("Login successful. Redirecting...")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with signup_tab:
        with st.form("signup_form"):
            new_username = st.text_input("New Username", placeholder="Choose a username")
            new_password = st.text_input("New Password", type="password", placeholder="At least 8 characters")
            confirm_password = st.text_input("Confirm Password", type="password")
            signup_submitted = st.form_submit_button("Create Account", use_container_width=True)

        if signup_submitted:
            if new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                ok, message = register_user(new_username, new_password)
                if ok:
                    st.success(message)
                else:
                    st.error(message)


def render_sidebar() -> tuple[str, bool]:
    st.sidebar.title(APP_TITLE)
    st.sidebar.caption("Hackathon Demo Flow")
    st.sidebar.write(f"Logged in as: `{st.session_state.auth_username}`")

    nav = st.sidebar.radio(
        "Navigation",
        options=["Dashboard", "Protect Video", "Leak Detection", "Reports (DMCA)", "Image DRM"],
    )

    logout_clicked = st.sidebar.button("Logout", use_container_width=True)

    st.sidebar.markdown("---")
    st.sidebar.success("Monitoring Enabled")
    return nav, logout_clicked


def render_top_header() -> None:
    username = st.session_state.auth_username or st.session_state.user_id
    st.markdown(
        f"""
        <div class=\"header-card\">
            <h2 style=\"margin:0;\">Welcome, {username}</h2>
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
                st.session_state.fake_db = [{"user_id": st.session_state.user_id, "hashes": hashes}]

                file_size = os.path.getsize(output_path)
                st.success(f"Watermark applied. Output ready: current_output.mp4 ({file_size} bytes)")
            except Exception as exc:
                st.error(f"Protection failed: {exc}")

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

                    st.session_state.detected_user = detected or best_user
                    st.session_state.confidence = max(confidence, detector_confidence / 100)

                    if st.session_state.detected_user:
                        if st.session_state.confidence < 0.3:
                            st.warning("Low confidence match. Possible false positive.")
                        else:
                            st.success(f"Leak detected: {st.session_state.detected_user}")
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

    st.markdown("</div>", unsafe_allow_html=True)


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

    st.markdown("</div>", unsafe_allow_html=True)


def section_web_leak_scanner() -> None:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("### 🌐 Web Leak Scanner")
    st.caption("Scan a webpage for media files and verify potential leaks.")

    scan_target_url = st.text_input(
        "Enter URL to scan",
        placeholder="https://example.com",
        key="web_scanner_url",
    )

    scan_clicked = st.button("Scan URL", use_container_width=True)

    if scan_clicked:
        if not scan_target_url.strip():
            st.warning("Please enter a valid URL")
        else:
            results = []
            try:
                with st.spinner("Crawling and scanning..."):
                    raw_results = scan_url(scan_target_url.strip(), st.session_state.fake_db)
                if isinstance(raw_results, list):
                    results = raw_results
            except Exception:
                results = []

            if not results:
                st.info("Crawler found no leaks, running internal scan...")
                try:
                    fallback_results = scan_platforms(st.session_state.fake_db)
                    if isinstance(fallback_results, list):
                        results = fallback_results
                except Exception:
                    results = []

            if results:
                st.success(f"✅ Detected {len(results)} leak(s)")
                st.markdown("")

                for item in results:
                    platform = item.get("platform", "Web")
                    confidence = float(item.get("confidence", 0) or 0)
                    source_url = item.get("url", "-")

                    if confidence > 80:
                        risk_color = "#ff4d4f"
                        risk_label = "High Risk"
                    elif confidence >= 50:
                        risk_color = "#f4c430"
                        risk_label = "Medium Risk"
                    else:
                        risk_color = "#2ecc71"
                        risk_label = "Low Risk"

                    st.markdown(
                        f"""
                        <div style="
                            border:1px solid rgba(255,255,255,0.12);
                            border-left:6px solid {risk_color};
                            border-radius:12px;
                            padding:14px;
                            margin:10px 0;
                            background:rgba(255,255,255,0.03);
                        ">
                            <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;">
                                <div>
                                    <div style="font-size:1.05rem;font-weight:700;">🛡️ Leak Found</div>
                                    <div style="opacity:0.9;">Platform: <strong>{platform}</strong></div>
                                </div>
                                <div style="color:{risk_color};font-weight:700;">{risk_label}</div>
                            </div>
                            <div style="margin-top:8px;"><strong>URL:</strong> {source_url}</div>
                            <div style="margin-top:6px;"><strong>Confidence:</strong> {confidence:.2f}%</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.progress(int(max(0, min(100, confidence))))
                    st.markdown("")
            else:
                st.warning("No leaks detected or no media found")

    st.markdown("</div>", unsafe_allow_html=True)


def section_image_protect() -> None:
    st.header("Image Protection")

    img_file = st.file_uploader("Upload Image", type=["jpg", "png"], key="img_upload")

    if img_file:
        path = "image_input.png"
        with open(path, "wb") as f:
            f.write(img_file.getbuffer())

        st.image(path)

        if st.button("Apply Image Protection"):
            from core.image_watermark import distribute_image

            try:
                out, image_id = distribute_image(
                    original_path=path,
                    user_id=st.session_state.user_id,
                    uploaded_by=st.session_state.user_id,
                )
                if st.session_state.user_id not in st.session_state.image_known_users:
                    st.session_state.image_known_users.append(st.session_state.user_id)

                st.session_state.img_output = out
                st.session_state.current_image_id = image_id
                st.success("Image Protected and recorded in database.")
            except Exception as exc:
                st.error(f"Image protection failed: {exc}")

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
            from core.image_watermark import detect_leak as detect_image_leak

            if not st.session_state.current_image_id:
                st.warning("Protect an image first so an image_id exists for leak matching.")
            else:
                try:
                    detected_user = detect_image_leak(path, st.session_state.current_image_id)
                    st.session_state.image_detected_user = detected_user
                    if detected_user:
                        st.success(f"Leak Detected: {detected_user}")
                    else:
                        st.warning("No valid image watermark detected.")
                except Exception as exc:
                    st.error(f"Image leak detection failed: {exc}")

    st.text_input(
        "Detected User ID",
        value=st.session_state.image_detected_user or "-",
        disabled=True,
    )


def section_image_report() -> None:
    st.markdown("---")
    st.subheader("Generate DMCA Report (Image)")

    if st.button("Generate Image DMCA Report"):
        try:
            user = st.session_state.image_detected_user or st.session_state.user_id
            notice = generate_dmca_notice(user)
            st.session_state.image_dmca = notice
        except Exception:
            user = st.session_state.image_detected_user or st.session_state.user_id
            st.session_state.image_dmca = f"""
NOTICE OF COPYRIGHT INFRINGEMENT (DMCA)

This notice is regarding unauthorized distribution of protected image content.

Detected User ID: {user}

The image contains an embedded forensic watermark identifying the responsible user.

Action Requested:
- Immediate removal of the infringing content.
- Investigation  of the source.

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
    section_web_leak_scanner()


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="DRM", layout="wide")
    init_db()
    inject_styles()
    init_state()
    _restore_login_if_possible()
    dirs = ensure_storage_dirs()

    if not st.session_state.authenticated:
        render_auth_page()
        return

    nav, logout_clicked = render_sidebar()

    if logout_clicked:
        logout_user()
        st.rerun()

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
                embed_image_watermark(img_path, out_path, st.session_state.user_id)
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


if __name__ == "__main__":
    main()
