"""Documentation fix modules.

This package contains modules for automatically fixing common documentation issues:
- broken_links: Fix broken internal and cross-reference links
- code_blocks: Fix code block formatting and language tags
- code_blocks_proper: Alternative code block formatter
- cross_plugin_links: Fix cross-plugin link references
- doc_links: Fix documentation link issues
- docs: General documentation fixes (whitespace, frontmatter, etc.)
- internal_links: Fix internal link references
- mdx_code_blocks: Fix MDX-specific code block issues
- mdx_syntax: Fix MDX syntax issues
- migration_syntax: Fix syntax during migrations
- proto_imports: Fix protocol buffer import statements
"""

__all__ = [
    "broken_links",
    "code_blocks",
    "code_blocks_proper",
    "cross_plugin_links",
    "doc_links",
    "docs",
    "internal_links",
    "mdx_code_blocks",
    "mdx_syntax",
    "migration_syntax",
    "proto_imports",
]
