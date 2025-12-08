"""
Tests for fs_tool (file system operations)

Migrated from tests/agents_legacy/test_fs_tool.py
High-value behavioral tests for file read/write security.

Fix: P1-XX - 添加 dry_run 测试
"""

import pytest
from pathlib import Path
from agents.tools.fs_tool import read_files, write_files, WritePreview


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


class TestWriteFilesDryRun:
    """Tests for write_files dry_run mode (P1-XX fix)."""

    def test_dry_run_does_not_write_file(self, tmp_path):
        """dry_run=True should not create files on disk."""
        changes = {"should_not_exist.txt": "content"}
        preview = write_files(tmp_path, changes, dry_run=True)

        # File should NOT exist
        file_path = tmp_path / "should_not_exist.txt"
        assert not file_path.exists()

        # Preview should report correctly
        assert preview["files_to_write"] == 1
        assert preview["files_to_create"] == 1
        assert preview["files_to_update"] == 0

    def test_dry_run_returns_write_preview(self, tmp_path):
        """dry_run should return WritePreview structure."""
        changes = {
            "new_file.txt": "new content",
            "nested/dir/file.txt": "nested content",
        }
        preview = write_files(tmp_path, changes, dry_run=True)

        assert isinstance(preview, dict)
        assert "files_to_write" in preview
        assert "files_to_create" in preview
        assert "files_to_update" in preview
        assert "total_bytes" in preview
        assert "paths" in preview

        assert preview["files_to_write"] == 2
        assert preview["files_to_create"] == 2
        assert len(preview["paths"]) == 2

    def test_dry_run_detects_update_vs_create(self, tmp_path):
        """dry_run should distinguish between new files and updates."""
        # Create an existing file
        existing = tmp_path / "existing.txt"
        existing.write_text("old content", encoding="utf-8")

        changes = {
            "existing.txt": "updated content",
            "new_file.txt": "new content",
        }
        preview = write_files(tmp_path, changes, dry_run=True)

        assert preview["files_to_write"] == 2
        assert preview["files_to_create"] == 1
        assert preview["files_to_update"] == 1

        # Existing file should NOT be changed
        assert existing.read_text(encoding="utf-8") == "old content"

    def test_dry_run_calculates_bytes(self, tmp_path):
        """dry_run should calculate total bytes correctly."""
        changes = {"file.txt": "12345"}  # 5 bytes
        preview = write_files(tmp_path, changes, dry_run=True)

        assert preview["total_bytes"] == 5

    def test_dry_run_path_traversal_still_blocked(self, tmp_path):
        """dry_run mode should still block path traversal."""
        changes = {"../../../etc/passwd": "malicious"}

        with pytest.raises(ValueError, match="escapes base directory"):
            write_files(tmp_path, changes, dry_run=True)

    def test_dry_run_false_writes_file(self, tmp_path):
        """dry_run=False (default) should write files."""
        changes = {"real_file.txt": "real content"}
        preview = write_files(tmp_path, changes, dry_run=False)

        # File should exist
        file_path = tmp_path / "real_file.txt"
        assert file_path.exists()
        assert file_path.read_text(encoding="utf-8") == "real content"

        # Preview should match
        assert preview["files_to_write"] == 1


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
