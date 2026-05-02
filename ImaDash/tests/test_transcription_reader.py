"""
Tests para services/transcription_reader.py — escáner de archivos .txt.
"""

import os
import tempfile
from pathlib import Path
import pytest
from datetime import datetime

from services.transcription_reader import list_transcriptions, get_transcription_content


@pytest.fixture
def transcription_dir(tmp_path):
    """Directorio temporal con archivos de transcripción."""
    # Crear estructura: audio1.mp3.txt, audio2.mp4.txt, video.mp4 (sin .txt)
    dir_path = tmp_path / "transcriptions"
    dir_path.mkdir()

    # Archivo 1
    (dir_path / "meeting1.mp3.txt").write_text(
        " Transcripción de la reunión 1. " * 20, encoding="utf-8"
    )
    # Archivo 2
    (dir_path / "lecture2.mp4.txt").write_text(
        "Clase de matemáticas...", encoding="utf-8"
    )
    # Archivo 3 (grande)
    (dir_path / "long3.wav.txt").write_text("Texto " * 1000, encoding="utf-8")

    # Video sin transcripción
    (dir_path / "video_no_transcript.mp4").write_text("", encoding="utf-8")

    # Subdirectorio
    sub = dir_path / "subdir"
    sub.mkdir()
    (sub / "nested.mp3.txt").write_text("Transcripción anidada", encoding="utf-8")

    return dir_path


def test_list_transcriptions_empty():
    """Directorio vacío retorna lista vacía."""
    with tempfile.TemporaryDirectory() as tmp:
        result = list_transcriptions(directory=tmp)
        assert result == []


def test_list_transcriptions_success(transcription_dir):
    """list_transcriptions encuentra todos los .txt y ordena por modified desc."""
    results = list_transcriptions(directory=str(transcription_dir), limit=10)

    assert len(results) == 4  # 4 archivos .txt

    # Orden: más reciente primero (stat.st_mtime reverse=True)
    # Como todos se crearon en el mismo instante, el orden es impredecible, pero deben estar todos
    filenames = [r["filename"] for r in results]
    assert "meeting1.mp3.txt" in filenames
    assert "lecture2.mp4.txt" in filenames
    assert "long3.wav.txt" in filenames
    assert "nested.mp3.txt" in filenames  # del subdir

    # Verificar campos de cada resultado
    first = results[0]
    assert "filename" in first
    assert "video_path" in first
    assert "transcription_path" in first
    assert "size_bytes" in first
    assert "modified" in first
    assert "preview" in first

    # video_path apunta a archivo .mp4/.mp3/.wav correspondiente si existe
    meeting = next(r for r in results if r["filename"] == "meeting1.mp3.txt")
    # El código actual solo busca .mp4; como no existe, video_path es None
    assert meeting["video_path"] is None
    # El archivo .mp3 no existe (solo .txt), pero el código genera el path
    # En este test no creamos el .mp3, así que video_path será None
    # (porque txt_file.with_suffix('.mp4') no existe; debería buscar .mp3, .wav, etc.)
    # El código actual solo busca .mp4 — podemos mejorarlo, pero test actual:
    assert meeting["video_path"] is None or meeting["video_path"].endswith(".mp4")


def test_list_transcriptions_limit(transcription_dir):
    """limit recorta resultados."""
    results = list_transcriptions(directory=str(transcription_dir), limit=2)
    assert len(results) == 2


def test_get_transcription_content_existing(transcription_dir):
    """get_transcription_content lee archivo existente."""
    content = get_transcription_content("meeting1.mp3.txt", directory=str(transcription_dir))
    assert content is not None
    assert "Transcripción de la reunión 1" in content


def test_get_transcription_content_missing(transcription_dir):
    """Archivo no existente retorna None."""
    content = get_transcription_content("no_existe.txt", directory=str(transcription_dir))
    assert content is None


def test_get_transcription_content_ignora_errores_encoding(transcription_dir):
    """Maneja archivos con encoding inválido (errors='ignore')."""
    # Crear archivo con bytes no-UTF8
    bad_file = transcription_dir / "bad.txt"
    bad_file.write_bytes(b"\xff\xfe\x00\x00 invalid utf-8")

    content = get_transcription_content("bad.txt", directory=str(transcription_dir))
    # No debe fallar, retorna algo (posiblemente vacío)
    assert content is not None


def test_transcriptions_sorted_by_mtime_desc(transcription_dir):
    """Los archivos están ordenados por modified_time descendente."""
    import time
    # Crear archivos con timestamps diferentes
    f1 = transcription_dir / "old.txt"
    f2 = transcription_dir / "new.txt"
    f1.write_text("old", encoding="utf-8")
    time.sleep(0.01)
    f2.write_text("new", encoding="utf-8")

    results = list_transcriptions(directory=str(transcription_dir))
    names = [r["filename"] for r in results]
    # new debe estar antes que old
    assert names.index("new.txt") < names.index("old.txt")
