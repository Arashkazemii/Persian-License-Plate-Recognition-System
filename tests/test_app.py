from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
import sqlite3
import sys
from types import SimpleNamespace

from PIL import Image
import pytest

from conftest import csrf
from database.database import create_database


@pytest.mark.parametrize("settings", [
    {"SECRET_KEY": ""}, {"USER_1_USERNAME": "", "USER_1_PASSWORD": ""},
    {"USER_2_USERNAME": "partial"}, {"MAX_UPLOAD_MB": "0"},
    {"USER_2_USERNAME": "test-operator", "USER_2_PASSWORD": "other"},
    {"SOURCE_URL": "javascript:alert(1)"},
    {"SOURCE_URL": "https:"},
])
def test_incomplete_or_unsafe_config_fails(load_app, settings):
    with pytest.raises(RuntimeError):
        load_app(**settings)


def test_startup_is_lazy_and_initializes_database(application):
    assert application.latest_plate is None
    assert application.model_manager.plate_detector is None
    with sqlite3.connect(application.DB_CONFIG["database"]) as conn:
        assert conn.execute("SELECT COUNT(*) FROM plates").fetchone()[0] == 0


@pytest.mark.parametrize("path", ["/", "/video_feed", "/get_latest_plate"])
def test_detection_routes_require_login(client, path):
    assert client.get(path).status_code == 302


def test_login_logout_and_initial_poll(signed_in):
    assert signed_in.get("/get_latest_plate").json == {"formatted_plate": None}
    assert signed_in.get("/logout").status_code == 405
    assert signed_in.post("/logout", data={"csrf_token": csrf(signed_in)}).status_code == 302
    assert signed_in.get("/get_latest_plate").status_code == 302


def test_bad_or_missing_login_fields_do_not_crash(client):
    client.get("/login")
    response = client.post("/login", data={"csrf_token": csrf(client)})
    assert response.status_code == 200
    assert b"Invalid credentials" in response.data
    assert client.get("/").status_code == 302


@pytest.mark.parametrize("path", ["/login", "/logout", "/set_rtsp", "/upload_image", "/upload_video"])
def test_missing_csrf_is_rejected(signed_in, path):
    assert signed_in.post(path).status_code == 400


def test_old_csrf_token_invalidated_on_login(client):
    client.get("/login")
    old_token = csrf(client)
    client.post("/login", data={"username": "test-operator", "password": "synthetic-test-password", "csrf_token": old_token})
    assert client.post("/set_rtsp", data={"rtsp_url": "0", "csrf_token": old_token}).status_code == 400


@pytest.mark.parametrize("source", ["", "/etc/passwd", "file:///etc/passwd", "http://localhost", "rtsp://", "rtsp://camera:bad"])
def test_unsafe_camera_sources_rejected(signed_in, source):
    assert signed_in.post("/set_rtsp", data={"rtsp_url": source, "csrf_token": csrf(signed_in)}).status_code == 400


def test_camera_allowlist(application, signed_in, monkeypatch):
    monkeypatch.setenv("RTSP_ALLOWED_HOSTS", "camera.example")
    for source, expected in [("rtsp://camera.example/live", 200), ("rtsp://other.example/live", 400), ("0", 200)]:
        response = signed_in.post("/set_rtsp", data={"rtsp_url": source, "csrf_token": csrf(signed_in)})
        assert response.status_code == expected
    assert application.current_source["path"] == "0"


def test_image_validation_and_fixed_upload_path(application, signed_in):
    invalid = signed_in.post("/upload_image", data={"image": (BytesIO(b"invalid"), "image.jpg"), "csrf_token": csrf(signed_in)})
    assert invalid.status_code == 400
    image = BytesIO()
    Image.new("RGB", (8, 8)).save(image, format="PNG")
    image.seek(0)
    valid = signed_in.post("/upload_image", data={"image": (image, "../../outside.png"), "csrf_token": csrf(signed_in)})
    assert valid.status_code == 200
    assert Path(application.current_source["path"]).parent == Path(application.UPLOAD_FOLDER)


def test_oversized_upload_rejected(signed_in):
    response = signed_in.post("/upload_image", data={"image": (BytesIO(b"x" * (1024 * 1024 + 1)), "large.jpg"), "csrf_token": csrf(signed_in)})
    assert response.status_code == 413


def test_video_validation_keeps_existing_file(application, signed_in, monkeypatch):
    current = Path(application.UPLOAD_FOLDER) / "current_video.mp4"
    current.write_bytes(b"previous-upload")
    cap = SimpleNamespace(isOpened=lambda: False, release=lambda: None)
    monkeypatch.setitem(sys.modules, "cv2", SimpleNamespace(VideoCapture=lambda path: cap))
    response = signed_in.post("/upload_video", data={"video": (BytesIO(b"invalid"), "clip.mp4"), "csrf_token": csrf(signed_in)})
    assert response.status_code == 400
    assert current.read_bytes() == b"previous-upload"
    assert list(Path(application.UPLOAD_FOLDER).iterdir()) == [current]


