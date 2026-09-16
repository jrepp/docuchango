#!/usr/bin/env -S uv run python3
"""Document Validation and Link Checker

Validates markdown documents for:
- YAML frontmatter format and required fields
- Internal link reachability
- Markdown formatting issues
- Consistent ADR/RFC numbering
- MDX compilation compatibility
- Document readability (Flesch Reading Ease, grade level metrics)
- Docusaurus build validation

Usage:
    docuchango validate
    docuchango validate --verbose
    docuchango validate --dry-run

Exit Codes:
    0 - All documents valid
    1 - Validation errors found
    2 - Missing dependencies
"""

import json
import re
import subprocess
import sys
from collections import deque
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path, PurePosixPath
from typing import Any, cast

try:
    import frontmatter
    import yaml
    from pydantic import ValidationError

    from docuchango.naming import resolve_naming_standard
    from docuchango.readability import TEXTSTAT_AVAILABLE, ReadabilityConfig, ReadabilityScorer

    # Import schemas from the docuchango package
    from docuchango.schemas import (
        ADRFrontmatter,
        DocsProjectConfig,
        DocsProjectReadability,
        DocsProjectStructure,
        GenericDocFrontmatter,
        MemoFrontmatter,
        PRDFrontmatter,
        RFCFrontmatter,
    )

    ENHANCED_VALIDATION = True
except ImportError as e:
    # Don't fail if only textstat is missing - just readability features will be disabled
    if "textstat" in str(e):
        # textstat is optional - set flag and continue
        TEXTSTAT_AVAILABLE = False
        ReadabilityConfig = None  # type: ignore[misc, assignment]
        ReadabilityScorer = None  # type: ignore[misc, assignment]
        ENHANCED_VALIDATION = True
    else:
        # Critical dependencies missing
        print("\n❌ CRITICAL ERROR: Required dependencies not found", file=sys.stderr)
        print("   Missing: python-frontmatter and/or pydantic", file=sys.stderr)
        print("   These are REQUIRED for proper frontmatter validation.", file=sys.stderr)
        print("\n   Fix:", file=sys.stderr)
        print("   $ uv sync", file=sys.stderr)
        print("\n   Then run validation with:", file=sys.stderr)
        print("   $ uv run tooling/validate_docs.py", file=sys.stderr)
        print(f"\n   Error details: {e}\n", file=sys.stderr)
        sys.exit(2)


from docuchango.config_paths import is_within_path, resolve_config_path
from docuchango.links import (
    LINK_PATTERN,
    NON_PATH_PREFIXES,
    RESOLVED_LINK_TYPES,
    classify_link,
    document_index,
    link_candidates,
    link_path_target,
    relative_link,
    resolve_internal_link,
    resolve_link_target,
    resolve_repository_escape,
)
from docuchango.links import (
    LinkType as LinkType,  # re-exported: `from docuchango.validator import LinkType` predates links.py
)
from docuchango.markdown import (
    blank_line_finding_message,
    blank_line_runs,
    mask_code,
    mdx_finding_message,
    mdx_tags,
)
from docuchango.text_io import (
    FMT_012_FINDING_MESSAGE,
    carriage_return_lines,
    has_bom,
    line_ending_finding_message,
    read_text,
)

#: Frontmatter fields FM-011 checks. The legacy ``date`` field is excluded:
#: Phase 1 migrates it to ``created`` before Phase 2 could report it.
DATE_FIELDS = ("created", "updated")

#: The two forms the bundled templates use, named in FM-011 messages.
FM_011_ACCEPTED_FORMS = "YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ"

#: ``YYYY-MM-DD`` and ``YYYY-MM-DDTHH:MM:SSZ``, paired with the ``strptime``
#: format that confirms the digits are a real point in time. A UTC offset
#: (``+00:00``) is deliberately not accepted: RFC-003 names ``Z``, and ``Z`` is
#: what docuchango writes wherever it generates a timestamp itself.
_FM_011_FORMS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\d{4}-\d{2}-\d{2}"), "%Y-%m-%d"),
    (re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"), "%Y-%m-%dT%H:%M:%SZ"),
)

#: The YAML block between the opening and closing ``---`` of a document.
_FRONTMATTER_BLOCK_PATTERN = re.compile(r"\A---[ \t]*\n(.*?)^---[ \t]*$", re.DOTALL | re.MULTILINE)


def is_accepted_date_format(value: str) -> bool:
    """Whether a ``created``/``updated`` value is one of the two FM-011 forms.

    The shape is matched with a regex and the digits are then parsed, so
    ``2024-13-45`` is rejected even though it has the right shape.
    """
    for pattern, fmt in _FM_011_FORMS:
        if not pattern.fullmatch(value):
            continue
        try:
            datetime.strptime(value, fmt)
        except ValueError:
            return False
        return True
    return False


def frontmatter_date_source(content: str, metadata: dict[str, Any]) -> dict[str, str]:
    """Return the :data:`DATE_FIELDS` scalars of ``content`` exactly as written.

    YAML resolves an unquoted ``2024-01-05`` to a ``datetime.date`` and both
    ``2024-01-05T10:00:00Z`` and ``2024-01-05T10:00:00+00:00`` to the same
    aware ``datetime``, so the parsed value cannot tell the accepted ``Z`` form
    from the offset form. The source text can, which is why FM-011 reads the
    scalars back out of the document with ``yaml.compose``: it parses without
    constructing values, and hands back the original text with quoting and
    trailing comments already stripped.

    A field is omitted when it is absent, when its value is ``null`` (which the
    schema check owns for ``created``) and when it is not a scalar at all.
    """
    match = _FRONTMATTER_BLOCK_PATTERN.match(content)
    if match is None:
        return {}
    try:
        node = yaml.compose(match.group(1), Loader=yaml.SafeLoader)
    except yaml.YAMLError:
        return {}
    if not isinstance(node, yaml.MappingNode):
        return {}

    source: dict[str, str] = {}
    for key_node, value_node in node.value:
        if not isinstance(key_node, yaml.ScalarNode) or key_node.value not in DATE_FIELDS:
            continue
        if not isinstance(value_node, yaml.ScalarNode):
            continue
        if metadata.get(key_node.value) is None:
            continue
        source[key_node.value] = value_node.value
    return source


@dataclass
class Document:
    """Represents a documentation file"""

    file_path: Path
    doc_type: str  # "adr", "rfc", "memo", or "doc"
    title: str
    status: str = ""
    date: str = ""
    tags: list[str] = field(default_factory=list)
    doc_id: str = ""  # Frontmatter id field (e.g., "adr-001", "rfc-015")
    expected_id: str | None = None  # ID inferred from configured filename pattern, when available
    doc_uuid: str = ""  # Frontmatter doc_uuid field (UUID v4)
    # Frontmatter project_id as written. ``None`` means the key is absent (or
    # the document has no frontmatter at all), which FM-002/FM-005 already
    # own, so FM-010 leaves it alone.
    project_id: str | None = None
    # Source text of the `created`/`updated` frontmatter scalars, keyed by
    # field name, for FM-011. Absent, null and non-scalar values are left out:
    # the parse cannot distinguish a `Z` timestamp from a `+00:00` one, so the
    # check reads the document source (see `frontmatter_date_source`).
    date_source: dict[str, str] = field(default_factory=dict)
    links: list["Link"] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    _content_cache: str | None = None  # Cached file content to avoid multiple reads

    def __hash__(self):
        return hash(str(self.file_path))

    def get_content(self) -> str:
        """Get file content, using cache if available"""
        if self._content_cache is None:
            self._content_cache = read_text(self.file_path)
        return self._content_cache


@dataclass
class Link:
    """Represents a link in a document"""

    source_doc: Path
    target: str
    line_number: int
    link_type: LinkType
    is_valid: bool = False
    error_message: str = ""

    def __str__(self) -> str:
        status = "✓" if self.is_valid else "✗"
        return f"{status} {self.source_doc.name}:{self.line_number} -> {self.target}"


@dataclass
class ProjectConfigContext:
    """Loaded docs-project.yaml with its path for relative path resolution."""

    config: DocsProjectConfig
    path: Path
    parent: "ProjectConfigContext | None" = None

    @property
    def base_dir(self) -> Path:
        return self.path.parent

    @property
    def allow_external_paths(self) -> bool:
        return self.config.security.allow_external_paths


