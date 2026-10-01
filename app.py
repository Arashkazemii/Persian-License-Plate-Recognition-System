# Copyright (C) 2024-2026 Arash Kazemi
# SPDX-License-Identifier: AGPL-3.0-only
from flask import Flask, render_template, Response, request, redirect, url_for, session, jsonify, flash, abort, send_file
from functools import wraps
from PIL import Image
import sqlite3
import os
from dotenv import load_dotenv
import re
from datetime import datetime, timedelta, timezone
from contextlib import closing
from pathlib import Path
from secrets import token_hex, compare_digest
from threading import Lock
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit
from database.database import create_database

# Load environment variables from a .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "")
if len(app.secret_key) < 32:
    raise RuntimeError("Set SECRET_KEY to a fresh random value of at least 32 characters.")
max_upload_mb = int(os.getenv("MAX_UPLOAD_MB", "100"))
if max_upload_mb <= 0:
    raise RuntimeError("MAX_UPLOAD_MB must be positive.")
app.config.update(
    MAX_CONTENT_LENGTH=max_upload_mb * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true",
)
SOURCE_URL = os.getenv("SOURCE_URL", "https://github.com/Arashkazemii/Persian-License-Plate-Recognition-System")
if urlsplit(SOURCE_URL).scheme not in {"https", "http"} or not urlsplit(SOURCE_URL).netloc:
    raise RuntimeError("SOURCE_URL must be an HTTP(S) URL for this version's source.")

# Create upload directory if it doesn't exist
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Explicit credentials only: never enable a built-in account.
users = {}
for number in (1, 2):
    username = os.getenv(f"USER_{number}_USERNAME", "")
    password = os.getenv(f"USER_{number}_PASSWORD", "")
    if bool(username) != bool(password):
        raise RuntimeError(f"Configure both USER_{number}_USERNAME and USER_{number}_PASSWORD.")
    if username:
        if username in users:
            raise RuntimeError("Configured usernames must be distinct.")
        users[username] = password
if not users:
    raise RuntimeError("Configure at least one account in your private environment.")

# Database config
DB_CONFIG = {
    'database': str(BASE_DIR / os.getenv("DB_PATH", "database/plates.db"))
}
create_database(DB_CONFIG['database'])

# Global variables for video source
current_source = {
    'type': 'rtsp',  # 'rtsp', 'image', or 'video'
    'path': os.getenv("RTSP_URL", "0")
}

# In-memory cooldown tracker
last_inserted = {
    'plate': None,
    'time': datetime.min.replace(tzinfo=timezone.utc)
}
latest_plate = None
processing_lock = Lock()

# Load YOLO models
class ModelManager:
    def __init__(self):
        self.plate_detector = None
        self.ocr_model = None

    def get_plate_detector(self):
        if self.plate_detector is None:
            from ultralytics import YOLO
            print("Loading Plate Detector Model...")
            self.plate_detector = YOLO(str(BASE_DIR / "models/best detector.pt"))
        return self.plate_detector

    def get_ocr_model(self):
        if self.ocr_model is None:
            from ultralytics import YOLO
            print("Loading OCR Model...")
            self.ocr_model = YOLO(str(BASE_DIR / "models/best ocr.pt"))
        return self.ocr_model

# Instantiate the model manager
model_manager = ModelManager()

# Character map for Persian license plates
charmap = {
    0: 'ث', 1: '3', 2: 'ت', 3: '1', 4: 'پ', 5: 'د', 6: '6', 7: 'ط', 8: 'ه‍', 
    9: 'ژ (معلولین و جانبازان)', 10: '2', 11: 'م', 12: 'الف', 13: '9', 14: '7', 
    15: 'ز', 16: '0', 17: 'ع', 18: '5', 19: 'ی', 20: 'س', 21: 'ج', 22: 'ش', 
    23: '4', 24: '8', 25: 'و', 26: 'ل', 27: 'ق', 28: 'ص', 29: 'ب', 30: 'ن'
}

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = token_hex(32)
    return session["csrf_token"]


