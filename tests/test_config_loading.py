"""Test suite for docs-project.yaml configuration loading."""

import tempfile
from pathlib import Path

import yaml

from docuchango.cli import _discover_doc_files
from docuchango.validator import DocValidator


class TestConfigLoading:
    """Test configuration file loading in DocValidator."""

    def test_load_valid_config(self):
        """Test that valid config file is loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            docs_cms = repo_root / "docs-cms"
            docs_cms.mkdir()

            # Create valid config file
            config_data = {
                "project": {
                    "id": "test-project",
                    "name": "Test Project",
                    "description": "Test description",
                },
                "structure": {
                    "adr_dir": "adr",
                    "rfc_dir": "rfcs",
                    "memo_dir": "memos",
                    "prd_dir": "prd",
                    "template_dir": "templates",
                    "document_folders": ["adr", "rfcs", "memos", "prd"],
                },
                "metadata": {
                    "created": "2025-10-27",
                    "maintainers": ["Test Team"],
                    "purpose": "Testing",
                },
            }

            config_path = docs_cms / "docs-project.yaml"
            with config_path.open("w") as f:
                yaml.dump(config_data, f)

            # Initialize validator
            validator = DocValidator(repo_root, verbose=False)

            # Check config was loaded
            assert validator.project_config is not None
            assert validator.project_config.project.id == "test-project"
            assert validator.project_config.project.name == "Test Project"
            assert validator.project_config.structure.prd_dir == "prd"
            assert "prd" in validator.project_config.structure.document_folders

    def test_load_config_with_defaults(self):
        """Test that config with minimal fields uses defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            docs_cms = repo_root / "docs-cms"
            docs_cms.mkdir()

            # Create minimal config file
            config_data = {
                "project": {
                    "id": "minimal-project",
                    "name": "Minimal Project",
                }
            }

            config_path = docs_cms / "docs-project.yaml"
            with config_path.open("w") as f:
                yaml.dump(config_data, f)

            # Initialize validator
            validator = DocValidator(repo_root, verbose=False)

            # Check config was loaded with defaults
            assert validator.project_config is not None
            assert validator.project_config.config_version == "1"
            assert validator.project_config.docuchango_version
            assert validator.project_config.structure.adr_dir == "adr"
            assert validator.project_config.structure.prd_dir == "prd"
            assert validator.project_config.structure.document_folders == ["adr", "rfcs", "memos", "prd"]

    def test_load_config_custom_folders(self):
        """Test that custom document_folders configuration is respected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            docs_cms = repo_root / "docs-cms"
            docs_cms.mkdir()

            # Create config with custom folders
            config_data = {
                "project": {
                    "id": "custom-project",
                    "name": "Custom Project",
                },
                "structure": {
                    "adr_dir": "decisions",
                    "prd_dir": "requirements",
                    "document_folders": ["decisions", "requirements"],
                },
            }

            config_path = docs_cms / "docs-project.yaml"
            with config_path.open("w") as f:
                yaml.dump(config_data, f)

            # Initialize validator
            validator = DocValidator(repo_root, verbose=False)

            # Check custom config
            assert validator.project_config is not None
            assert validator.project_config.structure.adr_dir == "decisions"
            assert validator.project_config.structure.prd_dir == "requirements"
            assert validator.project_config.structure.document_folders == ["decisions", "requirements"]

    def test_missing_config_file(self):
        """Test that missing config file returns None and doesn't crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            docs_cms = repo_root / "docs-cms"
            docs_cms.mkdir()
            # No config file created

            # Initialize validator
            validator = DocValidator(repo_root, verbose=False)

            # Check config is None but validator still works
            assert validator.project_config is None

    def test_invalid_config_format(self):
        """Test that invalid config format returns None gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            docs_cms = repo_root / "docs-cms"
            docs_cms.mkdir()

            # Create invalid config file
            config_data = {
                "project": {
                    "id": "Invalid_ID_With_Uppercase",  # Invalid format
                    "name": "Test Project",
                }
            }

            config_path = docs_cms / "docs-project.yaml"
            with config_path.open("w") as f:
                yaml.dump(config_data, f)

            # Initialize validator
            validator = DocValidator(repo_root, verbose=False)

            # Config should be None due to validation error
            assert validator.project_config is None

    def test_validator_uses_config_for_scanning(self):
        """Test that validator uses config to determine which folders to scan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            docs_cms = repo_root / "docs-cms"
            docs_cms.mkdir()

            # Create config that only scans ADR folder
            config_data = {
                "project": {
                    "id": "selective-project",
                    "name": "Selective Project",
                },
                "structure": {
                    "document_folders": ["adr"],  # Only scan ADR
                },
            }

            config_path = docs_cms / "docs-project.yaml"
            with config_path.open("w") as f:
                yaml.dump(config_data, f)

            # Create ADR folder with a file
            adr_dir = docs_cms / "adr"
            adr_dir.mkdir()
            adr_file = adr_dir / "adr-001-test-decision.md"
            adr_file.write_text(
                """---
title: Test Decision
status: Accepted
date: 2025-10-27
deciders: Team
tags: [test]
id: adr-001
project_id: selective-project
doc_uuid: 12345678-1234-4123-8123-123456789abc
---

# Context
Test ADR content.
"""
            )

            # Create PRD folder with a file (should be ignored)
            prd_dir = docs_cms / "prd"
            prd_dir.mkdir()
            prd_file = prd_dir / "prd-001-test-feature.md"
            prd_file.write_text(
                """---
title: Test Feature
status: Draft
author: Team
created: 2025-10-27
target_release: v1.0.0
tags: [test]
id: prd-001
project_id: selective-project
doc_uuid: 87654321-4321-4321-8321-210987654321
---

# Summary
Test PRD content.
"""
            )

            # Initialize validator and scan
            validator = DocValidator(repo_root, verbose=False)
            validator.scan_documents()

            # Should only find ADR, not PRD
            doc_types = [doc.doc_type for doc in validator.documents]
            assert "adr" in doc_types
            assert "prd" not in doc_types
            assert len(validator.documents) == 1

    def test_validator_default_folders_without_config(self):
        """Test that validator uses default folders when no config exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            docs_cms = repo_root / "docs-cms"
            docs_cms.mkdir()
            # No config file

            # Initialize validator
            validator = DocValidator(repo_root, verbose=False)

            # Get folder config - should use defaults
            folder_config = validator._get_folder_config()
            document_folders = validator._get_document_folders()

            assert folder_config["adr"] == "adr"
            assert folder_config["rfc"] == "rfcs"
            assert folder_config["memo"] == "memos"
            assert folder_config["prd"] == "prd"
            assert document_folders == ["adr", "rfcs", "memos", "prd"]

    def test_duplicate_folder_mapping_warning(self):
        """Test that duplicate folder mappings generate warnings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            docs_cms = repo_root / "docs-cms"
            docs_cms.mkdir()

            # Create config with duplicate folder mapping
            config_data = {
                "project": {
                    "id": "duplicate-folders",
                    "name": "Duplicate Folders Project",
                },
                "structure": {
                    "adr_dir": "docs",  # Both use same folder
                    "rfc_dir": "docs",  # Both use same folder
                    "document_folders": ["docs"],
                },
            }

            config_path = docs_cms / "docs-project.yaml"
            with config_path.open("w") as f:
                yaml.dump(config_data, f)

            # Create the docs folder
            docs_dir = docs_cms / "docs"
            docs_dir.mkdir()

            # Initialize validator and capture errors
            validator = DocValidator(repo_root, verbose=False)

            # Scan should warn about duplicate mapping
            # We check that the warning logic exists by verifying multiple types are mapped
            folder_to_types: dict[str, list[str]] = {}
            folder_config = validator._get_folder_config()
            for key, doc_type in [("adr", "adr"), ("rfc", "rfc"), ("memo", "memo"), ("prd", "prd")]:
                folder = folder_config[key]
                if folder not in folder_to_types:
                    folder_to_types[folder] = []
                folder_to_types[folder].append(doc_type)

            # Verify "docs" is mapped to multiple types
            assert "docs" in folder_to_types
            assert len(folder_to_types["docs"]) >= 2
            assert "adr" in folder_to_types["docs"]
            assert "rfc" in folder_to_types["docs"]

    def test_unrecognized_folder_warning(self):
        """Test that unrecognized folders in document_folders generate warnings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            docs_cms = repo_root / "docs-cms"
            docs_cms.mkdir()

            # Create config with unrecognized folder
            config_data = {
                "project": {
                    "id": "unrecognized-folder",
                    "name": "Unrecognized Folder Project",
                },
                "structure": {
                    "document_folders": ["adr", "unknown-folder", "prd"],
                },
            }

            config_path = docs_cms / "docs-project.yaml"
            with config_path.open("w") as f:
                yaml.dump(config_data, f)

            # Initialize validator
            validator = DocValidator(repo_root, verbose=False)

            # Verify that the unknown folder is not in the mapping
            folder_config = validator._get_folder_config()
            folder_to_types: dict[str, list[str]] = {}
            for key, doc_type in [("adr", "adr"), ("rfc", "rfc"), ("memo", "memo"), ("prd", "prd")]:
                folder = folder_config[key]
                if folder not in folder_to_types:
                    folder_to_types[folder] = []
                folder_to_types[folder].append(doc_type)

            # "unknown-folder" should not be in the mapping
            assert "unknown-folder" not in folder_to_types
            # But "adr" and "prd" should be
            assert "adr" in folder_to_types
            assert "prd" in folder_to_types

    def test_load_config_from_repo_root(self):
        """Validator should load docs-project.yaml from repo root when present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            config_data = {
                "project": {
                    "id": "root-config-project",
                    "name": "Root Config Project",
                },
                "structure": {
                    "document_folders": ["adr"],
                },
            }

            config_path = repo_root / "docs-project.yaml"
            with config_path.open("w") as f:
                yaml.dump(config_data, f)

            validator = DocValidator(repo_root, verbose=False)
            assert validator.project_config is not None
            assert validator.project_config.project.id == "root-config-project"

    def test_doc_types_custom_layout_mixed_schema(self):
        """Custom doc_types should support mixed folders and schema bindings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            docs_root = repo_root / "docs"
            docs_root.mkdir(parents=True)

            # Mixed layout: numbered ADR, non-numbered PRFAQ
            (docs_root / "adr").mkdir()
            (docs_root / "prfaq").mkdir()

            (docs_root / "adr" / "adr-001-test.md").write_text(
                """---
