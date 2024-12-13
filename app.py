from flask import Flask, render_template, Response, request, redirect, url_for, session, jsonify, flash
from functools import wraps
import cv2
import torch
from PIL import Image
import oracledb
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "7a8c9b7d467e5b2f9f759ce502e5b6fa")  # Replace with a secure secret key

# Sample credentials
users = {
    os.getenv("USER_1_USERNAME", "default_user"): os.getenv("USER_1_PASSWORD", "default_pass"),
    os.getenv("USER_2_USERNAME", "security"): os.getenv("USER_2_PASSWORD", "admin"),
}

# Database config
DB_CONFIG = {
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'dsn': os.getenv("DB_DSN", "oracledb:1521/oltpsrc")
}

# Load YOLO models
class ModelManager:
    def __init__(self):
        self.plate_detector = None
        self.ocr_model = None

    def get_plate_detector(self):
        if self.plate_detector is None:
            print("Loading Plate Detector Model...")
            self.plate_detector = torch.hub.load(
                'ultralytics/yolov5', 'custom', path='models/best_plate_detector.pt.pt'
            )
        return self.plate_detector

    def get_ocr_model(self):
        if self.ocr_model is None:
            print("Loading OCR Model...")
            self.ocr_model = torch.hub.load(
                'ultralytics/yolov5', 'custom', path='models/best_ocr.pt.pt'
            )
        return self.ocr_model


# Instantiate the model manager
model_manager = ModelManager()

plate_detector = model_manager.get_plate_detector()
ocr_model = model_manager.get_ocr_model()

# RTSP URL
rtsp_url = "rtsp_url / video.mp4 / etc."

# Character map for Persian license plates
character_map = {
    "Ø§": "ا", "Ø¨": "ب", "Ø¯": "د", "Ø³": "س", "Ø´": "ش", "Ù": "ف",
    "Ù": "ق", "Ú©": "ک", "Ù": "ل", "Ù": "م", "Ù": "ن", "Ù": "و",
    "Ù": "ه", "Û": "ی", "Ø¹": "ع", "Øº": "غ", "Ø²": "ز", "Ø±": "ر",
    "Ø·": "ط", "Ø¸": "ظ", "Øª": "ت", "Ø«": "ث", "Ø­": "ح", "Ø®": "خ",
    "Ù¾": "پ", "Ú": "چ", "Ú": "ژ", "Ø¬": "ج", "Ø°": "ذ", "ÙØ§": "لا",
    "Øµ": "ص", "Ø¶": "ض", "1": "1", "2": "2", "3": "3", "4": "4",
    "5": "5", "6": "6", "7": "7", "8": "8", "9": "9", "0": "0"
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

# Video feed generation
def generate_video_feed():
    global latest_plate
    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        print(f"Error: Unable to open video stream at {rtsp_url}")
        yield b""
        return
    
    frame_count = 0
    skip_frames = 5
    while True:
        try:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
            ret, frame = cap.read()
            if not ret:
                print("Warning: Frame read failed or stream ended.")
                break

            frame_count += skip_frames

            # Process the frame for detection
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            results1 = plate_detector(image)
            for result in results1.xyxy[0]:
                x1, y1, x2, y2, conf, cls = result.tolist()
                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                cropped_plate = image.crop((x1, y1, x2, y2))

                results2 = ocr_model(cropped_plate)
                df = results2.pandas().xyxy[0].sort_values(by="xmin")
                df['name'] = df['name'].replace(character_map)
                license_plate_chars = df['name'].tolist()
                
                if len(license_plate_chars) >= 8:
                    formatted_plate = (
                        f"{license_plate_chars[6]}{license_plate_chars[7]}"
                        f"ایران"
                        f"{license_plate_chars[3]}{license_plate_chars[4]}{license_plate_chars[5]}"
                        f"{license_plate_chars[2]}{license_plate_chars[0]}{license_plate_chars[1]}"
                    )
                else:
                    formatted_plate = "Invalid Plate"
                    
                latest_plate = formatted_plate

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, formatted_plate, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

            _, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

        except Exception as e:
            print(f"Error processing video feed: {e}")
            break

    cap.release()
    print("Video feed stream closed.")

@app.route("/get_latest_plate", methods=["GET"])
def get_latest_plate():
    return jsonify({"formatted_plate": latest_plate})

@app.route("/video_feed")
@login_required
def video_feed():
    return Response(generate_video_feed(), mimetype="multipart/x-mixed-replace; boundary=frame")

# Search database route
@app.route("/search", methods=["POST"])
@login_required
def search_database():
    plate_output = request.json.get("plate_output")  # JSON input validation

    if not plate_output:
        return jsonify({'error': 'License plate is required.'}), 400

    try:
        connection = oracledb.connect(**DB_CONFIG)
        cursor = connection.cursor()
        query = """
        SELECT 
            NAM_DRV_MTBIL, 
            DES_FAMIL_DRV_MTBIL, 
            COD_NATIONAL_DRV_MTBIL 
        FROM IRISA.MTM_WAYBILLS 
            WHERE COD_CAR_MTBIL = :plate
                """
        cursor.execute(query, plate=plate_output)
        result = cursor.fetchone()

        if result:
            name, name2, national_code = result
            return jsonify({'name': name, 'name2': name2, 'national_code': national_code})
        else:
            return jsonify({'error': 'No results found for the given plate.'}), 404

    except oracledb.DatabaseError as e:
        error_obj, = e.args
        print(f"Database error [{error_obj.code}]: {error_obj.message}")
        return jsonify({'error': 'Database connection failed.'}), 500

    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()

# Main page route
@app.route("/")
@login_required
def home():
    return render_template("main.html")

if __name__ == "__main__":
    app.run(debug=True)