@app.context_processor
def template_config():
    return {"csrf_token": csrf_token, "source_url": SOURCE_URL}


@app.before_request
def protect_forms():
    if request.method == "POST":
        expected = session.get("csrf_token", "")
        supplied = request.form.get("csrf_token", "")
        if not expected or not compare_digest(expected.encode(), supplied.encode()):
            abort(400, description="Invalid or missing CSRF token. Reload the page and retry.")


@app.errorhandler(413)
def upload_too_large(error):
    return jsonify({"status": "error", "message": "Upload exceeds MAX_UPLOAD_MB."}), 413

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username in users and compare_digest(users[username].encode(), password.encode()):
            session.clear()
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials. Please try again.")
            return render_template("login.html")
    return render_template("login.html")

# Logout route
@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))

# Set RTSP URL route
@app.route("/set_rtsp", methods=["POST"])
@login_required
def set_rtsp():
    global current_source
    rtsp_url = request.form.get('rtsp_url', '').strip()
    if valid_camera_source(rtsp_url):
        current_source = {
            'type': 'rtsp',
            'path': rtsp_url
        }
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Use an RTSP(S) URL on an allowed host or a numeric camera index."}), 400


def valid_camera_source(source):
    if source.isdecimal():
        return True
    try:
        parsed = urlsplit(source)
        allowed = {host.strip().lower() for host in os.getenv("RTSP_ALLOWED_HOSTS", "").split(",") if host.strip()}
        return (parsed.scheme in {"rtsp", "rtsps"} and bool(parsed.hostname)
                and (parsed.port is None or parsed.port > 0)
                and (not allowed or parsed.hostname.lower() in allowed))
    except ValueError:
        return False