class DocValidator:
    """Validates documentation"""

    def __init__(self, repo_root: Path, verbose: bool = False) -> None:
        self.repo_root = repo_root.resolve()
        self.verbose = verbose
        self.documents: list[Document] = []
        self.file_to_doc: dict[Path, Document] = {}
        self.all_links: list[Link] = []
        self.errors: list[str] = []
        # Filename -> scanned documents, built lazily for the LNK-001 candidate
        # list (see _link_candidates).
        self._document_index: dict[str, list[Path]] | None = None

        # Load project configuration
        self.project_config_path: Path | None = None
        self.project_config = self._load_project_config()
        self.project_configs = self._load_project_config_contexts()
        self._ownership_roots: list[tuple[Path, ProjectConfigContext]] | None = None

    def _load_project_config(self) -> DocsProjectConfig | None:
        """Load docs-project.yaml configuration"""
        candidate_paths = [
            self.repo_root / "docs-project.yaml",
            self.repo_root / "docs-cms" / "docs-project.yaml",
            self.repo_root / "docs" / "docs-project.yaml",
        ]

        for config_path in candidate_paths:
            if not config_path.exists():
                continue

            try:
                config_data = yaml.safe_load(read_text(config_path))
                config = DocsProjectConfig(**config_data)
                self.project_config_path = config_path
                self.log(f"✓ Loaded project config: {config.project.id} ({config_path})")
                return config
            except ValidationError as e:
                self.log(f"⚠️  Warning: Invalid project config format at {config_path}: {e}")
                return None
            except Exception as e:
                self.log(f"⚠️  Warning: Could not load project config at {config_path}: {e}")
                return None

        self.log("⚠️  Warning: Project config not found (looked for docs-project.yaml at repo root and docs-cms/)")
        return None

    def _load_project_config_at(self, config_path: Path) -> DocsProjectConfig | None:
        """Load one docs-project.yaml file from an explicit path."""
        if not config_path.exists():
            self.log(
                f"⚠️  Warning: Sub-project config not found: {config_path}. Add the file or remove it from subprojects.",
                force=True,
            )
            return None

        try:
            config_data = yaml.safe_load(read_text(config_path))
            config = DocsProjectConfig(**config_data)
            self.log(f"✓ Loaded sub-project config: {config.project.id} ({config_path})")
            return config
        except ValidationError as e:
            self.log(
                f"⚠️  Warning: Invalid sub-project config format at {config_path}: {e}. "
                "Fix the config or remove it from subprojects.",
                force=True,
            )
            return None
        except Exception as e:
            self.log(
                f"⚠️  Warning: Could not load sub-project config at {config_path}: {e}. "
                "Fix the config or remove it from subprojects.",
                force=True,
            )
            return None

    def _load_project_config_contexts(self) -> list[ProjectConfigContext]:
        """Load the primary project config and any referenced sub-project configs."""
        if not self.project_config or not self.project_config_path:
            return []

        contexts = [ProjectConfigContext(self.project_config, self.project_config_path)]
        seen = {self.project_config_path.resolve()}
        pending = deque(contexts)

        while pending:
            parent = pending.popleft()
            for subproject in parent.config.subprojects:
                sub_path = self._resolve_config_path(
                    parent,
                    parent.base_dir,
                    subproject.path,
                    parent.base_dir,
                    "subproject",
                )
                if not sub_path:
                    continue
                if sub_path.is_dir():
                    sub_path = sub_path / "docs-project.yaml"
                if sub_path in seen:
                    continue
                seen.add(sub_path)

                sub_config = self._load_project_config_at(sub_path)
                if not sub_config:
                    continue

                context = ProjectConfigContext(sub_config, sub_path, parent=parent)
                contexts.append(context)
                pending.append(context)

        return contexts

    def _get_config_base_dir(self) -> Path:
        """Base directory for resolving structure paths."""
        if self.project_config_path:
            return self.project_config_path.parent
        # Legacy default
        return self.repo_root / "docs-cms"

    def _add_path_escape_error(
        self, context: ProjectConfigContext, path_value: str, purpose: str, boundary: Path
    ) -> None:
        """Record a blocked config path that resolved outside its allowed boundary."""
        message = (
            f"Blocked {purpose} path '{path_value}' in {context.path}: configured paths must stay within "
            f"{boundary}. Use subprojects for additional docs roots or set security.allow_external_paths: true."
        )
        if message not in self.errors:
            self.errors.append(message)
        self.log(f"⚠️  Warning: {message}", force=True)

    def _resolve_config_path(
        self,
        context: ProjectConfigContext,
        base_dir: Path,
        path_value: str,
        boundary: Path,
        purpose: str,
    ) -> Path | None:
        """Resolve a configured path and block escapes by default."""
        resolved = resolve_config_path(base_dir, path_value, boundary, context.allow_external_paths)
        if resolved is None:
            self._add_path_escape_error(context, path_value, purpose, boundary.resolve())
        return resolved

    def _config_ownership_roots(self) -> list[tuple[Path, ProjectConfigContext]]:
        """Directories owned by each loaded config, deepest first.

        A config owns the directory that holds it plus every docs root it
        configures, so a document can be mapped back to the (sub-)project
        whose settings apply to it.
        """
        if self._ownership_roots is None:
            roots: list[tuple[Path, ProjectConfigContext]] = []
            for context in self.project_configs:
                owned = {context.base_dir.resolve()}
                for path_value in context.config.structure.docs_roots:
                    resolved = resolve_config_path(
                        context.base_dir, path_value, context.base_dir, context.allow_external_paths
                    )
                    if resolved:
                        owned.add(resolved)
                roots.extend((path, context) for path in owned)
            roots.sort(key=lambda item: len(item[0].parts), reverse=True)
            self._ownership_roots = roots
        return self._ownership_roots

    def _config_context_for_path(self, file_path: Path) -> ProjectConfigContext | None:
        """Return the loaded config that owns a document path.

        The deepest owning directory wins, so a document inside a sub-project
        resolves to that sub-project rather than to the root config.
        """
        if not self.project_configs:
            return None
        resolved = file_path.resolve()
        for root, context in self._config_ownership_roots():
            if is_within_path(resolved, root):
                return context
        return self.project_configs[0]

    def _readability_config_for(self, file_path: Path) -> "DocsProjectReadability | None":
        """Resolve the readability settings that apply to one document.

        The owning (sub-)project's `readability` block wins as a whole. A
        config that does not declare the block inherits its parent's block,
        up to the root config; nothing is merged key by key.
        """
        context = self._config_context_for_path(file_path)
        while context is not None:
            if "readability" in context.config.model_fields_set:
                return context.config.readability
            context = context.parent
        return self.project_config.readability if self.project_config else None

    def _repository_url_for(self, file_path: Path) -> str | None:
        """Resolve the ``project.repository_url`` that applies to one document.

        The governing (sub-)project's URL wins, resolved with the same
        ``_config_context_for_path`` that RD-001 and FM-010 use. A sub-project
        that declares none inherits the URL of the config that included it, up
        to the root config: a monorepo is usually one repository, so the root's
        URL is the right answer for a sub-project that does not live in one of
        its own. A sub-project checked out from a different repository declares
        its own URL and is not touched by the fallback.
        """
        context = self._config_context_for_path(file_path)
        while context is not None:
            if context.config.project.repository_url:
                return context.config.project.repository_url
            context = context.parent
        return self.project_config.project.repository_url if self.project_config else None

    def log(self, message: str, force: bool = False):
        """Log if verbose or forced"""
        if self.verbose or force:
            print(message)

    @staticmethod
    def _link_path_target(target: str) -> str:
        """The filesystem path portion of a Markdown link target.

        Lives in :mod:`docuchango.links` so the LNK-010 fixer strips titles,
        anchors and percent-escapes exactly the way this check does.
        """
        return link_path_target(target)

    def _get_folder_config(self) -> dict[str, str]:
        """Get folder configuration from project config or use defaults"""
        if self.project_config and self.project_config.structure:
            return {
                "adr": self.project_config.structure.adr_dir,
                "rfc": self.project_config.structure.rfc_dir,
                "memo": self.project_config.structure.memo_dir,
                "prd": self.project_config.structure.prd_dir,
            }
        # Default configuration
        return {
            "adr": "adr",
            "rfc": "rfcs",
            "memo": "memos",
            "prd": "prd",
        }

    def _get_document_folders(self) -> list[str]:
        """Get list of document folders to scan from config or defaults"""
        if self.project_config and self.project_config.structure:
            return self.project_config.structure.document_folders
        # Default folders to scan (includes prd now!)
        return ["adr", "rfcs", "memos", "prd"]

    def _get_scan_subfolders_default(self) -> bool:
        """Get the structure-level default for scanning nested subfolders"""
        if self.project_config and self.project_config.structure:
            return self.project_config.structure.scan_subfolders
        return False

    def _build_scan_entries(self) -> list[tuple[str, str, str, bool, bool, Path, Path, bool, bool]]:
        """Build scan entries as tuples:

        (doc_type, folder_relative, filename_pattern, enforce_filename_pattern,
        require_frontmatter, root_path, boundary, allow_external_paths, scan_subfolders)
        """
        default_patterns = {
            "adr": r"^(adr)-(\d{3})-(.+)\.md$",
            "rfc": r"^(rfc)-(\d{3})-(.+)\.md$",
            "memo": r"^(memo)-(\d{3})-(.+)\.md$",
            "prd": r"^(prd)-(\d{3})-(.+)\.md$",
        }

        contexts = self.project_configs or []

        if contexts:
            entries: list[tuple[str, str, str, bool, bool, Path, Path, bool, bool]] = []
            for context in contexts:
                config = context.config
                config_base = context.base_dir

                if config.structure and config.structure.doc_types:
                    roots = config.structure.effective_docs_roots()
                    custom_naming = config.structure.naming_standards or {}
                    structure_scan_subfolders = config.structure.scan_subfolders
                    for doc_type_name, cfg in config.structure.doc_types.items():
                        scan_subfolders = (
                            cfg.scan_subfolders if cfg.scan_subfolders is not None else structure_scan_subfolders
                        )
                        if cfg.naming_standard:
                            pattern = resolve_naming_standard(cfg.naming_standard, custom_naming)
                            if pattern:
                                pattern = f"^{pattern}" if not pattern.startswith("^") else pattern
                            else:
                                pattern = default_patterns.get(doc_type_name, r"^(.+)\.md$")
                        elif cfg.filename_pattern:
                            pattern = cfg.filename_pattern
                        else:
                            pattern = default_patterns.get(doc_type_name, r"^(.+)\.md$")
                        folders = cfg.folders or []
                        for root_rel in roots:
                            root_path = self._resolve_config_path(
                                context,
                                config_base,
                                root_rel,
                                config_base,
                                "docs root",
                            )
                            if not root_path:
                                continue
                            for folder in folders:
                                entries.append(
                                    (
                                        cfg.frontmatter_schema,
                                        config.structure.folder_under_root(root_rel, folder),
                                        pattern,
                                        cfg.enforce_filename_pattern,
                                        cfg.require_frontmatter,
                                        root_path,
                                        root_path,
                                        context.allow_external_paths,
                                        scan_subfolders,
                                    )
                                )
                    continue

                structure = config.structure
                for root_rel in structure.effective_docs_roots():
                    root_path = self._resolve_config_path(
                        context,
                        config_base,
                        root_rel,
                        config_base,
                        "docs root",
                    )
                    if not root_path:
                        continue
                    for schema_name, folder_name in structure.legacy_folder_bindings():
                        entries.append(
                            (
                                schema_name,
                                structure.folder_under_root(root_rel, folder_name),
                                default_patterns[schema_name],
                                True,
                                True,
                                root_path,
                                root_path,
                                context.allow_external_paths,
                                structure.scan_subfolders,
                            )
                        )
            return entries

        # Legacy behavior
        config_base = self._get_config_base_dir()
        structure = (
            self.project_config.structure
            if self.project_config and self.project_config.structure
            else DocsProjectStructure()
        )

        entries = []
        for root_rel in structure.effective_docs_roots():
            root_path = (config_base / root_rel).resolve()
            for schema_name, folder_name in structure.legacy_folder_bindings():
                entries.append(
                    (
                        schema_name,
                        structure.folder_under_root(root_rel, folder_name),
                        default_patterns[schema_name],
                        True,
                        True,
                        root_path,
                        root_path,
                        False,
                        structure.scan_subfolders,
                    )
                )
        return entries

    def _scan_document_folder(
        self,
        folder_path: Path,
        _folder_name: str,
        doc_type: str,
        pattern: re.Pattern[str],
        enforce_filename_pattern: bool,
        require_frontmatter: bool,
        scan_subfolders: bool = False,
    ):
        """Scan a specific document folder for markdown files"""
        if not folder_path.exists():
            self.log(f"   ⊘ Folder {folder_path} does not exist, skipping")
            return

        for md_file in folder_path.rglob("*.md"):
            # Skip README and index files (landing pages)
            if md_file.name in ["README.md", "index.md"]:
                continue

            # By default, only top-level files in the document folder are
            # treated as numbered documents subject to strict naming/
            # frontmatter/ID rules. Everything nested in a subfolder (e.g.
            # prd/testing/*, memos/private/*) is treated as supporting
            # material and skipped entirely - regardless of whether its name
            # happens to match the pattern - so it is never validated (or
            # mis-validated) as a top-level doc. When scan_subfolders is
            # enabled (structure.scan_subfolders, or the per-type
            # structure.doc_types.<type>.scan_subfolders override) nested
            # files are scanned with the same rules, matching the filename
            # pattern and deriving the expected id against the file name
            # only, never the subfolder path.
            is_top_level = md_file.parent == folder_path
            if enforce_filename_pattern and not is_top_level and not scan_subfolders:
                self.log(f"   ⊘ {md_file.relative_to(folder_path)}: nested support file, skipping")
                continue

            match = pattern.match(md_file.name)
            if enforce_filename_pattern and not match:
                # A top-level file that violates the naming convention is a
                # real error the author must fix.
                self.errors.append(f"Invalid {doc_type.upper()} filename: {md_file.name} (pattern: {pattern.pattern})")
                self.log(f"   ✗ {md_file.name}: Invalid filename format")
                continue

            expected_id = None
            if match and len(match.groups()) >= 2:
                prefix, num = match.groups()[:2]
                # Skip template files (000)
                if num == "000":
                    self.log(f"   ⊘ {md_file.name}: Skipping template file")
                    continue
                if isinstance(prefix, str) and isinstance(num, str) and prefix.lower() == doc_type and num.isdigit():
                    expected_id = f"{doc_type}-{num}"
                    # Amendment files (e.g. 'adr-043-amendment-01-...md') use the
                    # amendment id form 'adr-043-a1'. This '-aNN' convention is
                    # ADR-only, so the conversion is restricted to ADRs to avoid
                    # inventing false expected ids for other doc types.
                    if doc_type == "adr":
                        rest = match.groups()[2] if len(match.groups()) >= 3 else ""
                        if isinstance(rest, str):
                            amendment_match = re.match(r"amendment-0*(\d+)\b", rest)
                            if amendment_match:
                                expected_id = f"{doc_type}-{num}-a{amendment_match.group(1)}"

            doc = self._parse_document(
                md_file, doc_type, require_frontmatter=require_frontmatter, expected_id=expected_id
            )
            if doc:
                self.documents.append(doc)
                self.file_to_doc[md_file] = doc

    def scan_documents(self):
        """Scan all markdown files"""
        self.log("\n📂 Scanning documents...")

        entries = self._build_scan_entries()
        if not entries:
            self.log("   ⊘ No configured scan entries found", force=True)

        for (
            doc_type,
            folder_name,
            pattern_text,
            enforce_pattern,
            require_frontmatter,
            root_path,
            boundary,
            allow_external_paths,
            scan_subfolders,
        ) in entries:
            try:
                pattern = re.compile(pattern_text)
            except re.error as e:
                self.errors.append(f"Invalid filename regex for {doc_type}/{folder_name}: {e}")
                continue

            folder_path = (root_path / folder_name).resolve()
            if not allow_external_paths and not is_within_path(folder_path, boundary):
                self.errors.append(
                    f"Blocked document folder path '{folder_name}': configured paths must stay within {boundary}"
                )
                continue
            self.log(f"   Scanning {folder_path} ({doc_type} documents)...")
            self._scan_document_folder(
                folder_path,
                folder_name,
                doc_type,
                pattern,
                enforce_pattern,
                require_frontmatter,
                scan_subfolders,
            )

        # Scan general docs markdown files at each configured docs root.
        roots_to_scan = [self._get_config_base_dir()]
        if self.project_configs:
            roots_to_scan = []
            for context in self.project_configs:
                for path_value in context.config.structure.docs_roots:
                    resolved = self._resolve_config_path(
                        context, context.base_dir, path_value, context.base_dir, "docs root"
                    )
                    if resolved:
                        roots_to_scan.append(resolved)
        elif self.project_config and self.project_config.structure:
            roots_to_scan = [
                (self._get_config_base_dir() / p).resolve() for p in self.project_config.structure.docs_roots
            ]

        for docs_dir in roots_to_scan:
            if not docs_dir.exists():
                continue
            for md_file in docs_dir.glob("*.md"):
                if md_file.name in ["README.md", "docs-project.yaml"]:
                    continue
                doc = self._parse_document(md_file, "doc")
                if doc:
                    self.documents.append(doc)
                    self.file_to_doc[md_file] = doc

        self.log(f"   Found {len(self.documents)} documents")

    def _parse_document(
        self, file_path: Path, doc_type: str, require_frontmatter: bool = True, expected_id: str | None = None
    ) -> Document | None:
        """Parse a markdown file and validate frontmatter"""
        return self._parse_document_enhanced(
            file_path, doc_type, require_frontmatter=require_frontmatter, expected_id=expected_id
        )

    @staticmethod
    def _frontmatter_project_id(metadata: dict[str, Any]) -> str | None:
        """Return the frontmatter ``project_id`` as written, or ``None``.

        ``None`` means the key is absent, which the schema (FM-002) and the
        required-field fixer (FM-005) already own; an empty or blank value is
        returned as the empty string so FM-010 can report it.
        """
        if "project_id" not in metadata:
            return None
        value = metadata["project_id"]
        if value is None:
            return ""
        return str(value)

    def _infer_plain_markdown_title(self, file_path: Path, content: str) -> str:
        """Infer a title for plain-markdown generic documents."""
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped[2:].strip()
        return file_path.stem.replace("-", " ").replace("_", " ").strip().title() or file_path.name

    def _parse_document_enhanced(
        self, file_path: Path, doc_type: str, require_frontmatter: bool = True, expected_id: str | None = None
    ) -> Document | None:
        """Parse document with python-frontmatter and pydantic validation"""
        try:
            # Read file content once and cache it
            content = read_text(file_path)

            # Parse frontmatter from content
            post = frontmatter.loads(content)
            metadata = cast(dict[str, Any], post.metadata)

            if not metadata:
                if doc_type == "generic" and not require_frontmatter:
                    title = self._infer_plain_markdown_title(file_path, content)
                    self.log(f"   ✓ {file_path.name}: Plain Markdown generic doc")
                    return Document(
                        file_path=file_path,
                        doc_type=doc_type,
                        title=title,
                        expected_id=expected_id,
                        _content_cache=content,
                    )

                error = "Missing YAML frontmatter"
                self.log(f"   ✗ {file_path.name}: {error}")
                doc = Document(
                    file_path=file_path,
                    doc_type=doc_type,
                    title="Unknown",
                    expected_id=expected_id,
                    _content_cache=content,
                )
                doc.errors.append(error)
                return doc

            # Validate against schema
            try:
                if doc_type == "adr":
                    ADRFrontmatter(**metadata)
                elif doc_type == "rfc":
                    RFCFrontmatter(**metadata)
                elif doc_type == "memo":
                    MemoFrontmatter(**metadata)
                elif doc_type == "prd":
                    PRDFrontmatter(**metadata)
                else:
                    # Generic validation for other docs
                    GenericDocFrontmatter(**metadata)

            except ValidationError as e:
                # Pydantic validation errors - very detailed
                doc = Document(
                    file_path=file_path,
                    doc_type=doc_type,
                    title=metadata.get("title", "Unknown"),
                    status=metadata.get("status", ""),
                    date=str(metadata.get("date", metadata.get("created", ""))),
                    tags=metadata.get("tags", []),
                    doc_id=metadata.get("id", ""),
                    expected_id=expected_id,
                    project_id=self._frontmatter_project_id(metadata),
                    date_source=frontmatter_date_source(content, metadata),
                    _content_cache=content,
                )

                for error in e.errors():  # type: ignore[assignment]
                    field_name = ".".join(str(loc) for loc in error["loc"])
                    msg = error["msg"]
                    error_type = error["type"]

                    # Format user-friendly error message
                    if error_type == "literal_error":
                        # Extract allowed values from message
                        doc.errors.append(f"Frontmatter field '{field_name}': {msg}")
                    else:
                        doc.errors.append(f"Frontmatter field '{field_name}': {msg}")

                    self.log(f"   ✗ {file_path.name}: {field_name} - {msg}")

                return doc

            # Success - create document
            doc = Document(
                file_path=file_path,
                doc_type=doc_type,
                title=metadata.get("title", "Unknown"),
                status=metadata.get("status", ""),
                date=str(metadata.get("date", metadata.get("created", ""))),
                tags=metadata.get("tags", []),
                doc_id=metadata.get("id", ""),
                expected_id=expected_id,
                doc_uuid=metadata.get("doc_uuid", ""),
                project_id=self._frontmatter_project_id(metadata),
                date_source=frontmatter_date_source(content, metadata),
                _content_cache=content,
            )

            self.log(f"   ✓ {file_path.name}: {doc.title}")
            return doc

        except Exception as e:
            self.errors.append(f"Error parsing {file_path}: {e}")
            self.log(f"   ✗ {file_path.name}: {e}")
            return None

    def extract_links(self):
        """Extract all links from documents"""
        self.log("\n🔗 Extracting links...")

        for doc in self.documents:
            links = self._extract_links_from_doc(doc)
            doc.links = links
            self.all_links.extend(links)

        self.log(f"   Found {len(self.all_links)} total links")

    def _extract_links_from_doc(self, doc: Document) -> list[Link]:
        """Extract markdown links from a document using cached content"""
        links = []

        try:
            # Use the same masking as the MDX and repo-escape checks so a link
            # inside an indented or nested code fence is not extracted (and
            # then reported as broken). Line numbers are preserved by the mask.
            lines = self._mask_code(doc.get_content(), strip_frontmatter=True)

            for line_num, line in enumerate(lines, start=1):
                for match in LINK_PATTERN.finditer(line):
                    link_target = match.group(2)

                    # Skip mailto and data links
                    if link_target.startswith(NON_PATH_PREFIXES):
                        continue

                    link_type = self._classify_link(link_target, doc.file_path)

                    link = Link(source_doc=doc.file_path, target=link_target, line_number=line_num, link_type=link_type)
                    links.append(link)

        except Exception as e:
            self.errors.append(f"Error extracting links from {doc.file_path}: {e}")

        return links

    def _classify_link(self, target: str, source_path: Path) -> LinkType:
        """Classify link by target (see :func:`docuchango.links.classify_link`)."""
        return classify_link(target, source_path)

    def validate_links(self):
        """Validate all links"""
        self.log("\n✓ Validating links...")

        for link in self.all_links:
            if link.link_type == LinkType.EXTERNAL:
                link.is_valid = True
                continue

            if link.link_type == LinkType.ANCHOR:
                link.is_valid = True
                continue

            if link.link_type == LinkType.DOCUSAURUS_PLUGIN:
                # Cross-plugin links are valid (e.g., /prism-data-layer/netflix/...)
                link.is_valid = True
                continue

            if link.link_type in RESOLVED_LINK_TYPES:
                self._validate_internal_link(link)
            else:
                link.is_valid = False
                link.error_message = f"Unknown link type: {link.target}"

    @staticmethod
    def _resolve_link_target(base_dir: Path, target: str) -> tuple[Path, bool]:
        """Resolve a link target against base_dir and report existence.

        Lives in :mod:`docuchango.links`; see
        :func:`docuchango.links.resolve_link_target`.
        """
        return resolve_link_target(base_dir, target)

    def _validate_internal_link(self, link: Link) -> None:
        """Validate one internal document link (LNK-001).

        Resolution lives in :func:`docuchango.links.resolve_internal_link`, so
        the LNK-010 fixer decides a link is broken on exactly the same terms
        this check does: a site-root target against the repository root, and
        './x', '../x' and the bare relative 'adr/x.md' against the linking
        document's own folder.

        When the target does not exist, the message names the documents in the
        scanned set that carry that filename. One such candidate is the
        LNK-010 case and Phase 1 has already rewritten the link, so only the
        ambiguous case reaches here with candidates to list; naming them turns
        "file not found" into the choice the author actually has to make.
        """
        target_path, exists = resolve_internal_link(link.source_doc, self.repo_root, link.target)
        link.is_valid = exists
        if exists:
            return

        link.error_message = f"File not found: {target_path}"
        candidates = self._link_candidates(link)
        if len(candidates) < 2:
            return
        shown = ", ".join(relative_link(link.source_doc, candidate) for candidate in candidates)
        link.error_message += (
            f"; {len(candidates)} scanned documents are named "
            f"'{PurePosixPath(self._link_path_target(link.target)).name}': {shown}. "
            "LNK-010 rewrites a broken link only when exactly one document matches, "
            "so pick one and write the path out."
        )

    def _link_candidates(self, link: Link) -> list[Path]:
        """Scanned documents whose filename matches a broken link's target.

        The index is built once per run and kept on the validator, because
        ``validate_links`` walks every link in the tree and each ambiguous one
        would otherwise rescan the whole document set.
        """
        if self._document_index is None:
            self._document_index = document_index(doc.file_path for doc in self.documents)
        return link_candidates(link.target, self._document_index)

    def check_mdx_compilation(self):
        """Check MDX compilation using @mdx-js/mdx compiler"""
        self.log("\n🔧 Checking MDX compilation...")

        # Check if Node.js is available
        try:
            subprocess.run(["node", "--version"], check=False, capture_output=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.log("   ⚠️  Node.js not found, skipping MDX compilation check")
            return True

        # Check if validate_mdx.mjs exists
        mdx_validator = self.repo_root / "docusaurus" / "validate_mdx.mjs"
        if not mdx_validator.exists():
            self.log("   ⚠️  validate_mdx.mjs not found, skipping MDX compilation check")
            return True

        # Collect all document paths
        file_paths = [str(doc.file_path) for doc in self.documents]

        if not file_paths:
            self.log("   ⚠️  No documents to validate")
            return True

        try:
            # Call Node.js validator
            result = subprocess.run(
                ["node", str(mdx_validator)] + file_paths, check=False, capture_output=True, text=True, timeout=60
            )

            # Parse JSON results
            try:
                results = json.loads(result.stdout)
            except json.JSONDecodeError:
                error = "Failed to parse MDX validation results"
                self.errors.append(error)
                self.log(f"   ✗ {error}")
                if self.verbose:
                    self.log(f"      Output: {result.stdout}")
                    self.log(f"      Error: {result.stderr}")
                return False

            # Process results
            has_errors = False
            for file_result in results:
                file_path = Path(file_result["file"])

                # Find corresponding document
                doc = self.file_to_doc.get(file_path)
                if not doc:
                    continue

                if not file_result["valid"]:
                    has_errors = True
                    error_msg = file_result.get("reason", file_result.get("message", "Unknown MDX error"))
                    line = file_result.get("line")

                    if line:
                        error = f"MDX compilation error at line {line}: {error_msg}"
                    else:
                        error = f"MDX compilation error: {error_msg}"

                    doc.errors.append(error)
                    self.log(f"   ✗ {doc.file_path.name}: {error}")

            if not has_errors:
                self.log("   ✓ All documents compile as valid MDX")
                return True
            return False

        except subprocess.TimeoutExpired:
            error = "MDX validation timed out"
            self.errors.append(error)
            self.log(f"   ✗ {error}")
            return False
        except Exception as e:
            error = f"Error running MDX validation: {e}"
            self.errors.append(error)
            self.log(f"   ✗ {error}")
            return False

    @staticmethod
    def _mask_code(content: str, strip_frontmatter: bool = False) -> list[str]:
        """Return the document's lines with code masked out, line numbers kept.

        Lives in :mod:`docuchango.markdown` as :func:`~docuchango.markdown.mask_code`
        so the LNK-010 fixer skips the same fenced blocks and inline spans this
        check does.
        """
        return mask_code(content, strip_frontmatter=strip_frontmatter)

    def check_mdx_compatibility(self):
        """Report JSX-shaped '<...>' in prose that MDX cannot compile (MDX-001).

        MDX only mis-parses '<' when it looks like the start of a JSX tag, i.e.
        '<' immediately followed by a letter. A '<'/'>' before a digit or
        whitespace ('<5ms', '>90%', 'a < b') is NOT interpreted as JSX and is
        safe. Valid HTML elements, PascalCase components, explicitly
        self-closing tags and CommonMark autolinks are safe too. Only bare
        placeholders in prose ('<agentName>', '<token>') actually break MDX.

        The scan itself lives in :func:`docuchango.markdown.mdx_tags`, which
        masks code fences, inline code spans and the frontmatter block first.
        MDX-010 escapes exactly the tags this reports, using the same function,
        so the report and the repair can never drift.
        """
        self.log("\n🔧 Checking MDX compatibility...")

        mdx_issues_found = False

        for doc in self.documents:
            try:
                for tag in mdx_tags(doc.get_content()):
                    error = mdx_finding_message(tag)
                    doc.errors.append(error)
                    mdx_issues_found = True
                    self.log(f"   ✗ {doc.file_path.name}:{tag.line_number} - {error}")

            except Exception as e:
                doc.errors.append(f"Error checking MDX compatibility: {e}")

        if not mdx_issues_found:
            self.log("   ✓ No MDX syntax issues found")

    def check_cross_plugin_links(self):
        """Report relative links that escape the repository root (LNK-002).

        A relative link that resolves to a path outside the repository cannot be
        satisfied by any in-repo reference and will not resolve at build time.
        Links that point elsewhere inside the repository (e.g. into the source
        tree at '../../internal/...' or the repo-root README) are legitimate and
        are NOT flagged.

        Each offending link is reported individually with its line number and
        the resolved target. Whether a target escapes at all is decided by
        :func:`docuchango.links.resolve_repository_escape`, shared with the
        LNK-011 fixer, so the fixer cannot rewrite a link this check is happy
        with.

        LNK-011 repairs the finding in Phase 1 when the target exists on disk
        and the config governing the document sets ``project.repository_url``.
        What reaches this report is therefore a link whose target does not
        exist -- a typo, which must not be frozen into an absolute URL -- or a
        document whose config has no repository URL, and the message says so.
        """
        self.log("\n🔗 Checking links escaping the repository...")

        repo_root = self.repo_root.resolve()
        # Match links against the whole (masked) content so that Markdown links
        # whose label and target span multiple lines are still detected.
        link_pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)", re.DOTALL)
        issues_found = False

        for doc in self.documents:
            try:
                masked = "\n".join(self._mask_code(doc.get_content(), strip_frontmatter=True))

                for match in link_pattern.finditer(masked):
                    target = match.group(1).strip()
                    # Line number of the target (where the '(' opens).
                    line_num = masked.count("\n", 0, match.start(1)) + 1

                    resolved = resolve_repository_escape(doc.file_path, repo_root, target)
                    if resolved is None:
                        continue  # not a path, or stays inside the repository

                    issues_found = True
                    error = (
                        f"LNK-002: Line {line_num}: Link '{target}' points outside the repository "
                        f"({repo_root.name}/) - use an absolute GitHub URL for external references"
                    )
                    if resolved.exists() and not self._repository_url_for(doc.file_path):
                        error += (
                            ". The target exists on disk, so setting project.repository_url in the config "
                            "that governs this document lets LNK-011 rewrite this link for you"
                        )
                    doc.errors.append(error)
                    self.log(f"   ⚠️  {doc.file_path.name}:{line_num} - {error}")

            except Exception as e:
                doc.errors.append(f"Error checking cross-plugin links: {e}")

        if not issues_found:
            self.log("   ✓ No links escaping the repository found")

    def _extract_markdown_file_links(self, content: str, source_path: Path) -> dict[Path, tuple[int, str]]:
        """Extract Markdown file links and resolve them to absolute paths."""
        links: dict[Path, tuple[int, str]] = {}
        in_code_fence = False
        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

        for line_num, line in enumerate(content.splitlines(), start=1):
            if line.startswith("```"):
                in_code_fence = not in_code_fence
                continue
            if in_code_fence:
                continue

            line_without_code = re.sub(r"`[^`]+`", "", line)
            for match in link_pattern.finditer(line_without_code):
                target = self._link_path_target(match.group(2))
                if re.match(r"^[a-z][a-z0-9+.-]*:", target):
                    continue
                if not target.endswith(".md") and not target.startswith(("./", "../", "/")):
                    continue

                if target.startswith("/"):
                    resolved = (self.repo_root / target.lstrip("/")).resolve()
                else:
                    resolved = (source_path.parent / target).resolve()
                    if not resolved.suffix:
                        resolved = Path(str(resolved) + ".md")
                links[resolved] = (line_num, target)

        return links

    def _extract_bucket_headings(self, content: str, heading_level: int) -> dict[int, str]:
        """Map line numbers to bucket heading text at the configured heading level."""
        marker = "#" * heading_level
        headings: dict[int, str] = {}
        in_code_fence = False

        for line_num, line in enumerate(content.splitlines(), start=1):
            if line.startswith("```"):
                in_code_fence = not in_code_fence
                continue
            if in_code_fence:
                continue
            if line.startswith(f"{marker} ") and not line.startswith(f"{marker}#"):
                headings[line_num] = line[len(marker) :].strip()

        return headings

    def _bucket_for_target(self, target_path: Path, bucket_config) -> str | None:
        """Compute the expected index bucket for a target document."""
        post = frontmatter.loads(read_text(target_path))

        if bucket_config.cadence == "milestone":
            milestone = post.metadata.get(bucket_config.milestone_field)
            return str(milestone).strip() if milestone else None

        value = post.metadata.get(bucket_config.field)
        if isinstance(value, datetime):
            target_date = value.date()
        elif isinstance(value, date):
            target_date = value
        elif isinstance(value, str):
            target_date = date.fromisoformat(value.split("T", 1)[0])
        else:
            return None

        if bucket_config.cadence == "weekly":
            iso_year, iso_week, _ = target_date.isocalendar()
            return f"{iso_year}-W{iso_week:02d}"
        if bucket_config.cadence == "monthly":
            return f"{target_date:%Y-%m}"
        if bucket_config.cadence == "quarterly":
            quarter = ((target_date.month - 1) // 3) + 1
            return f"{target_date.year}-Q{quarter}"
        if bucket_config.cadence == "yearly":
            return f"{target_date.year}"
        return None

    def _glob_static_prefix(self, pattern: str) -> str:
        """Return the non-glob path prefix used for containment checks."""
        parts = Path(pattern).parts
        prefix_parts: list[str] = []
        for part in parts:
            if any(char in part for char in "*?["):
                break
            prefix_parts.append(part)
        if not prefix_parts:
            return "."
        return str(Path(*prefix_parts))

    def _safe_index_target_paths(self, context: ProjectConfigContext, target_pattern: str) -> set[Path]:
        """Expand an index target glob only when its static prefix stays in the config boundary."""
        prefix = self._glob_static_prefix(target_pattern)
        if not self._resolve_config_path(context, context.base_dir, prefix, context.base_dir, "index target"):
            return set()
        return {path.resolve() for path in context.base_dir.glob(target_pattern) if path.is_file()}

    def check_document_indexes(self):
        """Validate configured Markdown index files."""
        contexts = self.project_configs or []
        if not contexts and self.project_config and self.project_config_path:
            contexts = [ProjectConfigContext(self.project_config, self.project_config_path)]

        contexts = [context for context in contexts if context.config.indexes]
        if not contexts:
            return

        self.log("\n🗂️  Checking document indexes...")

        for context in contexts:
            config_base = context.base_dir
            for index_config in context.config.indexes:
                index_path = self._resolve_config_path(
                    context, config_base, index_config.path, config_base, "document index"
                )
                if not index_path:
                    continue
                if not index_path.exists():
                    self.errors.append(f"Document index '{index_config.name}' not found: {index_config.path}")
                    continue

                try:
                    content = read_text(index_path)
                    links = self._extract_markdown_file_links(content, index_path)
                    target_paths: set[Path] = set()
                    for target_pattern in index_config.targets:
                        target_paths.update(self._safe_index_target_paths(context, target_pattern))
                    target_paths.discard(index_path)

                    if index_config.require_entries and target_paths and not links:
                        self.errors.append(f"Document index '{index_config.name}' has no Markdown links")

                    if index_config.require_all_targets:
                        for target_path in sorted(target_paths):
                            if target_path not in links:
                                rel_target = target_path.relative_to(config_base)
                                self.errors.append(
                                    f"Document index '{index_config.name}' is missing target: {rel_target}"
                                )

                    if not index_config.allow_extra_links:
                        for linked_path, (line_num, raw_target) in sorted(links.items()):
                            if linked_path.exists() and linked_path not in target_paths:
                                self.errors.append(
                                    f"Document index '{index_config.name}' line {line_num} links outside targets: {raw_target}"
                                )

                    if index_config.time_bucket:
                        self._check_document_index_buckets(
                            index_config.name, content, links, target_paths, index_config.time_bucket, config_base
                        )

                    self.log(f"   ✓ {index_config.name}: {len(target_paths)} target(s) checked")
                except Exception as e:
                    self.errors.append(f"Error checking document index '{index_config.name}': {e}")

    def _check_document_index_buckets(
        self,
        name: str,
        content: str,
        links: dict[Path, tuple[int, str]],
        target_paths: set[Path],
        bucket_config,
        config_base: Path,
    ) -> None:
        """Validate that index links appear under the expected time or milestone bucket."""
        headings = self._extract_bucket_headings(content, bucket_config.heading_level)
        if not headings:
            self.errors.append(f"Document index '{name}' has no bucket headings")
            return

        if bucket_config.heading_pattern:
            heading_re = re.compile(bucket_config.heading_pattern)
            for line_num, heading in headings.items():
                if not heading_re.match(heading):
                    self.errors.append(f"Document index '{name}' line {line_num} has invalid bucket heading: {heading}")

        sorted_headings = sorted(headings.items())
        buckets = set(headings.values())

        def bucket_at_line(line_num: int) -> str | None:
            current = None
            for heading_line, heading in sorted_headings:
                if heading_line >= line_num:
                    break
                current = heading
            return current

        for target_path in sorted(target_paths):
            try:
                expected_bucket = self._bucket_for_target(target_path, bucket_config)
            except Exception as e:
                rel_target = target_path.relative_to(config_base)
                self.errors.append(f"Document index '{name}' cannot read bucket for {rel_target}: {e}")
                continue

            rel_target = target_path.relative_to(config_base)
            if not expected_bucket:
                self.errors.append(f"Document index '{name}' cannot determine bucket for {rel_target}")
                continue
            if expected_bucket not in buckets:
                self.errors.append(f"Document index '{name}' missing bucket heading: {expected_bucket}")
                continue
            if target_path not in links:
                continue

            line_num, _ = links[target_path]
            actual_bucket = bucket_at_line(line_num)
            if actual_bucket != expected_bucket:
                self.errors.append(
                    f"Document index '{name}' links {rel_target} under '{actual_bucket}' instead of '{expected_bucket}'"
                )

    def check_typescript_config(self):
        """Run TypeScript typecheck on Docusaurus config"""
        self.log("\n🔍 Running TypeScript typecheck...")

        docusaurus_dir = self.repo_root / "docusaurus"
        if not docusaurus_dir.exists():
            self.log("   ⚠️  Docusaurus directory not found, skipping typecheck")
            return True

        try:
            result = subprocess.run(
                ["npm", "run", "typecheck"],
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=docusaurus_dir,
            )

            if result.returncode == 0:
                self.log("   ✓ TypeScript typecheck passed")
                return True
            error = "TypeScript typecheck failed"
            self.errors.append(error)
            self.log(f"   ✗ {error}")
            if self.verbose:
                self.log(f"      {result.stderr}")
            return False

        except subprocess.TimeoutExpired:
            error = "TypeScript typecheck timed out"
            self.errors.append(error)
            self.log(f"   ✗ {error}")
            return False
        except FileNotFoundError:
            self.log("   ⚠️  npm not found, skipping typecheck")
            return True
        except Exception as e:
            error = f"Error running typecheck: {e}"
            self.errors.append(error)
            self.log(f"   ✗ {error}")
            return False

    def check_docusaurus_build(self, skip_build: bool = False):
        """Run Docusaurus build to catch compilation errors"""
        if skip_build:
            self.log("\n⏭️  Skipping Docusaurus build check (--skip-build)")
            return True

        self.log("\n🏗️  Running Docusaurus build validation...")
        self.log("   This may take a minute...")

        docusaurus_dir = self.repo_root / "docusaurus"
        if not docusaurus_dir.exists():
            self.log("   ⚠️  Docusaurus directory not found, skipping build check")
            return True

        try:
            result = subprocess.run(
                ["npm", "run", "build"],
                check=False,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes
                cwd=docusaurus_dir,
            )

            output = result.stdout + result.stderr

            # Extract warnings
            warning_pattern = re.compile(r"Warning:\s+(.+)")
            warnings = warning_pattern.findall(output)

            if result.returncode == 0:
                self.log("   ✓ Docusaurus build succeeded")
                if warnings:
                    self.log(f"   ⚠️  Build completed with {len(warnings)} warning(s)")
                    if self.verbose:
                        for warning in warnings[:5]:
                            self.log(f"      {warning}")
                        if len(warnings) > 5:
                            self.log(f"      ... and {len(warnings) - 5} more warnings")
                return True
            # Extract error details
            error_pattern = re.compile(r"Error:\s+(.+)")
            errors = error_pattern.findall(output)

            error_msg = "Docusaurus build failed"
            self.errors.append(error_msg)
            self.log(f"   ✗ {error_msg}")

            if errors:
                for error in errors[:3]:
                    self.log(f"      {error}")
                    self.errors.append(f"Build error: {error}")
            elif self.verbose:
                # Show last 500 chars if no specific error found
                self.log(f"      {output[-500:]}")

            return False

        except subprocess.TimeoutExpired:
            error = "Docusaurus build timed out (5 minutes)"
            self.errors.append(error)
            self.log(f"   ✗ {error}")
            return False
        except FileNotFoundError:
            self.log("   ⚠️  npm not found, skipping build check")
            return True
        except Exception as e:
            error = f"Error running build: {e}"
            self.errors.append(error)
            self.log(f"   ✗ {error}")
            return False

    def check_code_blocks(self):
        """Check code block formatting - balanced and properly labeled

        Rules (per CommonMark/MDX spec):
        - Opening fence: ``` followed by optional language (e.g., ```python, ```text)
        - Closing fence: ``` with NO language or other text
        - Blank line required before opening fence (except at document start or after frontmatter)
        - Blank line required after closing fence (except at document end)
        - Content: Everything between opening and closing is treated as content
        """
        self.log("\n📝 Checking code blocks...")

        total_valid = 0
        total_invalid = 0

        for doc in self.documents:
            try:
                content = doc.get_content()
                lines = content.split("\n")

                in_code_block = False
                in_frontmatter = False
                frontmatter_count = 0
                opening_line = None
                opening_language = None
                doc_valid_blocks = 0
                doc_invalid_blocks = 0
                closing_fence_line = None  # Track last closing fence for newline check
                previous_line_blank = True  # Track if previous line was blank
                frontmatter_end_line = None  # Track where frontmatter ends

                for line_num, line in enumerate(lines, start=1):
                    stripped = line.strip()

                    # Track frontmatter (first --- to second ---)
                    if stripped == "---":
                        frontmatter_count += 1
                        if frontmatter_count == 1:
                            in_frontmatter = True
                        elif frontmatter_count == 2:
                            in_frontmatter = False
                            frontmatter_end_line = line_num
                        continue

                    # Skip frontmatter content
                    if in_frontmatter:
                        continue

                    # Check if this line is a code fence (must start with exactly ``` or more backticks)
                    # Per CommonMark: fence must be at least 3 backticks
                    fence_match = re.match(r"^(`{3,})", stripped)
                    if not fence_match:
                        # Check if previous line was a closing fence and this line is not blank
                        if closing_fence_line is not None and closing_fence_line == line_num - 1:
                            if stripped and line_num <= len(lines):
                                # Non-blank line immediately after closing fence
                                error = f"Line {closing_fence_line}: Missing blank line after closing code fence (found content at line {line_num})"
                                doc.errors.append(error)
                                self.log(
                                    f"   ✗ {doc.file_path.name}:{closing_fence_line} - No blank line after closing fence"
                                )
                                doc_invalid_blocks += 1
                                total_invalid += 1
                            closing_fence_line = None  # Reset after check

                        # Track if this line is blank for next iteration
                        previous_line_blank = not stripped
                        continue

                    # This is a fence line
                    fence_backticks = fence_match.group(1)
                    remainder = stripped[len(fence_backticks) :].strip()

                    if not in_code_block:
                        # Opening fence - check for blank line before
                        # Exception: first line after frontmatter or very beginning of content
                        content_start = (frontmatter_end_line + 1) if frontmatter_end_line else 1
                        is_after_frontmatter = frontmatter_end_line and line_num == frontmatter_end_line + 1
                        is_document_start = line_num == content_start

                        if not previous_line_blank and not is_after_frontmatter and not is_document_start:
                            error = f"Line {line_num}: Missing blank line before opening code fence"
                            doc.errors.append(error)
                            self.log(f"   ✗ {doc.file_path.name}:{line_num} - No blank line before opening fence")
                            doc_invalid_blocks += 1
                            total_invalid += 1

                        if not remainder:
                            # Bare opening fence - INVALID (must have language)
                            error = f"Line {line_num}: Opening code fence missing language (use ```text for plain text)"
                            doc.errors.append(error)
                            self.log(f"   ✗ {doc.file_path.name}:{line_num} - Opening fence without language")
                            doc_invalid_blocks += 1
                            total_invalid += 1
                            # Still track as opening to detect closing
                            in_code_block = True
                            opening_line = line_num
                            opening_language = "<none>"
                        else:
                            # Valid opening with language
                            in_code_block = True
                            opening_line = line_num
                            opening_language = remainder.split()[0] if remainder else "<none>"

                        # Reset blank line tracking when entering code block
                        previous_line_blank = False
                    else:
                        # Closing fence
                        if remainder:
                            # Closing fence has extra text - this might indicate an unclosed block earlier
                            # If the remainder looks like a language specifier (single word, lowercase/numbers),
                            # this is likely an opening fence that's being misinterpreted as closing
                            looks_like_language = remainder and " " not in remainder and len(remainder) <= 20

                            if looks_like_language and opening_line:
                                # Strong signal: unclosed block earlier
                                error = f"Unclosed code block starting at line {opening_line} (```{opening_language})"
                                doc.errors.append(error)
                                self.log(f"   ✗ {doc.file_path.name} - Unclosed block at line {opening_line}")
                                error = f"Line {line_num}: This appears to be a new opening fence (```{remainder}), but was interpreted as a closing fence due to the unclosed block above"
                                doc.errors.append(error)
                                self.log(f"   ℹ {doc.file_path.name}:{line_num} - Cascading error from unclosed block")
                                doc_invalid_blocks += 2  # Count both errors
                                total_invalid += 2
                                # Reset state and treat this as opening fence
                                in_code_block = True
                                opening_line = line_num
                                opening_language = remainder
                                previous_line_blank = False
                                continue

                            # Actual closing fence with extra text
                            error = f"Line {line_num}: Closing code fence has extra text (```{remainder}), should be just ```"
                            doc.errors.append(error)
                            self.log(f"   ✗ {doc.file_path.name}:{line_num} - Closing fence with text '```{remainder}'")
                            doc_invalid_blocks += 1
                            total_invalid += 1
                        else:
                            # Valid closing fence
                            doc_valid_blocks += 1
                            total_valid += 1
                            closing_fence_line = line_num  # Mark for newline check

                        # Mark block as closed regardless
                        in_code_block = False
                        opening_line = None
                        opening_language = None
                        # Reset blank line tracking - fence line itself is not blank
                        previous_line_blank = False

                # Check for unclosed code block
                if in_code_block:
                    error = f"Unclosed code block starting at line {opening_line} (```{opening_language})"
                    doc.errors.append(error)
                    self.log(f"   ✗ {doc.file_path.name} - Unclosed block at line {opening_line}")
                    doc_invalid_blocks += 1
                    total_invalid += 1

                # Report per-document summary
                if doc_valid_blocks > 0 or doc_invalid_blocks > 0:
                    if doc_invalid_blocks == 0:
                        self.log(f"   ✓ {doc.file_path.name}: {doc_valid_blocks} valid code blocks")
                    else:
                        self.log(f"   ✗ {doc.file_path.name}: {doc_valid_blocks} valid, {doc_invalid_blocks} invalid")

            except Exception as e:
                doc.errors.append(f"Error checking code blocks: {e}")
                self.log(f"   ✗ {doc.file_path.name}: Exception - {e}")

        self.log(
            f"\n   Total: {total_valid} valid code blocks, {total_invalid} invalid code blocks across {len(self.documents)} documents"
        )

    def check_formatting(self):
        """Check markdown formatting issues"""
        self.log("\n📝 Checking formatting...")

        for doc in self.documents:
            try:
                content = doc.get_content()
                lines = content.split("\n")

                # FMT-012: a UTF-8 BOM hides the opening '---' from the
                # frontmatter parser. Documents are read with the BOM stripped,
                # so the file itself has to be consulted for the marker.
                if has_bom(doc.file_path):
                    doc.errors.append(FMT_012_FINDING_MESSAGE)
                    self.log(f"   ✗ {doc.file_path.name}: {FMT_012_FINDING_MESSAGE}")

                # FMT-010: `content` has already been through universal
                # newlines, so a CRLF is invisible there too and the bytes on
                # disk are the only witness. One finding per offending line,
                # the way FMT-001 reports trailing whitespace.
                for line_num, kind in carriage_return_lines(doc.file_path):
                    message = line_ending_finding_message(line_num, kind)
                    doc.errors.append(message)
                    self.log(f"   ✗ {doc.file_path.name}: {message}")

                # Check for trailing whitespace
                for line_num, line in enumerate(lines, start=1):
                    if line.rstrip() != line:
                        doc.errors.append(f"Line {line_num}: Trailing whitespace")

                # FMT-002: runs of more than two blank lines, one finding per
                # line past the second so the numbers line up with FMT-001.
                # Blank lines inside a code fence or the frontmatter block are
                # content, not formatting, and are neither reported here nor
                # collapsed by FMT-011 - the two share `blank_line_runs` so a
                # fixing run cannot leave a finding the fixer thinks it fixed.
                for run in blank_line_runs(content):
                    for line_num in run.excess_lines:
                        doc.errors.append(blank_line_finding_message(line_num))

            except Exception as e:
                doc.errors.append(f"Error checking formatting: {e}")

    def check_readability(self):
        """Check document readability using textstat metrics (RD-001).

        Settings are resolved per document from the (sub-)project that owns
        it, so a sub-project can enable, disable or tune readability on its
        own.
        """
        if not TEXTSTAT_AVAILABLE:
            self.log("\n📖 Readability checking skipped (textstat not installed)")
            return

        if not self.project_config:
            self.log("\n📖 Readability checking disabled")
            return

        # Each document is scored with the settings of the config that owns
        # it; identical settings share one scorer.
        enabled_docs: list[tuple[Document, DocsProjectReadability]] = []
        for doc in self.documents:
            settings = self._readability_config_for(doc.file_path)
            if settings and settings.enabled:
                enabled_docs.append((doc, settings))

        if not enabled_docs:
            self.log("\n📖 Readability checking disabled")
            return

        self.log("\n📖 Checking readability...")

        scorers: dict[str, ReadabilityScorer] = {}

        for doc, settings in enabled_docs:
            scorer_key = settings.model_dump_json()
            scorer = scorers.get(scorer_key)
            if scorer is None:
                scorer = ReadabilityScorer(settings.to_readability_config())
                scorers[scorer_key] = scorer

            try:
                content = doc.get_content()
                report = scorer.analyze_document(content, file_path=str(doc.file_path.relative_to(self.repo_root)))

                if report.has_errors():
                    for line_num, error_msg in report.get_all_errors():
                        doc.errors.append(f"Line {line_num}: {error_msg}")
                        self.log(f"   ✗ {doc.file_path.name}:{line_num}: {error_msg}")
                else:
                    self.log(f"   ✓ {doc.file_path.name}: {report.total_paragraphs} paragraphs analyzed, all readable")

            except Exception as e:
                doc.errors.append(f"Error checking readability: {e}")
                self.log(f"   ✗ {doc.file_path.name}: Readability check failed: {e}")

    def check_project_ids(self):
        """Validate `project_id` against the governing config (FM-010).

        The governing config is the deepest one that owns the document's
        folder, so a monorepo is not flattened to a single ID: a document in
        a sub-project is compared against that sub-project's `project.id`.
        Documents that no config governs, and documents whose frontmatter has
        no `project_id` key at all (FM-002 and FM-005 own that), are skipped.
        """
        self.log("\n🏷️  Checking project_id...")

        if not self.project_configs:
            self.log("   ⊘ No project config loaded; project_id check skipped")
            return

        mismatches = 0
        for doc in self.documents:
            if doc.project_id is None:
                continue

            context = self._config_context_for_path(doc.file_path)
            if context is None:
                continue

            expected = context.config.project.id
            if doc.project_id == expected:
                self.log(f"   ✓ {doc.file_path.name}: project_id='{expected}'")
                continue

            actual = doc.project_id if doc.project_id else "(empty)"
            error = (
                f"FM-010: project_id '{actual}' does not match project.id '{expected}' "
                f"in {self._display_path(context.path)}"
            )
            doc.errors.append(error)
            self.log(f"   ✗ {doc.file_path.name}: {error}")
            mismatches += 1

        if mismatches == 0:
            self.log("   ✓ All project_id values match their governing config")
        else:
            self.log(f"   ✗ Found {mismatches} project_id mismatch(es)")

    def check_date_formats(self):
        """Validate `created` and `updated` date formats (FM-011).

        Only two forms are accepted, the ones the bundled templates use:
        `YYYY-MM-DD` and `YYYY-MM-DDTHH:MM:SSZ`. Everything else is reported
        with the value as written, including a UTC offset (`+00:00`) and a
        timestamp with no zone at all, because RFC-003 names `Z` and `Z` is
        what docuchango writes wherever it generates a timestamp.

        Phase 1 runs first, so a value FM-006 recognizes (`2026/09/14`,
        `14.09.2026`, `September 14, 2026`, ...) is already ISO 8601 by the
        time this runs and nothing is reported; a `--dry-run` reports both
        FM-006's proposed rewrite and this finding, the way FMT-012 does. A
        format FM-006 cannot identify stays a report in either mode: guessing
        the intent of `01/02/2024` is exactly what the fixer refuses to do.

        A field that is absent or explicitly null is skipped: the schema check
        (FM-002) owns a missing `created`, and `updated` is not in any schema.
        """
        self.log("\n📅 Checking date formats...")

        findings = 0
        for doc in self.documents:
            for field_name in DATE_FIELDS:
                value = doc.date_source.get(field_name)
                if value is None or is_accepted_date_format(value):
                    continue
                shown = f"'{value}'" if value.strip() else "(empty)"
                error = f"FM-011: Frontmatter field '{field_name}': {shown} is not {FM_011_ACCEPTED_FORMS}"
                doc.errors.append(error)
                self.log(f"   ✗ {doc.file_path.name}: {error}")
                findings += 1

        if findings == 0:
            self.log(f"   ✓ All created/updated values are {FM_011_ACCEPTED_FORMS}")
        else:
            self.log(f"   ✗ Found {findings} unrecognized date format(s)")

    def _display_path(self, path: Path) -> str:
        """Render a path relative to the repository root when it is inside it."""
        try:
            return str(path.resolve().relative_to(self.repo_root))
        except ValueError:
            return str(path)

    def check_ids(self):
        """Validate document IDs for consistency and uniqueness"""
        self.log("\n🆔 Checking document IDs...")

        # Track IDs for uniqueness check
        seen_ids: dict[str, Path] = {}
        id_errors = 0

        for doc in self.documents:
            # Skip docs without doc_type (generic docs)
            if doc.doc_type not in ["adr", "rfc", "memo", "prd"]:
                continue

            # Check if ID exists
            if not doc.doc_id:
                error = "Missing 'id' field in frontmatter"
                doc.errors.append(error)
                self.log(f"   ✗ {doc.file_path.name}: {error}")
                id_errors += 1
                continue

            # Extract expected ID from filename
            filename = doc.file_path.name

            # Check ID matches filename
            if doc.expected_id and doc.doc_id != doc.expected_id:
                error = f"ID mismatch: frontmatter has '{doc.doc_id}' but filename suggests '{doc.expected_id}'"
                doc.errors.append(error)
                self.log(f"   ✗ {filename}: {error}")
                id_errors += 1

            # Check ID matches title number
            title_pattern = re.compile(r"^(ADR|RFC|MEMO|PRD)-(\d{3}):", re.IGNORECASE)
            title_match = title_pattern.match(doc.title)
            if title_match:
                title_prefix, title_num = title_match.groups()
                expected_title_id = f"{doc.doc_type}-{title_num}"

                if doc.doc_id != expected_title_id:
                    error = f"ID mismatch with title: frontmatter has '{doc.doc_id}' but title has '{title_prefix}-{title_num}'"
                    doc.errors.append(error)
                    self.log(f"   ✗ {filename}: {error}")
                    id_errors += 1

            # Check for duplicate IDs
            if doc.doc_id in seen_ids:
                other_doc = seen_ids[doc.doc_id]
                error = f"Duplicate ID '{doc.doc_id}' - also used by {other_doc.name}"
                doc.errors.append(error)
                self.log(f"   ✗ {filename}: {error}")
                id_errors += 1
            else:
                seen_ids[doc.doc_id] = doc.file_path
                self.log(f"   ✓ {filename}: id='{doc.doc_id}'")

        if id_errors == 0:
            self.log(f"   ✓ All document IDs are valid and unique ({len(seen_ids)} IDs checked)")
        else:
            self.log(f"   ✗ Found {id_errors} ID validation error(s)")

    @staticmethod
    def _format_number_ranges(numbers: list[int]) -> str:
        """Render sorted numbers as a compact range list: ``3, 7-9``."""
        if not numbers:
            return ""
        parts: list[str] = []
        start = previous = numbers[0]
        for number in numbers[1:]:
            if number == previous + 1:
                previous = number
                continue
            parts.append(str(start) if start == previous else f"{start}-{previous}")
            start = previous = number
        parts.append(str(start) if start == previous else f"{start}-{previous}")
        return ", ".join(parts)

    @staticmethod
    def _numbering_gap_types(context: ProjectConfigContext) -> set[str]:
        """Document types whose config opts into ID-010 for this (sub-)project.

        The opt-in lives on the per-type block, so it is keyed by the schema
        that block binds: two `doc_types` entries that bind the same schema
        share one numbering sequence, and enabling the flag on either reports
        that whole sequence.
        """
        structure = context.config.structure
        if not structure or not structure.doc_types:
            return set()
        return {cfg.frontmatter_schema for cfg in structure.doc_types.values() if cfg.report_numbering_gaps}

    def check_numbering_gaps(self):
        """Report missing numbers in a document type's id sequence (ID-010).

        Opt-in per type via
        `structure.doc_types.<type>.report_numbering_gaps: true`, because a
        gap is usually deliberate: a proposal was withdrawn and its number
        was never reused. Numbering is grouped per (governing config, id
        prefix), so the two `adr/` folders of a monorepo are two independent
        sequences rather than one with holes in it. Report only - the remedy
        is `docuchango bulk compress-ids`, which renumbers each type into a
        contiguous sequence and rewrites the references.
        """
        self.log("\n🔢 Checking numbering gaps...")

        if not self.project_configs:
            self.log("   ⊘ No project config loaded; numbering gap check skipped")
            return

        # An id is part of a numbering sequence only when it is exactly
        # `<prefix>-<number>`. An ADR amendment id (`adr-043-a1`) hangs off
        # its parent and is never a number of its own.
        id_pattern = re.compile(r"^([A-Za-z][A-Za-z0-9]*)-(\d+)$")

        # (config path, id prefix) -> number -> the doc_id that claimed it
        groups: dict[tuple[Path, str], dict[int, str]] = {}
        enabled_cache: dict[Path, set[str]] = {}
        for doc in self.documents:
            if not doc.doc_id:
                continue
            match = id_pattern.match(doc.doc_id)
            if not match:
                continue

            context = self._config_context_for_path(doc.file_path)
            if context is None:
                continue
            enabled = enabled_cache.get(context.path)
            if enabled is None:
                enabled = self._numbering_gap_types(context)
                enabled_cache[context.path] = enabled
            if doc.doc_type not in enabled:
                continue

            prefix, number_text = match.groups()
            groups.setdefault((context.path, prefix.lower()), {}).setdefault(int(number_text), doc.doc_id)

        if not groups:
            self.log("   ⊘ No document type opts into numbering gap reporting")
            return

        gaps_found = 0
        for (config_path, prefix), numbers in sorted(groups.items(), key=lambda item: (str(item[0][0]), item[0][1])):
            ordered = sorted(numbers)
            lowest, highest = ordered[0], ordered[-1]
            missing = [number for number in range(lowest, highest + 1) if number not in numbers]
            if not missing:
                self.log(f"   ✓ {prefix}: {len(ordered)} contiguous ids ({numbers[lowest]}..{numbers[highest]})")
                continue

            error = (
                f"ID-010: {prefix} numbering in {self._display_path(config_path)} has gaps: "
                f"missing {self._format_number_ranges(missing)} "
                f"(lowest {numbers[lowest]}, highest {numbers[highest]}); "
                f"run 'docuchango bulk compress-ids' to renumber"
            )
            self.errors.append(error)
            self.log(f"   ✗ {error}")
            gaps_found += 1

        if gaps_found == 0:
            self.log("   ✓ No numbering gaps found")

    def check_uuids(self):
        """Validate document UUIDs for uniqueness"""
        self.log("\n🔑 Checking document UUIDs...")

        # Track UUIDs for uniqueness check
        seen_uuids: dict[str, Path] = {}
        uuid_errors = 0

        for doc in self.documents:
            # Skip docs without doc_type (generic docs) or without UUID
            if doc.doc_type not in ["adr", "rfc", "memo", "prd"] or not doc.doc_uuid:
                continue

            # Check for duplicate UUIDs
            if doc.doc_uuid in seen_uuids:
                other_doc = seen_uuids[doc.doc_uuid]
                error = f"Duplicate UUID '{doc.doc_uuid}' - also used by {other_doc.name}"
                doc.errors.append(error)
                self.log(f"   ✗ {doc.file_path.name}: {error}")
                uuid_errors += 1
            else:
                seen_uuids[doc.doc_uuid] = doc.file_path
                self.log(f"   ✓ {doc.file_path.name}: doc_uuid='{doc.doc_uuid[:8]}...'")

        if uuid_errors == 0:
            self.log(f"   ✓ All document UUIDs are unique ({len(seen_uuids)} UUIDs checked)")
        else:
            self.log(f"   ✗ Found {uuid_errors} UUID uniqueness error(s)")

    def generate_report(self) -> tuple[bool, str]:
        """Generate validation report"""
        lines = []
        lines.append("\n" + "=" * 80)
        lines.append("📊 DOCUMENTATION VALIDATION REPORT")
        lines.append("=" * 80)

        # Summary
        total_docs = len(self.documents)
        docs_with_errors = sum(1 for d in self.documents if d.errors)
        total_links = len(self.all_links)
        valid_links = sum(1 for link in self.all_links if link.is_valid)
        broken_links = total_links - valid_links

        lines.append(f"\n📄 Documents scanned: {total_docs}")
        lines.append(f"   ADRs: {sum(1 for d in self.documents if d.doc_type == 'adr')}")
        lines.append(f"   RFCs: {sum(1 for d in self.documents if d.doc_type == 'rfc')}")
        lines.append(f"   MEMOs: {sum(1 for d in self.documents if d.doc_type == 'memo')}")
        lines.append(f"   Docs: {sum(1 for d in self.documents if d.doc_type == 'doc')}")

        lines.append(f"\n🔗 Total links: {total_links}")
        lines.append(f"   Valid: {valid_links}")
        lines.append(f"   Broken: {broken_links}")

        # Link breakdown
        link_counts: dict[LinkType, int] = {}
        for link in self.all_links:
            link_counts[link.link_type] = link_counts.get(link.link_type, 0) + 1

        lines.append("\n📋 Link Types:")
        for link_type, count in sorted(link_counts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"   {link_type.value}: {count}")

        # Tags summary (union of all tags)
        all_tags: dict[str, int] = {}
        for doc in self.documents:
            for tag in doc.tags:
                all_tags[tag] = all_tags.get(tag, 0) + 1

        if all_tags:
            lines.append(f"\n🏷️  Tags (union across all documents): {len(all_tags)} unique tags")
            # Show top 15 tags by usage
            sorted_tags = sorted(all_tags.items(), key=lambda x: x[1], reverse=True)
            for tag, count in sorted_tags[:15]:
                lines.append(f"   {tag}: {count} document(s)")
            if len(sorted_tags) > 15:
                lines.append(f"   ... and {len(sorted_tags) - 15} more tags")

        # Document errors
        if docs_with_errors > 0:
            lines.append(f"\n❌ DOCUMENTS WITH ERRORS ({docs_with_errors}):")
            lines.append("-" * 80)

            for doc in self.documents:
                if doc.errors:
                    lines.append(f"\n📄 {doc.file_path.relative_to(self.repo_root)}")
                    lines.append(f"   Title: {doc.title}")
                    for error in doc.errors:
                        lines.append(f"   ✗ {error}")

        # Broken links
        if broken_links > 0:
            lines.append(f"\n❌ BROKEN LINKS ({broken_links}):")
            lines.append("-" * 80)

            broken_by_doc: dict[Path, list[Link]] = {}
            for link in self.all_links:
                if not link.is_valid:
                    if link.source_doc not in broken_by_doc:
                        broken_by_doc[link.source_doc] = []
                    broken_by_doc[link.source_doc].append(link)

            for doc_path, doc_links in sorted(broken_by_doc.items()):
                lines.append(f"\n📄 {doc_path.relative_to(self.repo_root)}")
                for link in doc_links:
                    lines.append(f"   Line {link.line_number}: {link.target}")
                    lines.append(f"      → {link.error_message}")

        # Validation-level errors (TypeScript, build, etc.)
        if self.errors:
            lines.append(f"\n❌ VALIDATION ERRORS ({len(self.errors)}):")
            lines.append("-" * 80)
            for error in self.errors:
                lines.append(f"   ✗ {error}")

        # Final status
        lines.append("\n" + "=" * 80)
        if docs_with_errors == 0 and broken_links == 0 and not self.errors:
            lines.append("✅ SUCCESS: All documents valid!")
            all_valid = True
        else:
            lines.append("❌ FAILURE: Validation errors found")
            all_valid = False

            # Add remediation help
            lines.append("")
            lines.append("🔧 REMEDIATION TOOLS:")
            lines.append("")
            lines.append("  Automatically fix common issues:")
            lines.append("    uv run python -m tooling.fix_docs")
            lines.append("")
            lines.append("  Fix specific issues:")
            lines.append("    • Code fence formatting:     uv run python -m tooling.fix_code_blocks_proper <file>")
            lines.append("    • Broken cross-plugin links: uv run python -m tooling.fix_cross_plugin_links")
            lines.append("    • Frontmatter fields:        uv run python -m tooling.add_frontmatter_all")
            lines.append("")
            lines.append("  Manual fixes for:")
            lines.append("    • Broken links: Update file paths to match actual document slugs")
            lines.append("    • Missing files: Ensure referenced documents exist")
            lines.append('    • UUID conflicts: Generate new UUIDs with \'uuidgen | tr "[:upper:]" "[:lower:]"\'')
            lines.append("")

        lines.append("=" * 80 + "\n")

        return all_valid, "\n".join(lines)

    def validate(self, skip_build: bool = False) -> bool:
        """Run full validation pipeline"""
        self.scan_documents()
        self.extract_links()
        self.validate_links()
        self.check_project_ids()  # FM-010: project_id vs the governing config
        self.check_date_formats()  # FM-011: created/updated date formats
        self.check_ids()  # Validate document IDs
        self.check_numbering_gaps()  # ID-010: opt-in numbering gap report
        self.check_uuids()  # Validate document UUID uniqueness
        self.check_code_blocks()  # Check code block balance and labeling
        self.check_mdx_compilation()  # Check MDX compilation with @mdx-js/mdx
        self.check_mdx_compatibility()
        self.check_cross_plugin_links()
        self.check_document_indexes()
        self.check_formatting()
        self.check_readability()  # Check document readability

        # Build validation (can be skipped for faster checks)
        build_passed = self.check_typescript_config()
        build_passed = self.check_docusaurus_build(skip_build) and build_passed

        all_valid, report = self.generate_report()
        print(report)
        return all_valid and build_passed


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate documentation (run before pushing docs)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Full validation (recommended before pushing)
    uv run tooling/validate_docs.py

    # Quick check (skip slow build validation)
    uv run tooling/validate_docs.py --skip-build

    # Verbose output
    uv run tooling/validate_docs.py --verbose

What this checks:
    ✓ YAML frontmatter format
    ✓ Internal link validity
    ✓ MDX syntax compatibility
    ✓ Cross-plugin link issues
    ✓ Document readability metrics
    ✓ TypeScript compilation
    ✓ Full Docusaurus build
        """,
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    parser.add_argument(
        "--skip-build", action="store_true", help="Skip Docusaurus build check (faster, but less thorough)"
    )

    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    validator = DocValidator(repo_root=repo_root, verbose=args.verbose)

    try:
        all_valid = validator.validate(skip_build=args.skip_build)
        sys.exit(0 if all_valid else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
