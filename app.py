import streamlit as st
try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
import os
import cv2
import tempfile

from dotenv import load_dotenv
import time

# Load Credentials
load_dotenv()

st.set_page_config(page_title="AxelGuard System", page_icon="🚗", layout="wide")

st.title("🚗 AxelGuard Pothole detection system")
st.write("Upload a dashcam video. We will save it to the Cloud and detect potholes using your Custom AI.")

# AWS Configuration
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
BUCKET_NAME = "pothole-detection-demo-upload"

# Initialize S3
if HAS_BOTO3:
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )
else:
    s3 = None

# Initialize Model
MODEL_PATH = "pothole_seg_v1.pt"

@st.cache_resource
def load_model():
    if not os.path.exists(MODEL_PATH):
        st.error(f"Model file not found: {MODEL_PATH}")
        return None
    try:
        from ultralytics import YOLO
        return YOLO(MODEL_PATH)
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

model = load_model()
if model is None:
    st.stop()

# --- Functions ---
def upload_to_s3(file_path, object_name):
    """Uploads a file to S3 bucket, creating bucket if needed."""
    if not HAS_BOTO3 or s3 is None:
        st.warning("AWS Library (boto3) not installed. Upload skipped.")
        return False

    try:
        # Check/Create Bucket
        try:
            s3.head_bucket(Bucket=BUCKET_NAME)
        except:
            try:
                if AWS_REGION == 'us-east-1':
                    s3.create_bucket(Bucket=BUCKET_NAME)
                else:
                    s3.create_bucket(
                        Bucket=BUCKET_NAME,
                        CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
                    )
                st.success(f"Created new S3 bucket: {BUCKET_NAME}")
            except Exception as e:
                st.error(f"Could not create bucket: {e}")
                return False

        # Upload
        s3.upload_file(file_path, BUCKET_NAME, object_name)
        return True
    except Exception as e:
        st.error(f"S3 Upload Error: {e}")
        return False

def process_video(video_path, temp_dir):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Live Processing")
        live_image = st.empty()
    with col2:
        st.subheader("Recent Detections")
        # Grid for recent detections
        recent_det_placeholders = [st.empty() for _ in range(4)]
        
    detected_frame_paths = []
    
    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Run Inference (Only show Class 3: Pothole)
        results = model(frame, conf=0.25, verbose=False, classes=[3]) # 25% Confidence, Only Potholes
        
        # Check if Pothole (Class 3 in your yaml)
        has_detection = False
        for r in results:
            if r.boxes:
                has_detection = True
                
        # Visualize
        annotated_frame = results[0].plot()
        annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        
        # Update Live View
        if frame_idx % 5 == 0: # Update every 5 frames
            live_image.image(annotated_frame_rgb, caption=f"Frame {frame_idx}", use_container_width=True)
            status_text.text(f"Processing Frame {frame_idx}/{total_frames}...")
            progress_bar.progress(min(frame_idx / total_frames, 1.0))
            
        # Save Trigger
        if has_detection:
            # Save to disk to save RAM
            save_path = os.path.join(temp_dir, f"det_{frame_idx}.jpg")
            # Convert back to BGR for opencv write, or just save RGB if we use PIL. 
            # cv2.imwrite expects BGR.
            annotated_frame_bgr = cv2.cvtColor(annotated_frame_rgb, cv2.COLOR_RGB2BGR)
            cv2.imwrite(save_path, annotated_frame_bgr)
            
            detected_frame_paths.append(save_path)
            
            # Update Recent Detections Gallery (Simultaneously show last 4)
            # Get last 4 paths
            recent = detected_frame_paths[-4:]
            # Reverse so newest is top/first
            recent_reversed = recent[::-1]
            
            for i, p_path in enumerate(recent_reversed):
                if i < 4:
                    recent_det_placeholders[i].image(p_path, caption=f"Pothole @ Frame {frame_idx}", use_container_width=True)
        
        frame_idx += 1

    cap.release()
    progress_bar.progress(1.0)
    status_text.text("Processing Complete!")
    return detected_frame_paths

# --- Main UI ---
uploaded_file = st.file_uploader("Choose a video...", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    # Save temp
    tfile = tempfile.NamedTemporaryFile(delete=False) 
    tfile.write(uploaded_file.read())
    video_path = tfile.name
    
    st.info(f"Video Loaded: {uploaded_file.name}")
    
    if st.button("Analyze & Upload"):
        # 1. Upload
        with st.spinner("Uploading to AWS S3..."):
            timestamp = int(time.time())
            s3_name = f"{timestamp}_{uploaded_file.name}"
            success = upload_to_s3(video_path, s3_name)
            if success:
                st.success(f"✅ Uploaded to S3: s3://{BUCKET_NAME}/{s3_name}")
            else:
                st.warning("⚠️ S3 Upload Failed (Check credentials), but proceeding with detection locally.")
                
        # 2. Process
        with st.spinner("Analyzing Video..."):
            # Create a localized temporary directory for frames
            with tempfile.TemporaryDirectory() as temp_dir:
                detections = process_video(video_path, temp_dir)
                
                st.success(f"Done! Found detections in {len(detections)} frames.")
                
                if len(detections) > 0:
                    st.write("---")
                    st.header("Detection Report")
                    # Display all detections in a grid
                    cols = st.columns(3)
                    for i, img_path in enumerate(detections):
                        if i > 50: break # Limit gallery
                        col = cols[i % 3]
                        col.image(img_path, caption=f"Detection {i+1}", use_container_width=True)
                else:
                    st.write("No potholes detected.")
