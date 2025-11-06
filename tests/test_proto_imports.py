"""Tests for proto_imports.py fix module."""

from pathlib import Path

from docuchango.fixes.proto_imports import ProtoImportFixer


class TestProtoImportFixerInit:
    """Test ProtoImportFixer initialization."""

    def test_init_with_default_path(self):
        """Test initialization with default path."""
        fixer = ProtoImportFixer()
        assert fixer.proto_dir == Path("proto-public/go")
        assert fixer.hashicorp_dir == Path("proto-public/go/hashicorp")

    def test_init_with_custom_path(self, tmp_path):
        """Test initialization with custom path."""
        custom_dir = tmp_path / "custom"
        fixer = ProtoImportFixer(proto_dir=custom_dir)
        assert fixer.proto_dir == custom_dir
        assert fixer.hashicorp_dir == custom_dir / "hashicorp"


class TestProtoImportFixerFindFiles:
    """Test finding .pb.go files."""

    def test_find_pb_files_nonexistent_dir(self, tmp_path):
        """Test finding files when directory doesn't exist."""
        fixer = ProtoImportFixer(proto_dir=tmp_path / "nonexistent")
        files = fixer.find_pb_files()
        assert files == []

    def test_find_pb_files_empty_dir(self, tmp_path):
        """Test finding files in empty directory."""
        hashicorp_dir = tmp_path / "hashicorp"
        hashicorp_dir.mkdir(parents=True)
        fixer = ProtoImportFixer(proto_dir=tmp_path)
        files = fixer.find_pb_files()
        assert files == []

    def test_find_pb_files_with_files(self, tmp_path):
        """Test finding .pb.go files."""
        hashicorp_dir = tmp_path / "hashicorp"
        hashicorp_dir.mkdir(parents=True)

        # Create some .pb.go files
        (hashicorp_dir / "file1.pb.go").write_text("// content")
        (hashicorp_dir / "file2.pb.go").write_text("// content")
        # Create non-.pb.go file
        (hashicorp_dir / "other.go").write_text("// content")

        fixer = ProtoImportFixer(proto_dir=tmp_path)
        files = fixer.find_pb_files()
        assert len(files) == 2
        assert all(f.suffix == ".go" and ".pb.go" in f.name for f in files)

    def test_find_pb_files_recursive(self, tmp_path):
        """Test finding .pb.go files in subdirectories."""
        hashicorp_dir = tmp_path / "hashicorp"
        sub_dir = hashicorp_dir / "api" / "v1"
        sub_dir.mkdir(parents=True)

        (hashicorp_dir / "file1.pb.go").write_text("// content")
        (sub_dir / "file2.pb.go").write_text("// content")

        fixer = ProtoImportFixer(proto_dir=tmp_path)
        files = fixer.find_pb_files()
        assert len(files) == 2


