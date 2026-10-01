"""Optional CPU smoke test on synthetic media; not an accuracy benchmark."""
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["YOLO_CONFIG_DIR"] = str(ROOT / ".cache" / "yolo-smoke")
Path(os.environ["YOLO_CONFIG_DIR"]).mkdir(parents=True, exist_ok=True)
os.environ["YOLO_AUTOINSTALL"] = "false"

import cv2
import numpy as np
import dotenv


def main():
    # Isolate storage and credentials from the developer's private .env.
    dotenv.load_dotenv = lambda *args, **kwargs: False
    with TemporaryDirectory() as folder:
        os.environ.update(SECRET_KEY="synthetic-smoke-secret-" + "x" * 32,
                          USER_1_USERNAME="smoke", USER_1_PASSWORD="synthetic-smoke-password",
                          USER_2_USERNAME="", USER_2_PASSWORD="", DB_PATH=str(Path(folder) / "plates.db"),
                          RTSP_URL="0", RTSP_ALLOWED_HOSTS="", SESSION_COOKIE_SECURE="false")
        import app
        app.UPLOAD_FOLDER = folder
        frame = np.zeros((128, 256, 3), dtype=np.uint8)
        for label, model in [("detector", app.model_manager.get_plate_detector()), ("ocr", app.model_manager.get_ocr_model())]:
            results = model(frame, device="cpu", verbose=False)
            assert len(results) == 1
            print(label, "checkpoint loaded and inferred; classes:", len(model.names))
        app.process_frame(frame.copy())
        video = str(Path(folder) / "synthetic.avi")
        writer = cv2.VideoWriter(video, cv2.VideoWriter_fourcc(*"MJPG"), 5, (256, 128))
        assert writer.isOpened()
        writer.write(frame)
        writer.write(frame)
        writer.release()
        client = app.app.test_client()
        client.get("/login")
        with client.session_transaction() as session:
            token = session["csrf_token"]
        assert client.post("/login", data={"username": "smoke", "password": "synthetic-smoke-password", "csrf_token": token}).status_code == 302
        client.get("/")
        with client.session_transaction() as session:
            token = session["csrf_token"]
        with open(video, "rb") as upload:
            assert client.post("/upload_video", data={"video": (upload, "synthetic.avi"), "csrf_token": token}).status_code == 200
        response = client.get("/video_feed")
        frames = list(response.response)
        response.close()
        assert len(frames) == 2 and all(b"Content-Type: image/jpeg" in item for item in frames)
        print("Real OpenCV upload and two-frame MJPEG stream passed")


if __name__ == "__main__":
    main()
