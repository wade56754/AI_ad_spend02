"""Unit tests for fs_tool."""

import pytest
from pathlib import Path
from agents.tools.fs_tool import read_files, write_files


def test_write_files_creates_file(tmp_path):
    """Test that write_files creates file successfully."""
    changes = {"test.txt": "hello world"}
    write_files(tmp_path, changes)

    file_path = tmp_path / "test.txt"
    assert file_path.exists()
    assert file_path.read_text(encoding="utf-8") == "hello world"


def test_read_files_returns_content(tmp_path):
    """Test that read_files returns correct content."""
    file_path = tmp_path / "sample.txt"
    file_path.write_text("test content", encoding="utf-8")

    result = read_files(tmp_path, ["sample.txt"])

    assert "sample.txt" in result
    assert result["sample.txt"] == "test content"


def test_read_files_nonexistent_returns_empty(tmp_path):
    """Test that read_files returns empty string for non-existent file."""
    result = read_files(tmp_path, ["nonexistent.txt"])

    assert "nonexistent.txt" in result
    assert result["nonexistent.txt"] == ""


def test_write_files_path_traversal_blocked(tmp_path):
    """Test that write_files blocks path traversal attempts."""
    changes = {"../../etc/passwd": "malicious"}

    with pytest.raises(ValueError, match="escapes base directory"):
        write_files(tmp_path, changes)


def test_read_files_path_traversal_returns_error(tmp_path):
    """Test that read_files returns error for path traversal."""
    result = read_files(tmp_path, ["../../etc/passwd"])

    assert "../../etc/passwd" in result
    assert "ERROR" in result["../../etc/passwd"]
    assert "escapes base" in result["../../etc/passwd"]


def test_write_files_creates_nested_directories(tmp_path):
    """Test that write_files creates parent directories automatically."""
    changes = {"nested/dir/file.txt": "nested content"}
    write_files(tmp_path, changes)

    file_path = tmp_path / "nested" / "dir" / "file.txt"
    assert file_path.exists()
    assert file_path.read_text(encoding="utf-8") == "nested content"


def test_read_files_multiple_files(tmp_path):
    """Test that read_files handles multiple files correctly."""
    (tmp_path / "file1.txt").write_text("content1", encoding="utf-8")
    (tmp_path / "file2.txt").write_text("content2", encoding="utf-8")

    result = read_files(tmp_path, ["file1.txt", "file2.txt"])

    assert len(result) == 2
    assert result["file1.txt"] == "content1"
    assert result["file2.txt"] == "content2"
