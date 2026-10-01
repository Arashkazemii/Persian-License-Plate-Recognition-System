import importlib.util
from pathlib import Path
import sys

import dotenv
import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def load_app(monkeypatch, tmp_path):
    # Never load a developer's .env or touch their database/uploads.
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: False)
    settings = {
        "SECRET_KEY": "synthetic-test-key-" + "x" * 32,
        "USER_1_USERNAME": "test-operator",
        "USER_1_PASSWORD": "synthetic-test-password",
        "USER_2_USERNAME": "",
        "USER_2_PASSWORD": "",
        "DB_PATH": str(tmp_path / "data" / "plates.db"),
        "RTSP_URL": "0",
        "RTSP_ALLOWED_HOSTS": "",
        "MAX_UPLOAD_MB": "1",
        "SESSION_COOKIE_SECURE": "false",
        "SOURCE_URL": "https://example.org/source",
    }
    for key, value in settings.items():
        monkeypatch.setenv(key, value)

    def load(**overrides):
        for key, value in overrides.items():
            monkeypatch.setenv(key, value)
        spec = importlib.util.spec_from_file_location("app", ROOT / "app.py")
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, "app", module)
        spec.loader.exec_module(module)
        module.app.config["TESTING"] = True
        module.UPLOAD_FOLDER = str(tmp_path / "uploads")
        Path(module.UPLOAD_FOLDER).mkdir(exist_ok=True)
        return module

    return load


@pytest.fixture
def application(load_app):
    return load_app()


@pytest.fixture
def client(application):
    return application.app.test_client()


def csrf(client):
    with client.session_transaction() as session:
        return session["csrf_token"]


@pytest.fixture
def signed_in(client):
    client.get("/login")
    response = client.post("/login", data={
        "username": "test-operator", "password": "synthetic-test-password",
        "csrf_token": csrf(client),
    })
    assert response.status_code == 302
    client.get("/")
    return client