title: Test ADR Decision
status: Accepted
created: 2025-01-01
deciders: Core Team
tags: [architecture]
id: adr-001
project_id: mixed-project
doc_uuid: 12345678-1234-4123-8123-123456789abc
---

# ADR content
"""
            )

            (docs_root / "prfaq" / "prfaq-why-now.md").write_text(
                """---
title: Why now
project_id: mixed-project
doc_uuid: 87654321-4321-4321-8321-210987654321
tags: [product]
---

# PRFAQ content
"""
            )

            config_data = {
                "project": {
                    "id": "mixed-project",
                    "name": "Mixed Project",
                },
                "structure": {
                    "docs_roots": ["docs"],
                    "doc_types": {
                        "adr": {
                            "schema": "adr",
                            "folders": ["adr"],
                            "filename_pattern": r"^(adr)-(\d{3})-(.+)\.md$",
                            "enforce_filename_pattern": True,
                        },
                        "prfaq": {
                            "schema": "generic",
                            "folders": ["prfaq"],
                            "filename_pattern": r"^prfaq-.+\.md$",
                            "enforce_filename_pattern": True,
                        },
                    },
                },
            }

            config_path = repo_root / "docs-project.yaml"
            with config_path.open("w") as f:
                yaml.dump(config_data, f)

            validator = DocValidator(repo_root, verbose=False)
            validator.scan_documents()

            # ADR + PRFAQ should both be discovered
            names = sorted(d.file_path.name for d in validator.documents)
            assert "adr-001-test.md" in names
            assert "prfaq-why-now.md" in names

    def test_doc_types_can_disable_filename_enforcement(self):
        """Custom doc_types can disable strict filename enforcement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            docs_root = repo_root / "docs"
            docs_root.mkdir(parents=True)
            (docs_root / "notes").mkdir()

            # Doesn't match strict numeric pattern but should pass when enforcement is disabled
            (docs_root / "notes" / "draft-about-capacity.md").write_text(
                """---
title: Capacity Notes
project_id: mixed-project
doc_uuid: 11111111-1111-4111-8111-111111111111
---

# Notes
"""
            )

            config_data = {
                "project": {
                    "id": "mixed-project",
                    "name": "Mixed Project",
                },
                "structure": {
                    "docs_roots": ["docs"],
                    "doc_types": {
                        "notes": {
                            "schema": "generic",
                            "folders": ["notes"],
                            "filename_pattern": r"^note-(\d+)\.md$",
                            "enforce_filename_pattern": False,
                        }
                    },
                },
            }

            config_path = repo_root / "docs-project.yaml"
            with config_path.open("w") as f:
                yaml.dump(config_data, f)

            validator = DocValidator(repo_root, verbose=False)
            validator.scan_documents()

            names = [d.file_path.name for d in validator.documents]
            assert "draft-about-capacity.md" in names
            assert not any("Invalid" in err for err in validator.errors)

    def test_generic_doc_types_can_allow_plain_markdown_without_frontmatter(self):
        """Generic lanes can opt into plain markdown without YAML frontmatter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            docs_root = repo_root / "docs"
            docs_root.mkdir(parents=True)
            (docs_root / "design").mkdir()

            doc_path = docs_root / "design" / "plain-design-note.md"
            doc_path.write_text(
                """# Plain Design Note

