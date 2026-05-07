import streamlit as st
try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

import os
import cv2
import tempfile
import time
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Axel Guard — Pothole AI",
    page_icon="🛣️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Page shell ── */
.ag-shell {
    min-height: 100vh;
    background: #0a0f1e;
    color: #f1f5f9;
}

/* ── Top navbar ── */
.ag-navbar {
    background: rgba(15,23,42,0.95);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(255,255,255,0.06);
    padding: 0 40px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
}
.ag-logo {
    display: flex;
    align-items: center;
    gap: 12px;
}
.ag-logo-icon {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, #f97316, #ea580c);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
    box-shadow: 0 4px 14px rgba(249,115,22,0.4);
}
.ag-logo-text { font-weight: 900; font-size: 17px; letter-spacing: -0.5px; color: #f8fafc; }
.ag-logo-sub  { font-size: 11px; color: #f97316; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase; }
.ag-badge {
    background: rgba(249,115,22,0.15);
    border: 1px solid rgba(249,115,22,0.3);
    color: #fb923c;
    font-size: 11px;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 20px;
    letter-spacing: 0.05em;
}

/* ── Hero ── */
.ag-hero {
    padding: 64px 40px 40px;
    text-align: center;
}
.ag-hero h1 {
    font-size: 48px;
    font-weight: 900;
    letter-spacing: -1.5px;
    background: linear-gradient(135deg, #f8fafc 0%, #94a3b8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 16px;
    line-height: 1.1;
}
.ag-hero p {
    color: #64748b;
    font-size: 16px;
    font-weight: 500;
    max-width: 480px;
    margin: 0 auto;
    line-height: 1.6;
}

/* ── Stat cards ── */
.ag-stats {
    display: flex;
    gap: 16px;
    padding: 0 40px 40px;
    justify-content: center;
}
.ag-stat {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 20px 32px;
    text-align: center;
    min-width: 140px;
}
.ag-stat-val {
    font-size: 28px;
    font-weight: 900;
    color: #f8fafc;
    letter-spacing: -1px;
    line-height: 1;
}
.ag-stat-lbl {
    font-size: 11px;
    font-weight: 600;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-top: 6px;
}
.ag-stat.orange .ag-stat-val { color: #f97316; }
.ag-stat.green  .ag-stat-val { color: #22c55e; }
.ag-stat.blue   .ag-stat-val { color: #38bdf8; }

/* ── Upload card ── */
.ag-upload-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 24px;
    padding: 40px;
    margin: 0 40px 32px;
}
.ag-section-title {
    font-size: 13px;
    font-weight: 700;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.ag-section-title::before {
    content: '';
    display: block;
    width: 3px;
    height: 14px;
    background: #f97316;
    border-radius: 2px;
}

/* ── Analyze button ── */
.stButton > button {
    background: linear-gradient(135deg, #f97316, #ea580c) !important;
    color: white !important;
    font-weight: 800 !important;
    font-size: 15px !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 14px 40px !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 8px 24px rgba(249,115,22,0.35) !important;
    transition: all 0.2s !important;
    width: 100% !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 12px 32px rgba(249,115,22,0.45) !important;
}

/* ── Progress ── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #f97316, #fb923c) !important;
    border-radius: 4px !important;
}

/* ── Live feed label ── */
.ag-live-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(239,68,68,0.15);
    border: 1px solid rgba(239,68,68,0.3);
    color: #f87171;
    font-size: 11px;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 20px;
    letter-spacing: 0.08em;
    margin-bottom: 10px;
}
.ag-live-dot {
    width: 6px; height: 6px;
    background: #ef4444;
    border-radius: 50%;
    animation: pulse 1.2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

/* ── Detection count badge ── */
.ag-det-badge {
    background: rgba(34,197,94,0.15);
    border: 1px solid rgba(34,197,94,0.3);
    color: #4ade80;
    font-size: 22px;
    font-weight: 900;
    padding: 16px 24px;
    border-radius: 16px;
    text-align: center;
    margin-bottom: 8px;
}

/* ── Result grid frame caption ── */
.ag-frame-cap {
    font-size: 11px;
    color: #475569;
    font-weight: 600;
    margin-top: 4px;
    text-align: center;
}

/* ── Info/warning boxes ── */
.ag-info {
    background: rgba(56,189,248,0.08);
    border: 1px solid rgba(56,189,248,0.2);
    border-radius: 12px;
    padding: 14px 20px;
    color: #7dd3fc;
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 16px;
}
.ag-warn {
    background: rgba(251,191,36,0.08);
    border: 1px solid rgba(251,191,36,0.2);
    border-radius: 12px;
    padding: 14px 20px;
    color: #fcd34d;
    font-size: 14px;
    font-weight: 500;
}
.ag-success {
    background: rgba(34,197,94,0.08);
    border: 1px solid rgba(34,197,94,0.2);
    border-radius: 12px;
    padding: 14px 20px;
    color: #4ade80;
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 16px;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.02) !important;
    border: 2px dashed rgba(249,115,22,0.3) !important;
    border-radius: 16px !important;
    padding: 20px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgba(249,115,22,0.6) !important;
    background: rgba(249,115,22,0.04) !important;
}

/* ── Divider ── */
.ag-divider {
    height: 1px;
    background: rgba(255,255,255,0.06);
    margin: 32px 40px;
}

/* Image borders */
[data-testid="stImage"] img {
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
}
</style>
""", unsafe_allow_html=True)

# ── AWS / Model setup ─────────────────────────────────────────────────────────
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION     = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")
BUCKET_NAME    = "axelguard-pothole-detections"
MODEL_PATH     = "pothole_seg_v1.pt"

if HAS_BOTO3 and AWS_ACCESS_KEY:
    s3 = boto3.client("s3", aws_access_key_id=AWS_ACCESS_KEY,
                      aws_secret_access_key=AWS_SECRET_KEY, region_name=AWS_REGION)
else:
    s3 = None

@st.cache_resource(show_spinner=False)
def load_model():
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        from ultralytics import YOLO
        return YOLO(MODEL_PATH)
    except Exception:
        return None

# ── Navbar ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ag-navbar">
  <div class="ag-logo">
    <div class="ag-logo-icon">🛣️</div>
    <div>
      <div class="ag-logo-text">AXEL GUARD</div>
      <div class="ag-logo-sub">Pothole AI</div>
    </div>
  </div>
  <div class="ag-badge">⚡ YOLOv8 Segmentation</div>
</div>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ag-hero">
  <h1>Detect Potholes<br>Before They Cost You</h1>
  <p>Upload any dashcam footage and our custom-trained AI identifies every pothole in seconds.</p>
</div>
""", unsafe_allow_html=True)

# ── Load model (show spinner in center) ───────────────────────────────────────
with st.spinner("Loading AI model..."):
    model = load_model()

if model is None:
    st.markdown('<div style="padding:40px"><div class="ag-warn">⚠️ Model file not found. Make sure <code>pothole_seg_v1.pt</code> is in the app directory.</div></div>', unsafe_allow_html=True)
    st.stop()

# ── Session state for stats ───────────────────────────────────────────────────
if "total_analyzed" not in st.session_state:
    st.session_state.total_analyzed = 0
if "total_detections" not in st.session_state:
    st.session_state.total_detections = 0
if "last_duration" not in st.session_state:
    st.session_state.last_duration = 0

# ── Stats row ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="ag-stats">
  <div class="ag-stat orange">
    <div class="ag-stat-val">{st.session_state.total_analyzed}</div>
    <div class="ag-stat-lbl">Videos Analyzed</div>
  </div>
  <div class="ag-stat green">
    <div class="ag-stat-val">{st.session_state.total_detections}</div>
    <div class="ag-stat-lbl">Potholes Found</div>
  </div>
  <div class="ag-stat blue">
    <div class="ag-stat-val">{st.session_state.last_duration}s</div>
    <div class="ag-stat-lbl">Last Scan Time</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Upload card ───────────────────────────────────────────────────────────────
st.markdown('<div class="ag-upload-card">', unsafe_allow_html=True)
st.markdown('<div class="ag-section-title">Upload Dashcam Video</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    label="Drag & drop or browse — MP4, MOV, AVI (max 200MB)",
    type=["mp4", "mov", "avi"],
    label_visibility="collapsed",
)

if uploaded_file:
    size_mb = uploaded_file.size / (1024 * 1024)
    st.markdown(f'<div class="ag-info">📁 <strong>{uploaded_file.name}</strong> &nbsp;·&nbsp; {size_mb:.1f} MB &nbsp;·&nbsp; Ready to analyze</div>', unsafe_allow_html=True)
    analyze_btn = st.button("🔍  Run Pothole Detection", use_container_width=True)
else:
    analyze_btn = False

st.markdown('</div>', unsafe_allow_html=True)

# ── S3 upload helper ──────────────────────────────────────────────────────────
def upload_to_s3(file_path, object_name):
    if not s3:
        return False
    try:
        try:
            s3.head_bucket(Bucket=BUCKET_NAME)
        except Exception:
            try:
                if AWS_REGION == "us-east-1":
                    s3.create_bucket(Bucket=BUCKET_NAME)
                else:
                    s3.create_bucket(Bucket=BUCKET_NAME,
                                     CreateBucketConfiguration={"LocationConstraint": AWS_REGION})
            except Exception:
                return False
        s3.upload_file(file_path, BUCKET_NAME, object_name)
        return True
    except Exception:
        return False

# ── Main analysis ─────────────────────────────────────────────────────────────
if uploaded_file and analyze_btn:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tfile.write(uploaded_file.read())
    video_path = tfile.name
    tfile.close()

    start_time = time.time()

    # S3 upload
    with st.spinner("Uploading to cloud storage..."):
        ts      = int(time.time())
        s3_key  = f"uploads/{ts}_{uploaded_file.name}"
        success = upload_to_s3(video_path, s3_key)

    if success:
        st.markdown(f'<div style="padding:0 40px"><div class="ag-success">☁️ Backed up to S3 — <code>s3://{BUCKET_NAME}/{s3_key}</code></div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="padding:0 40px"><div class="ag-warn">⚠️ Cloud backup skipped — running detection locally.</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="ag-divider"></div>', unsafe_allow_html=True)

    # ── Live detection layout ──
    st.markdown('<div style="padding:0 40px">', unsafe_allow_html=True)
    st.markdown('<div class="ag-section-title">Live Analysis Feed</div>', unsafe_allow_html=True)

    col_feed, col_side = st.columns([3, 1], gap="large")

    with col_feed:
        st.markdown('<div class="ag-live-badge"><div class="ag-live-dot"></div>PROCESSING</div>', unsafe_allow_html=True)
        live_placeholder = st.empty()

    with col_side:
        st.markdown('<div style="font-size:12px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:12px">Recent Hits</div>', unsafe_allow_html=True)
        recent_slots = [st.empty() for _ in range(4)]
        det_count_placeholder = st.empty()

    progress_bar  = st.progress(0)
    status_placeholder = st.empty()

    cap          = cv2.VideoCapture(video_path)
    total_frames = max(int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), 1)
    fps          = cap.get(cv2.CAP_PROP_FPS) or 30

    detected_paths = []
    frame_idx      = 0

    with tempfile.TemporaryDirectory() as tmp_dir:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            results    = model(frame, conf=0.30, verbose=False, classes=[3])
            has_det    = any(r.boxes and len(r.boxes) > 0 for r in results)
            annotated  = results[0].plot()
            ann_rgb    = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

            if frame_idx % 4 == 0:
                elapsed   = frame_idx / fps
                remaining = max((total_frames - frame_idx) / fps, 0)
                live_placeholder.image(ann_rgb, use_container_width=True)
                status_placeholder.markdown(
                    f'<div style="color:#475569;font-size:13px;font-weight:600;margin-top:8px">'
                    f'Frame {frame_idx}/{total_frames} &nbsp;·&nbsp; '
                    f'{elapsed:.0f}s elapsed &nbsp;·&nbsp; ~{remaining:.0f}s remaining</div>',
                    unsafe_allow_html=True
                )
                progress_bar.progress(min(frame_idx / total_frames, 1.0))

            if has_det:
                save_path = os.path.join(tmp_dir, f"det_{frame_idx:06d}.jpg")
                cv2.imwrite(save_path, cv2.cvtColor(ann_rgb, cv2.COLOR_RGB2BGR))
                detected_paths.append((frame_idx, save_path))

                recent = detected_paths[-4:][::-1]
                for i, (fidx, pth) in enumerate(recent):
                    recent_slots[i].image(pth, caption=f"Frame {fidx}", use_container_width=True)

                det_count_placeholder.markdown(
                    f'<div class="ag-det-badge">{len(detected_paths)}</div>'
                    f'<div style="color:#475569;font-size:11px;font-weight:600;text-align:center">potholes detected</div>',
                    unsafe_allow_html=True
                )

            frame_idx += 1

        cap.release()
        progress_bar.progress(1.0)
        duration = int(time.time() - start_time)

        # Update session stats
        st.session_state.total_analyzed   += 1
        st.session_state.total_detections += len(detected_paths)
        st.session_state.last_duration     = duration

        status_placeholder.markdown(
            f'<div style="color:#4ade80;font-size:14px;font-weight:700;margin-top:8px">'
            f'✅ Analysis complete in {duration}s</div>',
            unsafe_allow_html=True
        )

        st.markdown('</div>', unsafe_allow_html=True)

        # ── Results report ──
        st.markdown('<div class="ag-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div style="padding:0 40px 40px">', unsafe_allow_html=True)
        st.markdown('<div class="ag-section-title">Detection Report</div>', unsafe_allow_html=True)

        if detected_paths:
            # Summary row
            detection_rate = (len(detected_paths) / total_frames) * 100
            severity = "HIGH" if detection_rate > 15 else "MEDIUM" if detection_rate > 5 else "LOW"
            sev_color = "#ef4444" if severity == "HIGH" else "#f59e0b" if severity == "MEDIUM" else "#22c55e"

            st.markdown(f"""
            <div style="display:flex;gap:16px;margin-bottom:32px;flex-wrap:wrap">
              <div class="ag-stat" style="flex:1;min-width:120px">
                <div class="ag-stat-val" style="color:#f97316">{len(detected_paths)}</div>
                <div class="ag-stat-lbl">Frames with Potholes</div>
              </div>
              <div class="ag-stat" style="flex:1;min-width:120px">
                <div class="ag-stat-val" style="color:#38bdf8">{total_frames}</div>
                <div class="ag-stat-lbl">Total Frames</div>
              </div>
              <div class="ag-stat" style="flex:1;min-width:120px">
                <div class="ag-stat-val" style="color:#a78bfa">{detection_rate:.1f}%</div>
                <div class="ag-stat-lbl">Detection Rate</div>
              </div>
              <div class="ag-stat" style="flex:1;min-width:120px">
                <div class="ag-stat-val" style="color:{sev_color}">{severity}</div>
                <div class="ag-stat-lbl">Road Severity</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Gallery
            cols = st.columns(3, gap="medium")
            for i, (fidx, img_path) in enumerate(detected_paths[:60]):
                with cols[i % 3]:
                    st.image(img_path, use_container_width=True)
                    st.markdown(f'<div class="ag-frame-cap">Detection #{i+1} &nbsp;·&nbsp; Frame {fidx}</div>', unsafe_allow_html=True)

            if len(detected_paths) > 60:
                st.markdown(f'<div style="color:#475569;font-size:13px;font-weight:600;text-align:center;margin-top:16px">Showing 60 of {len(detected_paths)} detections</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center;padding:48px">
              <div style="font-size:48px;margin-bottom:12px">✅</div>
              <div style="font-size:20px;font-weight:800;color:#f8fafc">Road Clear</div>
              <div style="color:#475569;font-size:14px;margin-top:8px">No potholes detected in this footage.</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    os.unlink(video_path)
