import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest

from ai_model.data import acquire


def test_default_download_directory_stays_in_repository():
    assert acquire.DEFAULT_DATA == Path(__file__).resolve().parents[1] / "data/ham10000"


def test_regional_probe_requires_the_expected_source_range(monkeypatch, capsys):
    import sys

    monkeypatch.setattr(acquire, "BASE", acquire.BASE)
    monkeypatch.setattr(sys, "argv", ["acquire", "--probe", "--regional-endpoint"])
    def respond(request, **kwargs):
        assert request.full_url.startswith(acquire.REGIONAL_BASE)
        return Response(b"x" * 1024**2, status=206, headers={"Content-Range": "bytes 0-1048575/2771732744", "ETag": '"test-only-source"'})
    monkeypatch.setattr(acquire.urllib.request, "urlopen", respond)
    assert acquire.main() == 0
    report = json.loads(capsys.readouterr().out)
    assert report["bytes"] == 1024**2 and report["etag"] == '"test-only-source"'


class Response(io.BytesIO):
    def __init__(self, content, status=200, headers=None):
        super().__init__(content)
        self.status = status
        self.headers = headers or {"Content-Length": str(len(content)), "ETag": '"fixture-etag"'}


def test_download_receipt_and_changed_cache_rejection(tmp_path, monkeypatch):
    target = tmp_path / "fixture.bin"
    monkeypatch.setattr(acquire.urllib.request, "urlopen", lambda *args, **kwargs: Response(b"synthetic-download-fixture"))
    receipt = acquire.download("fixture.bin", target)
    assert receipt["sha256"] == hashlib.sha256(target.read_bytes()).hexdigest()
    monkeypatch.setattr(acquire.urllib.request, "urlopen", lambda *args, **kwargs: pytest.fail("Verified cache must not redownload"))
    assert acquire.download("fixture.bin", target) == receipt
    target.write_bytes(b"changed")
    with pytest.raises(ValueError, match="Checksum mismatch"):
        acquire.download("fixture.bin", target)


def test_partial_download_resumes_with_verified_range(tmp_path, monkeypatch):
    target = tmp_path / "fixture.bin"
    target.with_name("fixture.bin.part").write_bytes(b"abc")
    target.with_name("fixture.bin.part.json").write_text(json.dumps({"etag": '"fixture-etag"'}))
    def response(request, **kwargs):
        assert request.get_header("Range") == "bytes=3-"
        assert request.get_header("If-range") == '"fixture-etag"'
        return Response(b"def", status=206, headers={"Content-Range": "bytes 3-5/6", "Content-Length": "3", "ETag": '"fixture-etag"'})
    monkeypatch.setattr(acquire.urllib.request, "urlopen", response)
    acquire.download("fixture.bin", target)
    assert target.read_bytes() == b"abcdef"


def test_wrong_partial_range_does_not_replace_saved_bytes(tmp_path, monkeypatch):
    target = tmp_path / "fixture.bin"
    partial = target.with_name("fixture.bin.part")
    partial.write_bytes(b"abc")
    target.with_name("fixture.bin.part.json").write_text(json.dumps({"etag": '"fixture-etag"'}))
    monkeypatch.setattr(acquire.urllib.request, "urlopen", lambda *args, **kwargs: Response(b"bad", status=206, headers={"Content-Range": "bytes 0-2/6", "Content-Length": "3"}))
    with pytest.raises(ValueError, match="Content-Range"):
        acquire.download("fixture.bin", target)
    assert partial.read_bytes() == b"abc"
    assert not target.exists()


def test_ranged_download_preserves_prefix_and_joins_exact_ranges(tmp_path, monkeypatch):
    target = tmp_path / "fixture.bin"
    content = b"abcdefghijkl"
    target.with_name("fixture.bin.part").write_bytes(content[:3])
    target.with_name("fixture.bin.part.json").write_text(json.dumps({"etag": '"fixture-etag"', "bytes_expected": len(content)}))
    def respond(request, **kwargs):
        if request.get_method() == "HEAD":
            return Response(b"", headers={"Content-Length": str(len(content)), "ETag": '"fixture-etag"'})
        start, end = map(int, request.get_header("Range").removeprefix("bytes=").split("-"))
        assert request.get_header("If-match") == '"fixture-etag"'
        return Response(content[start:end + 1], status=206, headers={"Content-Range": f"bytes {start}-{end}/{len(content)}", "ETag": '"fixture-etag"'})
    monkeypatch.setattr(acquire.urllib.request, "urlopen", respond)
    receipt = acquire.download_parallel("fixture.bin", target, workers=2, chunk_size=3)
    assert target.read_bytes() == content
    assert receipt["sha256"] == hashlib.sha256(content).hexdigest()


def test_zip_path_traversal_rejected(tmp_path):
    archive_path = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../outside.txt", "unsafe")
        archive.writestr("images/ISIC_0000001.jpg", b"fixture")
    with pytest.raises(ValueError, match="Unsafe archive"):
        acquire.extract_images(archive_path, tmp_path / "images")
    assert not (tmp_path / "outside.txt").exists()


def test_duplicate_archive_basenames_rejected(tmp_path):
    archive_path = tmp_path / "duplicate.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("a/ISIC_0000001.jpg", b"first")
        archive.writestr("b/ISIC_0000001.jpg", b"second")
    with pytest.raises(ValueError, match="Duplicate image"):
        acquire.extract_images(archive_path, tmp_path / "images")


def test_official_label_group_join_requires_one_to_one_mapping(tmp_path):
    truth = "image,MEL,NV,BCC,AKIEC,BKL,DF,VASC\nISIC_0000001,0,1,0,0,0,0,0\n"
    with zipfile.ZipFile(tmp_path / acquire.TRUTH, "w") as archive:
        archive.writestr(acquire.TRUTH.replace(".zip", ".csv"), truth)
    (tmp_path / acquire.GROUPS).write_text("image,lesion_id,diagnosis_confirm_type\nISIC_0000001,lesion1,synthetic\n")
    target = tmp_path / "joined.csv"
    assert acquire.canonical_metadata(tmp_path, target) == 1
    with target.open() as handle:
        row = next(csv.DictReader(handle))
    assert row["dx"] == "nv" and row["lesion_id"] == "lesion1"
    (tmp_path / acquire.GROUPS).write_text("image,lesion_id,diagnosis_confirm_type\nISIC_0000002,lesion2,synthetic\n")
    with pytest.raises(ValueError, match="one-to-one"):
        acquire.canonical_metadata(tmp_path, target)
