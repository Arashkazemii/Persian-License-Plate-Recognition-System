from flask import Flask, render_template, Response, request, redirect, url_for, session, jsonify, flash
from functools import wraps
import cv2
import torch
from PIL import Image
import sqlite3
import os
from dotenv import load_dotenv
from ultralytics import YOLO
import re
from datetime import datetime, timedelta, timezone
import tempfile
import shutil

# Load environment variables from a .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "7a8c9b7d467e5b2f9f759ce502e5b6fa")  # Replace with a secure secret key

# Create upload directory if it doesn't exist
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Sample credentials
users = {
    os.getenv("USER_1_USERNAME", "default_user"): os.getenv("USER_1_PASSWORD", "default_pass"),
    os.getenv("USER_2_USERNAME", "security"): os.getenv("USER_2_PASSWORD", "admin"),
}

# Database config
DB_CONFIG = {
    'database': os.getenv("DB_PATH", "./database/plates.db")
}

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

# Load YOLO models
class ModelManager:
    def __init__(self):
        self.plate_detector = None
        self.ocr_model = None

    def get_plate_detector(self):
        if self.plate_detector is None:
            print("Loading Plate Detector Model...")
            self.plate_detector = YOLO("./models/best detector.pt")
        return self.plate_detector

    def get_ocr_model(self):
        if self.ocr_model is None:
            print("Loading OCR Model...")
            self.ocr_model = YOLO("./models/best ocr.pt")
        return self.ocr_model

# Instantiate the model manager
model_manager = ModelManager()

plate_detector = model_manager.get_plate_detector()
ocr_model = model_manager.get_ocr_model()

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
        if "logged_in" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username] == password:
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials. Please try again.")
            return render_template("login.html")
    return render_template("login.html")

# Logout route
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# Set RTSP URL route
@app.route("/set_rtsp", methods=["POST"])
@login_required
def set_rtsp():
    global current_source
    rtsp_url = request.form.get('rtsp_url')
    if rtsp_url:
        current_source = {
            'type': 'rtsp',
            'path': rtsp_url
        }
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "No RTSP URL provided"}), 400

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
        # Save the uploaded file
        filename = os.path.join(UPLOAD_FOLDER, 'current_video.mp4')
        file.save(filename)
        
        current_source = {
            'type': 'video',
            'path': filename
        }
        return jsonify({"status": "success"})
    
    return jsonify({"status": "error", "message": "Invalid file"}), 400

# Video feed generation
def generate_video_feed():
    global latest_plate
    cap = cv2.VideoCapture(current_source['path'])
    
    if not cap.isOpened():
        print(f"Error: Unable to open video source at {current_source['path']}")
        yield b""
        return

    while True:
        try:
            ret, frame = cap.read()
            if not ret:
                if current_source['type'] == 'image':
                    # For image, keep showing the same frame
                    frame = cv2.imread(current_source['path'])
                else:
                    print("End of video stream.")
                    break
            
            # Process the frame for detection
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            detection_results = plate_detector(image)

            if detection_results and len(detection_results) > 0:
                for detection_result in detection_results:
                    x1, y1, x2, y2 = detection_result.boxes.xyxy[0].tolist()
                    x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                    cropped_plate = image.crop((x1, y1, x2, y2))

                    # OCR the plate
                    ocr_results = ocr_model(cropped_plate)
                    
                    for ocr_result in ocr_results:
                        ocr_data = ocr_result.boxes.data
                        sorted_tensor = ocr_data[torch.argsort(ocr_data[:, 0])]
                        sorted_last_column = sorted_tensor[:, -1]

                        # Convert tensor to characters
                        converted_characters = [
                            charmap[int(num.item())] for num in sorted_last_column
                        ]

                        if len(converted_characters) == 8:
                            # Format the plate number
                            result_string = ''.join(converted_characters)
                            formatted_text = re.sub(
                                r"(\d{2})(\D)(\d{3})(\d{2})", r"\1 \2 \3 \4", result_string
                            )

                            now_utc = datetime.now(timezone.utc)
                            five_minutes_ago = now_utc - timedelta(minutes=5)

                            # Avoid flooding inserts by memory check
                            if (formatted_text != last_inserted['plate'] or 
                                (now_utc - last_inserted['time']).total_seconds() > 10):

                                try:
                                    conn = sqlite3.connect(DB_CONFIG['database'])
                                    cursor = conn.cursor()

                                    cursor.execute("""
                                        SELECT COUNT(*) FROM plates 
                                        WHERE plate = ? AND time_detected > ?
                                    """, (formatted_text, five_minutes_ago.isoformat()))
                                    
                                    count = cursor.fetchone()[0]

                                    if count == 0:
                                        cursor.execute("""
                                            INSERT INTO plates (plate, time_detected)
                                            VALUES (?, ?)
                                        """, (formatted_text, now_utc.isoformat()))
                                        conn.commit()

                                        # Visual feedback
                                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                        cv2.putText(frame, formatted_text, (x1, y1 - 10),
                                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

                                        latest_plate = formatted_text
                                        last_inserted['plate'] = formatted_text
                                        last_inserted['time'] = now_utc

                                except sqlite3.Error as e:
                                    print(f"Database error: {e}")
                                finally:
                                    if conn:
                                        conn.close()

            # Encode and stream
            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

        except Exception as e:
            print(f"Error processing video feed: {e}")
            continue

    cap.release()
    print("Video processing completed.")

@app.route("/get_latest_plate", methods=["GET"])
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

if __name__ == "__main__":
    app.run(debug=True)