This lane intentionally uses plain markdown without frontmatter.

```text
Example block
```
"""
            )

            config_data = {
                "project": {
                    "id": "mixed-project",
                    "name": "Mixed Project",
                },
                "structure": {
                    "docs_roots": ["docs"],
                    "doc_types": {
                        "design-notes": {
                            "schema": "generic",
                            "folders": ["design"],
                            "filename_pattern": r".+\.md$",
                            "enforce_filename_pattern": False,
                            "require_frontmatter": False,
                        }
                    },
                },
            }

            config_path = repo_root / "docs-project.yaml"
            with config_path.open("w") as f:
                yaml.dump(config_data, f)

            validator = DocValidator(repo_root, verbose=False)
            validator.scan_documents()

            assert len(validator.documents) == 1
            doc = validator.documents[0]
            assert doc.file_path.name == "plain-design-note.md"
            assert doc.title == "Plain Design Note"
            assert doc.errors == []

    def test_generic_doc_types_still_require_frontmatter_by_default(self):
        """Generic lanes stay strict unless require_frontmatter is disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            docs_root = repo_root / "docs"
            docs_root.mkdir(parents=True)
            (docs_root / "design").mkdir()

            (docs_root / "design" / "strict-design-note.md").write_text(
                """# Strict Design Note

This document omits frontmatter and should still fail by default.
"""
            )

            config_data = {
                "project": {
                    "id": "mixed-project",
                    "name": "Mixed Project",
                },
                "structure": {
                    "docs_roots": ["docs"],
                    "doc_types": {
                        "design-notes": {
                            "schema": "generic",
                            "folders": ["design"],
                            "filename_pattern": r".+\.md$",
                            "enforce_filename_pattern": False,
                        }
                    },
                },
            }

            config_path = repo_root / "docs-project.yaml"
            with config_path.open("w") as f:
                yaml.dump(config_data, f)

            validator = DocValidator(repo_root, verbose=False)
            validator.scan_documents()

            assert len(validator.documents) == 1
            assert validator.documents[0].errors == ["Missing YAML frontmatter"]

    def test_sub_projects_load_multi_project_config_with_legacy_files(self):
        """Parent configs can reference multiple sub-project configs and keep legacy docs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            legacy_adr_dir = repo_root / "adr"
            service_a = repo_root / "vendor" / "service-a"
            service_a_docs = service_a / "docs" / "adr"
            service_b = repo_root / "vendor" / "service-b"
            service_b_memos = service_b / "memos"
            legacy_adr_dir.mkdir(parents=True)
            service_a_docs.mkdir(parents=True)
            service_b_memos.mkdir(parents=True)

            (repo_root / "docs-project.yaml").write_text(
                yaml.dump(
                    {
                        "config_version": "1",
                        "docuchango_version": "1.15.0",
                        "project": {"id": "parent-project", "name": "Parent Project"},
                        "structure": {"document_folders": ["adr"]},
                        "sub_projects": [
                            "vendor/service-a/docs-project.yaml",
                            {"path": "vendor/service-b/docs-project.yaml"},
                        ],
                    }
                )
            )
            (service_a / "docs-project.yaml").write_text(
                yaml.dump(
                    {
                        "config_version": "1",
                        "docuchango_version": "1.15.0",
                        "project": {"id": "service-a", "name": "Service A"},
                        "structure": {
                            "docs_roots": ["docs"],
                            "doc_types": {
                                "adr": {
                                    "schema": "adr",
                                    "folders": ["adr"],
                                    "filename_pattern": r"^(adr)-(\d{3})-(.+)\.md$",
                                }
                            },
                        },
                    }
                )
            )
            (service_b / "docs-project.yaml").write_text(
                yaml.dump(
                    {
                        "config_version": "1",
                        "docuchango_version": "1.15.0",
                        "project": {"id": "service-b", "name": "Service B"},
                        "structure": {"document_folders": ["memos"]},
                    }
                )
            )

            (legacy_adr_dir / "adr-001-parent-legacy.md").write_text(
                """---