# Upload image route
@app.route("/upload_image", methods=["POST"])
@login_required
def upload_image():
    global current_source
    if 'image' not in request.files:
        return jsonify({"status": "error", "message": "No image file provided"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
    
    if file:
        try:
            with Image.open(file.stream) as uploaded:
                if uploaded.width * uploaded.height > 20_000_000:
                    raise ValueError("Image too large")
                uploaded.verify()
            file.stream.seek(0)
        except (OSError, ValueError, Image.DecompressionBombError):
            return jsonify({"status": "error", "message": "Invalid image or image exceeds 20 megapixels."}), 400
        # Save the uploaded file
        filename = os.path.join(UPLOAD_FOLDER, 'current_image.jpg')
        file.save(filename)
        
        current_source = {
            'type': 'image',
            'path': filename
        }
        return jsonify({"status": "success"})
    
    return jsonify({"status": "error", "message": "Invalid file"}), 400

# Upload video route
@app.route("/upload_video", methods=["POST"])
@login_required
def upload_video():
    global current_source
    if 'video' not in request.files:
        return jsonify({"status": "error", "message": "No video file provided"}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
    
    if file:
        if Path(file.filename).suffix.lower() not in {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v'}:
            return jsonify({"status": "error", "message": "Unsupported video extension."}), 400
        import cv2

        filename = os.path.join(UPLOAD_FOLDER, 'current_video.mp4')
        # Validate a temporary file before replacing the currently selected video.
        with NamedTemporaryFile(dir=UPLOAD_FOLDER, suffix=Path(file.filename).suffix, delete=False) as upload:
            temp_path = upload.name
        try:
            file.save(temp_path)
            cap = cv2.VideoCapture(temp_path)
            try:
                readable, frame = cap.read() if cap.isOpened() else (False, None)
            finally:
                cap.release()
            if not readable or frame is None:
                return jsonify({"status": "error", "message": "Video cannot be decoded."}), 400
            os.replace(temp_path, filename)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
        current_source = {
            'type': 'video',
            'path': filename
        }
        return jsonify({"status": "success"})
    
    return jsonify({"status": "error", "message": "Invalid file"}), 400

def record_plate(formatted_text, now_utc):
    """Keep the original ten-second memory check and five-minute DB cooldown."""
    global latest_plate
    if (formatted_text == last_inserted['plate'] and
            (now_utc - last_inserted['time']).total_seconds() <= 10):
        return False
    cutoff = (now_utc - timedelta(minutes=5)).isoformat()
    try:
        with closing(sqlite3.connect(DB_CONFIG['database'])) as conn, conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM plates WHERE plate = ? AND julianday(time_detected) > julianday(?)",
                (formatted_text, cutoff),
            ).fetchone()[0]
            if count:
                return False
            conn.execute("INSERT INTO plates (plate, time_detected) VALUES (?, ?)",
                         (formatted_text, now_utc.isoformat()))
    except sqlite3.Error:
        app.logger.error("Could not store detection; check database access and schema.")
        return False
    latest_plate = formatted_text
    last_inserted.update(plate=formatted_text, time=now_utc)
    return True


def process_frame(frame):
    """Preserve first-box selection, OCR order, class mapping, and YOLO defaults."""
    import cv2
    import torch

    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    detection_results = model_manager.get_plate_detector()(image)
    for detection_result in detection_results or []:
        boxes = detection_result.boxes
        if boxes is None or len(boxes) == 0:
            continue
        x1, y1, x2, y2 = map(int, boxes.xyxy[0].tolist())
        if x2 <= x1 or y2 <= y1:
            continue
        cropped_plate = image.crop((x1, y1, x2, y2))
        for ocr_result in model_manager.get_ocr_model()(cropped_plate):
            if ocr_result.boxes is None:
                continue
            ocr_data = ocr_result.boxes.data
            sorted_tensor = ocr_data[torch.argsort(ocr_data[:, 0])]
            converted_characters = [charmap[int(num.item())] for num in sorted_tensor[:, -1]]
            if len(converted_characters) != 8:
                continue
            formatted_text = re.sub(r"(\d{2})(\D)(\d{3})(\d{2})", r"\1 \2 \3 \4",
                                    ''.join(converted_characters))
            if record_plate(formatted_text, datetime.now(timezone.utc)):
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, formatted_text, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)


def generate_video_feed():
    import cv2

    # A running feed retains its source when another request changes the input.
    source = current_source.copy()
    path = source['path']
    cap = None
    try:
        if source['type'] == 'rtsp':
            if not valid_camera_source(path):
                app.logger.warning("Invalid configured camera source.")
                return
            path = int(path) if path.isdecimal() else path
        if source['type'] != 'image':
            cap = cv2.VideoCapture(path)
            if not cap.isOpened():
                app.logger.warning("Unable to open video source.")
                return
        while True:
            if source['type'] == 'image':
                frame = cv2.imread(path)
            else:
                ret, frame = cap.read()
                if not ret:
                    break
            if frame is None:
                break
            # Ultralytics predictors and cooldown state are shared by this process.
            with processing_lock:
                process_frame(frame)
            encoded, buffer = cv2.imencode('.jpg', frame)
            if not encoded:
                break
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    except Exception as error:
        # Backend exceptions can include URLs/passwords; log the type only.
        app.logger.error("Video processing stopped (%s).", type(error).__name__)
    finally:
        if cap is not None:
            cap.release()

@app.route("/get_latest_plate", methods=["GET"])
@login_required
def get_latest_plate():
    return jsonify({"formatted_plate": latest_plate})

@app.route("/video_feed")
@login_required
def video_feed():
    return Response(generate_video_feed(), mimetype="multipart/x-mixed-replace; boundary=frame")

# Main page route
@app.route("/")
@login_required
def home():
    return render_template("main.html")


@app.route("/license")
def license_text():
    return send_file(BASE_DIR / "LICENSE", mimetype="text/plain")

if __name__ == "__main__":
    from waitress import serve
    # Shared source/models require a single process; threads let polling coexist with streaming.
    serve(app, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")), threads=4)