class TestProtoImportFixerFixFile:
    """Test fixing imports in files."""

    def test_fix_google_api_import(self, tmp_path):
        """Test fixing google/api import."""
        test_file = tmp_path / "test.pb.go"
        content = """package test
import "github.com/hashicorp/cloud-agf-devportal/proto-public/go/google/api"
"""
        test_file.write_text(content, encoding="utf-8")

        fixer = ProtoImportFixer(proto_dir=tmp_path)
        modified, count = fixer.fix_file(test_file)

        assert modified is True
        assert count == 1

        result = test_file.read_text(encoding="utf-8")
        assert "google.golang.org/genproto/googleapis/api" in result
        assert "hashicorp" not in result

    def test_fix_google_rpc_import(self, tmp_path):
        """Test fixing google/rpc import."""
        test_file = tmp_path / "test.pb.go"
        content = """package test
import "github.com/hashicorp/cloud-agf-devportal/proto-public/go/google/rpc"
"""
        test_file.write_text(content, encoding="utf-8")

        fixer = ProtoImportFixer(proto_dir=tmp_path)
        modified, count = fixer.fix_file(test_file)

        assert modified is True
        assert count == 1

        result = test_file.read_text(encoding="utf-8")
        assert "google.golang.org/genproto/googleapis/rpc" in result

    def test_fix_buf_validate_import(self, tmp_path):
        """Test fixing buf/validate import."""
        test_file = tmp_path / "test.pb.go"
        content = """package test
import "github.com/hashicorp/cloud-agf-devportal/proto-public/go/buf/validate"
"""
        test_file.write_text(content, encoding="utf-8")

        fixer = ProtoImportFixer(proto_dir=tmp_path)
        modified, count = fixer.fix_file(test_file)

        assert modified is True
        assert count == 1

        result = test_file.read_text(encoding="utf-8")
        assert "buf.build/gen/go/bufbuild/protovalidate/protocolbuffers/go/buf/validate" in result

    def test_fix_multiple_imports(self, tmp_path):
        """Test fixing multiple imports in one file."""
        test_file = tmp_path / "test.pb.go"
        content = """package test
import (
    "github.com/hashicorp/cloud-agf-devportal/proto-public/go/google/api"
    "github.com/hashicorp/cloud-agf-devportal/proto-public/go/google/rpc"
    "github.com/hashicorp/cloud-agf-devportal/proto-public/go/buf/validate"
)
"""
        test_file.write_text(content, encoding="utf-8")

        fixer = ProtoImportFixer(proto_dir=tmp_path)
        modified, count = fixer.fix_file(test_file)

        assert modified is True
        assert count == 3

        result = test_file.read_text(encoding="utf-8")
        assert "google.golang.org/genproto/googleapis/api" in result
        assert "google.golang.org/genproto/googleapis/rpc" in result
        assert "buf.build/gen/go/bufbuild/protovalidate" in result
        assert "hashicorp" not in result

    def test_fix_duplicate_imports(self, tmp_path):
        """Test fixing duplicate imports."""
        test_file = tmp_path / "test.pb.go"
        content = """package test
import "github.com/hashicorp/cloud-agf-devportal/proto-public/go/google/api"
import "github.com/hashicorp/cloud-agf-devportal/proto-public/go/google/api"
"""
        test_file.write_text(content, encoding="utf-8")

        fixer = ProtoImportFixer(proto_dir=tmp_path)
        modified, count = fixer.fix_file(test_file)

        assert modified is True
        assert count == 2  # Both occurrences replaced

    def test_no_changes_needed(self, tmp_path):
        """Test file with already correct imports."""
        test_file = tmp_path / "test.pb.go"
        content = """package test
import "google.golang.org/genproto/googleapis/api"
"""
        test_file.write_text(content, encoding="utf-8")

        fixer = ProtoImportFixer(proto_dir=tmp_path)
        modified, count = fixer.fix_file(test_file)

        assert modified is False
        assert count == 0

        # File should not be modified
        result = test_file.read_text(encoding="utf-8")
        assert result == content

    def test_preserve_other_imports(self, tmp_path):
        """Test that non-matching imports are preserved."""
        test_file = tmp_path / "test.pb.go"
        content = """package test
import (
    "context"
    "github.com/hashicorp/cloud-agf-devportal/proto-public/go/google/api"
    "google.golang.org/grpc"
)
"""
        test_file.write_text(content, encoding="utf-8")

        fixer = ProtoImportFixer(proto_dir=tmp_path)
        modified, count = fixer.fix_file(test_file)

        assert modified is True
        assert count == 1

        result = test_file.read_text(encoding="utf-8")
        assert "context" in result
        assert "google.golang.org/grpc" in result

    def test_empty_file(self, tmp_path):
        """Test empty file handling."""
        test_file = tmp_path / "test.pb.go"
        test_file.write_text("", encoding="utf-8")

        fixer = ProtoImportFixer(proto_dir=tmp_path)
        modified, count = fixer.fix_file(test_file)

        assert modified is False
        assert count == 0

    def test_unicode_content_preserved(self, tmp_path):
        """Test Unicode content is preserved."""
        test_file = tmp_path / "test.pb.go"
        content = """package test
// Comment with Unicode: 中文 → ✓
import "github.com/hashicorp/cloud-agf-devportal/proto-public/go/google/api"
"""
        test_file.write_text(content, encoding="utf-8")

        fixer = ProtoImportFixer(proto_dir=tmp_path)
        fixer.fix_file(test_file)

        result = test_file.read_text(encoding="utf-8")
        assert "中文" in result
        assert "→" in result
        assert "✓" in result

    def test_fix_import_in_code_body(self, tmp_path):
        """Test fixing imports that appear in code body (edge case)."""
        test_file = tmp_path / "test.pb.go"
        content = """package test
import "github.com/hashicorp/cloud-agf-devportal/proto-public/go/google/api"

// Reference to github.com/hashicorp/cloud-agf-devportal/proto-public/go/google/api
var x = "github.com/hashicorp/cloud-agf-devportal/proto-public/go/google/api"
"""
        test_file.write_text(content, encoding="utf-8")

        fixer = ProtoImportFixer(proto_dir=tmp_path)
        modified, count = fixer.fix_file(test_file)

        # Should replace all occurrences (import + comment + string)
        assert modified is True
        assert count == 3

    def test_file_with_no_imports(self, tmp_path):
        """Test file with no imports."""
        test_file = tmp_path / "test.pb.go"
        content = """package test

func main() {
    println("hello")
}
"""
        test_file.write_text(content, encoding="utf-8")

        fixer = ProtoImportFixer(proto_dir=tmp_path)
        modified, count = fixer.fix_file(test_file)

        assert modified is False
        assert count == 0


class TestProtoImportFixerReplacements:
    """Test the replacement patterns."""

    def test_all_replacements_defined(self):
        """Test that all expected replacements are defined."""
        fixer = ProtoImportFixer()
        assert len(fixer.REPLACEMENTS) == 3

        patterns = [pattern for pattern, _ in fixer.REPLACEMENTS]
        assert any("google/api" in p for p in patterns)
        assert any("google/rpc" in p for p in patterns)
        assert any("buf/validate" in p for p in patterns)

    def test_replacement_targets(self):
        """Test that replacements have correct targets."""
        fixer = ProtoImportFixer()
        replacements = dict(fixer.REPLACEMENTS)

        # Check the targets are what we expect
        assert any("google.golang.org" in v for v in replacements.values())
        assert any("buf.build" in v for v in replacements.values())