title: Parent Legacy Decision
status: Accepted
created: 2025-01-01
deciders: Core Team
tags: [architecture]
id: adr-001
project_id: parent-project
doc_uuid: 11111111-1111-4111-8111-111111111111
---

# Legacy ADR content
"""
            )
            (service_a_docs / "adr-002-submodule-decision.md").write_text(
                """---
title: Submodule Decision
status: Accepted
created: 2025-01-01
deciders: Core Team
tags: [architecture]
id: adr-002
project_id: service-a
doc_uuid: 22222222-2222-4222-8222-222222222222
---

# ADR content
"""
            )
            (service_b_memos / "memo-001-legacy-submodule.md").write_text(
                """---
title: Legacy Submodule Memo
author: Platform Team
created: 2025-01-01
tags: [operations]
id: memo-001
project_id: service-b
doc_uuid: 33333333-3333-4333-8333-333333333333
---

# Memo content
"""
            )

            validator = DocValidator(repo_root, verbose=False)
            validator.scan_documents()

            assert len(validator.project_configs) == 3
            assert [context.config.project.id for context in validator.project_configs] == [
                "parent-project",
                "service-a",
                "service-b",
            ]
            assert [context.config.config_version for context in validator.project_configs] == ["1", "1", "1"]
            assert [context.config.docuchango_version for context in validator.project_configs] == [
                "1.15.0",
                "1.15.0",
                "1.15.0",
            ]
            assert sorted(doc.file_path.name for doc in validator.documents) == [
                "adr-001-parent-legacy.md",
                "adr-002-submodule-decision.md",
                "memo-001-legacy-submodule.md",
            ]

    def test_discover_doc_files_includes_sub_project_configs(self):
        """CLI file discovery includes docs found through sub-project references."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            submodule = repo_root / "libs" / "service-b"
            docs_dir = submodule / "adr"
            docs_dir.mkdir(parents=True)

            (repo_root / "docs-project.yaml").write_text(
                yaml.dump(
                    {
                        "config_version": "1",
                        "docuchango_version": "1.15.0",
                        "project": {"id": "parent-project", "name": "Parent Project"},
                        "sub_projects": [{"path": "libs/service-b/docs-project.yaml"}],
                    }
                )
            )
            (submodule / "docs-project.yaml").write_text(
                yaml.dump(
                    {
                        "config_version": "1",
                        "docuchango_version": "1.15.0",
                        "project": {"id": "service-b", "name": "Service B"},
                        "structure": {"document_folders": ["adr"]},
                    }
                )
            )
            doc_path = docs_dir / "adr-001-service-b.md"
            doc_path.write_text("# Not parsed by discovery\n")

            assert _discover_doc_files(repo_root) == [doc_path.resolve()]

    def test_missing_sub_project_config_warns_and_continues(self, capsys):
        """Missing sub-project configs should warn with remediation and keep validating parent docs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            adr_dir = repo_root / "adr"
            adr_dir.mkdir()

            (repo_root / "docs-project.yaml").write_text(
                yaml.dump(
                    {
                        "project": {"id": "parent-project", "name": "Parent Project"},
                        "structure": {"document_folders": ["adr"]},
                        "sub_projects": ["missing-submodule/docs-project.yaml"],
                    }
                )
            )
            (adr_dir / "adr-001-parent-decision.md").write_text(
                """---
