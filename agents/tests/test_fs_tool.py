"""
Tests for fs_tool (file system operations)

Migrated from tests/agents_legacy/test_fs_tool.py
High-value behavioral tests for file read/write security.
"""

import pytest
from pathlib import Path
from agents.tools.fs_tool import read_files, write_files


class TestWriteFiles:
    """Tests for write_files function."""

    def test_creates_file(self, tmp_path):
        """write_files should create file successfully."""
        changes = {"test.txt": "hello world"}
        write_files(tmp_path, changes)

        file_path = tmp_path / "test.txt"
        assert file_path.exists()
        assert file_path.read_text(encoding="utf-8") == "hello world"

    def test_creates_nested_directories(self, tmp_path):
        """write_files should create parent directories automatically."""
        changes = {"nested/dir/file.txt": "nested content"}
        write_files(tmp_path, changes)

        file_path = tmp_path / "nested" / "dir" / "file.txt"
        assert file_path.exists()
        assert file_path.read_text(encoding="utf-8") == "nested content"

    def test_path_traversal_blocked(self, tmp_path):
        """write_files should block path traversal attempts."""
        changes = {"../../etc/passwd": "malicious"}

        with pytest.raises(ValueError, match="escapes base directory"):
            write_files(tmp_path, changes)


class TestReadFiles:
    """Tests for read_files function."""

    def test_returns_content(self, tmp_path):
        """read_files should return correct content."""
        file_path = tmp_path / "sample.txt"
        file_path.write_text("test content", encoding="utf-8")

        result = read_files(tmp_path, ["sample.txt"])

        assert "sample.txt" in result
        assert result["sample.txt"] == "test content"

    def test_nonexistent_returns_empty(self, tmp_path):
        """read_files should return empty string for non-existent file."""
        result = read_files(tmp_path, ["nonexistent.txt"])

        assert "nonexistent.txt" in result
        assert result["nonexistent.txt"] == ""

    def test_path_traversal_returns_error(self, tmp_path):
        """read_files should return error for path traversal."""
        result = read_files(tmp_path, ["../../etc/passwd"])

        assert "../../etc/passwd" in result
        assert "ERROR" in result["../../etc/passwd"]
        assert "escapes base" in result["../../etc/passwd"]

    def test_multiple_files(self, tmp_path):
        """read_files should handle multiple files correctly."""
        (tmp_path / "file1.txt").write_text("content1", encoding="utf-8")
        (tmp_path / "file2.txt").write_text("content2", encoding="utf-8")

        result = read_files(tmp_path, ["file1.txt", "file2.txt"])

        assert len(result) == 2
        assert result["file1.txt"] == "content1"
        assert result["file2.txt"] == "content2"