def test_valid_video_replaces_current_file(application, signed_in, monkeypatch):
    released = []
    cap = SimpleNamespace(isOpened=lambda: True, read=lambda: (True, object()), release=lambda: released.append(True))
    monkeypatch.setitem(sys.modules, "cv2", SimpleNamespace(VideoCapture=lambda path: cap))
    response = signed_in.post("/upload_video", data={"video": (BytesIO(b"synthetic-video"), "clip.mp4"), "csrf_token": csrf(signed_in)})
    assert response.status_code == 200
    assert released == [True]
    assert Path(application.current_source["path"]).read_bytes() == b"synthetic-video"


def test_database_initialization_preserves_existing_rows(tmp_path):
    path = tmp_path / "new" / "plates.db"
    create_database(path)
    with sqlite3.connect(path) as conn:
        conn.execute("INSERT INTO plates (plate) VALUES (?)", ("synthetic-plate",))
    create_database(path)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM plates").fetchone()[0] == 1


def test_failed_video_save_removes_temporary_file(application, signed_in, monkeypatch):
    from werkzeug.datastructures import FileStorage

    monkeypatch.setitem(sys.modules, "cv2", SimpleNamespace())

    def fail(*args, **kwargs):
        raise OSError("synthetic storage failure")

    monkeypatch.setattr(FileStorage, "save", fail)
    with pytest.raises(OSError):
        signed_in.post("/upload_video", data={"video": (BytesIO(b"synthetic-video"), "clip.mp4"), "csrf_token": csrf(signed_in)})
    assert list(Path(application.UPLOAD_FOLDER).iterdir()) == []


def test_duplicate_window_and_latest_plate(application):
    now = datetime.now(timezone.utc)
    assert application.record_plate("synthetic-A", now)
    assert not application.record_plate("synthetic-A", now + timedelta(seconds=5))
    assert not application.record_plate("synthetic-A", now + timedelta(seconds=20))
    assert application.record_plate("synthetic-B", now + timedelta(seconds=21))
    assert not application.record_plate("synthetic-A", now + timedelta(seconds=22))
    assert application.record_plate("synthetic-A", now + timedelta(minutes=6))
    assert application.latest_plate == "synthetic-A"
    with sqlite3.connect(application.DB_CONFIG["database"]) as conn:
        assert conn.execute("SELECT COUNT(*) FROM plates").fetchone()[0] == 3


def test_connection_failure_does_not_mask_original_error(application, monkeypatch):
    def fail(*args, **kwargs):
        raise sqlite3.OperationalError("synthetic failure")
    monkeypatch.setattr(application.sqlite3, "connect", fail)
    assert not application.record_plate("synthetic", datetime.now(timezone.utc))


def test_legacy_sqlite_timestamps_honor_duplicate_window(application):
    now = datetime.now(timezone.utc)
    with sqlite3.connect(application.DB_CONFIG["database"]) as conn:
        conn.execute("INSERT INTO plates (plate, time_detected) VALUES (?, ?)",
                     ("synthetic-legacy", now.strftime("%Y-%m-%d %H:%M:%S")))
    assert not application.record_plate("synthetic-legacy", now + timedelta(seconds=20))
    assert application.record_plate("synthetic-legacy", now + timedelta(minutes=6))


def test_empty_detections_do_not_index_first_box(application, monkeypatch):
    class EmptyBoxes:
        def __len__(self):
            return 0
    monkeypatch.setitem(sys.modules, "cv2", SimpleNamespace(cvtColor=lambda frame, code: frame, COLOR_BGR2RGB=1))
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace())
    monkeypatch.setattr(application.Image, "fromarray", lambda frame: frame)
    application.model_manager.plate_detector = lambda frame: [SimpleNamespace(boxes=EmptyBoxes())]
    application.process_frame(object())
    assert application.model_manager.ocr_model is None


@pytest.mark.parametrize("mode", ["disconnect", "failure", "end", "unopened"])
def test_video_capture_released_on_all_exit_paths(application, monkeypatch, mode, caplog):
    opened_paths, released = [], []
    reads = iter([(True, object()), (False, None)])
    cap = SimpleNamespace(isOpened=lambda: mode != "unopened", read=lambda: next(reads), release=lambda: released.append(True))
    def capture(path):
        opened_paths.append(path)
        return cap
    fake = SimpleNamespace(VideoCapture=capture, imencode=lambda ext, frame: (True, SimpleNamespace(tobytes=lambda: b"jpeg")))
    monkeypatch.setitem(sys.modules, "cv2", fake)
    def process(frame):
        if mode == "failure":
            raise RuntimeError("sensitive-backend-detail")
    monkeypatch.setattr(application, "process_frame", process)
    feed = application.generate_video_feed()
    if mode == "disconnect":
        assert b"Content-Type: image/jpeg" in next(feed)
        feed.close()
    else:
        list(feed)
    assert opened_paths == [0]
    assert released == [True]
    assert "sensitive-backend-detail" not in caplog.text


def test_license_and_corresponding_source_links(client):
    response = client.get("/login")
    assert b"https://example.org/source" in response.data
    assert b'"/license"' in response.data
    assert b"GNU AFFERO GENERAL PUBLIC LICENSE" in client.get("/license").data