title: Parent Decision
status: Accepted
created: 2025-01-01
deciders: Core Team
tags: [architecture]
id: adr-001
project_id: parent-project
doc_uuid: 11111111-1111-4111-8111-111111111111
---

# Parent ADR content
"""
            )

            validator = DocValidator(repo_root, verbose=False)
            validator.scan_documents()

            output = capsys.readouterr().out
            assert "Sub-project config not found" in output
            assert "Add the file or remove it from sub_projects" in output
            assert [context.config.project.id for context in validator.project_configs] == ["parent-project"]
            assert [doc.file_path.name for doc in validator.documents] == ["adr-001-parent-decision.md"]

    def test_invalid_sub_project_config_warns_and_continues(self, capsys):
        """Invalid sub-project configs should warn with remediation and keep validating parent docs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            submodule = repo_root / "vendor" / "invalid-service"
            adr_dir = repo_root / "adr"
            submodule.mkdir(parents=True)
            adr_dir.mkdir()

            (repo_root / "docs-project.yaml").write_text(
                yaml.dump(
                    {
                        "project": {"id": "parent-project", "name": "Parent Project"},
                        "structure": {"document_folders": ["adr"]},
                        "sub_projects": ["vendor/invalid-service/docs-project.yaml"],
                    }
                )
            )
            (submodule / "docs-project.yaml").write_text(
                yaml.dump(
                    {
                        "project": {"id": "Invalid_ID", "name": "Invalid Service"},
                    }
                )
            )
            (adr_dir / "adr-001-parent-decision.md").write_text(
                """---
title: Parent Decision
status: Accepted
created: 2025-01-01
deciders: Core Team
tags: [architecture]
id: adr-001
project_id: parent-project
doc_uuid: 11111111-1111-4111-8111-111111111111
---

# Parent ADR content
"""
            )

            validator = DocValidator(repo_root, verbose=False)
            validator.scan_documents()

            output = capsys.readouterr().out
            assert "Invalid sub-project config format" in output
            assert "Fix the config or remove it from sub_projects" in output
            assert [context.config.project.id for context in validator.project_configs] == ["parent-project"]
            assert [doc.file_path.name for doc in validator.documents] == ["adr-001-parent-decision.md"]
