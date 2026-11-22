from pathlib import Path

from config import settings
from core import watcher


def test_is_capture(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "HAND_REVIEW_DIR", tmp_path)
    assert watcher.is_capture(tmp_path / "ErrorGrave" / "a.png")
    assert watcher.is_capture(tmp_path / "OOP" / "b.JPG")
    assert not watcher.is_capture(tmp_path / "ErrorGrave" / "262442102849.txt")   # análisis IA
    assert not watcher.is_capture(tmp_path / "_archivo" / "a.png")                # no es spot
    assert not watcher.is_capture(tmp_path / "a.png")                             # raíz
    assert not watcher.is_capture(tmp_path / "ErrorGrave" / "sub" / "a.png")      # subcarpeta


def test_wait_until_stable(tmp_path, monkeypatch):
    monkeypatch.setattr(watcher, "STABLE_SECONDS", 1)
    f = tmp_path / "a.png"
    f.write_bytes(b"x" * 10)
    assert watcher.wait_until_stable(f)
    assert not watcher.wait_until_stable(tmp_path / "no_existe.png")


def test_pending_skips_processed(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "HAND_REVIEW_DIR", tmp_path)
    (tmp_path / "OOP").mkdir()
    done, todo = tmp_path / "OOP" / "done.png", tmp_path / "OOP" / "todo.png"
    for p in (done, todo):
        p.write_bytes(b"x")
    (tmp_path / "OOP" / "nota.txt").write_text("x")
    monkeypatch.setattr(watcher.state, "is_processed", lambda p: Path(p) == done)
    assert watcher.pending() == [todo]
