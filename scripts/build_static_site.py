#!/usr/bin/env python3
"""Build the static GitHub Pages site for Docuchango schemas and templates."""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path
from typing import Any

import tomllib

from docuchango.schemas import (
    ADRFrontmatter,
    GenericDocFrontmatter,
    MemoFrontmatter,
    PRDFrontmatter,
    RFCFrontmatter,
)

BASE_URL = "https://jrepp.github.io/docuchango/"
ROOT = Path("site")
FRONTMATTER_SCHEMAS = {
    "adr.schema.json": ("ADR frontmatter", ADRFrontmatter),
    "rfc.schema.json": ("RFC frontmatter", RFCFrontmatter),
    "memo.schema.json": ("Memo frontmatter", MemoFrontmatter),
    "prd.schema.json": ("PRD frontmatter", PRDFrontmatter),
    "generic.schema.json": ("Generic document frontmatter", GenericDocFrontmatter),
}
REPORTS_DIR = ROOT / "reports"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def render_page(path: Path, title: str, description: str, body: str) -> None:
    canonical = BASE_URL + (
        "" if path.name == "index.html" and path.parent == ROOT else path.relative_to(ROOT).as_posix()
    )
    escaped_title = html.escape(title)
    escaped_description = html.escape(description)
    write_text(
        path,
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_title}</title>
  <meta name="description" content="{escaped_description}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{escaped_title}">
  <meta property="og:description" content="{escaped_description}">
  <meta property="og:url" content="{canonical}">
  <meta name="twitter:card" content="summary">
  <script type="application/ld+json">{{"@context":"https://schema.org","@type":"SoftwareApplication","name":"Docuchango","applicationCategory":"DeveloperApplication","operatingSystem":"Cross-platform","url":"{BASE_URL}","codeRepository":"https://github.com/jrepp/docuchango"}}</script>
  <style>
    :root {{ color-scheme: light dark; --fg: #18202a; --muted: #5b6675; --bg: #f7f3ea; --card: #fffaf0; --line: #d9cbb1; --accent: #6d3bff; }}
    @media (prefers-color-scheme: dark) {{ :root {{ --fg: #f1eadb; --muted: #c9bea8; --bg: #15110d; --card: #211a14; --line: #4a3a2b; --accent: #b9a2ff; }} }}
    * {{ box-sizing: border-box; }} body {{ margin: 0; font: 16px/1.6 ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; color: var(--fg); background: radial-gradient(circle at top left, color-mix(in srgb, var(--accent) 18%, transparent), transparent 28rem), var(--bg); }}
    main {{ max-width: 980px; margin: 0 auto; padding: 4rem 1.25rem; }} header {{ margin-bottom: 2rem; }} h1 {{ font-size: clamp(2.4rem, 6vw, 4.75rem); line-height: .95; letter-spacing: -.05em; margin: 0 0 1rem; }} h2 {{ margin-top: 2.25rem; }} p {{ max-width: 68ch; }} a {{ color: var(--accent); }}
    .lead {{ font-size: 1.2rem; color: var(--muted); }} .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 1rem; margin: 1.5rem 0; }} .card {{ background: color-mix(in srgb, var(--card) 88%, transparent); border: 1px solid var(--line); border-radius: 18px; padding: 1rem; box-shadow: 0 12px 40px color-mix(in srgb, #000 10%, transparent); }}
    .card h3 {{ margin: 0 0 .4rem; }} code {{ background: color-mix(in srgb, var(--line) 35%, transparent); border-radius: .35rem; padding: .1rem .3rem; }} ul {{ padding-left: 1.25rem; }} footer {{ margin-top: 4rem; color: var(--muted); font-size: .95rem; }}
  </style>
</head>
<body><main>{body}<footer>Docuchango static schemas and templates. <a href="https://github.com/jrepp/docuchango">GitHub</a> · <a href="https://pypi.org/project/docuchango/">PyPI</a></footer></main></body>
</html>
""",
    )


def load_security_report() -> dict[str, Any] | None:
    report_path = Path("security-report.json")
    if not report_path.exists():
        return None
    return json.loads(report_path.read_text(encoding="utf-8"))


def load_ci_python_versions() -> list[str]:
    ci_path = Path(".github/workflows/ci.yml")
    versions: list[str] = []
    in_python_versions = False
    for line in ci_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("python-version:"):
            in_python_versions = True
            versions.extend(part.strip().strip("'\"") for part in stripped.split("[", 1)[1].split("]", 1)[0].split(","))
            continue
        if in_python_versions and stripped.startswith("-"):
            versions.append(stripped[1:].strip().strip("'\""))
            continue
        if in_python_versions and stripped and not stripped.startswith("#"):
            break
    return [version for version in versions if version]


def load_coverage_summary() -> dict[str, Any] | None:
    coverage_path = Path("coverage.xml")
    if not coverage_path.exists():
        return None
    coverage_xml = coverage_path.read_text(encoding="utf-8", errors="replace")
    coverage_match = re.search(r"<coverage\b[^>]*>", coverage_xml)
    if coverage_match is None:
        return None
    coverage_tag = coverage_match.group(0)

    def attribute(name: str, default: str = "0") -> str:
        match = re.search(rf'\b{name}="([^"]+)"', coverage_tag)
        return match.group(1) if match else default

    return {
        "line_rate": round(float(attribute("line-rate")) * 100, 2),
        "branch_rate": round(float(attribute("branch-rate")) * 100, 2),
        "lines_covered": int(attribute("lines-covered")),
        "lines_valid": int(attribute("lines-valid")),
        "branches_covered": int(attribute("branches-covered")),
        "branches_valid": int(attribute("branches-valid")),
    }


def summarize_security_report(report: dict[str, Any] | None) -> dict[str, Any]:
    if report is None:
        return {
            "status": "not-generated",
            "vulnerability_count": None,
            "dependency_count": None,
            "message": "Security audit report was not generated for this local build.",
        }
    dependencies = report.get("dependencies", [])
    vulnerabilities = [vuln for dependency in dependencies for vuln in dependency.get("vulns", [])]
    return {
        "status": "pass" if not vulnerabilities else "fail",
        "vulnerability_count": len(vulnerabilities),
        "dependency_count": len(dependencies),
        "message": "No known vulnerabilities found." if not vulnerabilities else "Known vulnerabilities found.",
    }


def main() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]
    version = project["version"]
    requires_python = project["requires-python"]
    classifier_versions = sorted(
        classifier.rsplit(" :: ", 1)[1]
        for classifier in project["classifiers"]
        if classifier.startswith("Programming Language :: Python :: 3.")
    )
    ci_python_versions = load_ci_python_versions()
    coverage_summary = load_coverage_summary()
    security_report = load_security_report()
    security_summary = summarize_security_report(security_report)

    if ROOT.exists():
        shutil.rmtree(ROOT)
    (ROOT / "schemas" / "frontmatter").mkdir(parents=True)
    (ROOT / "templates" / "init").mkdir(parents=True)
    (ROOT / "templates" / "library").mkdir(parents=True)
    REPORTS_DIR.mkdir(parents=True)

    shutil.copy2("docuchango/templates/docs-project.schema.json", ROOT / "schemas" / "docs-project.schema.json")
    for source in Path("docuchango/templates").iterdir():
        if source.is_file():
            shutil.copy2(source, ROOT / "templates" / "init" / source.name)
    for source in Path("templates").iterdir():
        if source.is_file():
            shutil.copy2(source, ROOT / "templates" / "library" / source.name)

    for filename, (title, model) in FRONTMATTER_SCHEMAS.items():
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        schema["$id"] = f"https://jrepp.github.io/docuchango/schemas/frontmatter/{filename}"
        schema["title"] = title
        write_text(ROOT / "schemas" / "frontmatter" / filename, json.dumps(schema, indent=2) + "\n")

    conformance_report = {
        "name": "docuchango",
        "version": version,
        "requires_python": requires_python,
        "declared_python_classifiers": classifier_versions,
        "ci_python_matrix": ci_python_versions,
        "supported_python_versions": ci_python_versions or classifier_versions,
        "coverage": coverage_summary,
        "checks": {
            "unit_tests": "CI runs pytest with coverage for every supported Python version.",
            "lint": "CI runs ruff format, ruff lint, and mypy.",
            "build": "CI runs uv build and twine check.",
            "workflow_lint": "CI runs actionlint.",
        },
    }
    write_text(ROOT / "version.json", json.dumps({"name": "docuchango", "version": version}, indent=2) + "\n")
    write_text(REPORTS_DIR / "python-conformance.json", json.dumps(conformance_report, indent=2) + "\n")
    write_text(REPORTS_DIR / "security-summary.json", json.dumps(security_summary, indent=2) + "\n")
    if security_report is not None:
        write_text(REPORTS_DIR / "security-report.json", json.dumps(security_report, indent=2) + "\n")

    schema_cards = "".join(
        f'<article class="card"><h3>{html.escape(title)}</h3><p><a href="/docuchango/schemas/frontmatter/{filename}">{html.escape(filename)}</a></p></article>'
        for filename, (title, _) in FRONTMATTER_SCHEMAS.items()
    )
    init_templates = "".join(
        f'<li><a href="/docuchango/templates/init/{path.name}">{html.escape(path.name)}</a></li>'
        for path in sorted((ROOT / "templates" / "init").iterdir())
    )
    library_templates = "".join(
        f'<li><a href="/docuchango/templates/library/{path.name}">{html.escape(path.name)}</a></li>'
        for path in sorted((ROOT / "templates" / "library").iterdir())
    )
    python_tags = "".join(
        f"<code>Python {html.escape(version)}</code> " for version in ci_python_versions or classifier_versions
    )
    coverage_text = (
        f"Line coverage: <code>{coverage_summary['line_rate']}%</code>. Branch coverage: <code>{coverage_summary['branch_rate']}%</code>."
        if coverage_summary
        else "Coverage summary is populated when <code>coverage.xml</code> is available."
    )
    security_status = html.escape(security_summary["status"])
    security_message = html.escape(security_summary["message"])

    render_page(
        ROOT / "index.html",
        "Docuchango schemas and templates",
        "Static JSON schemas, frontmatter schemas, markdown document templates, and version metadata for Docuchango.",
        f"""<header><h1>Docuchango schemas and templates</h1><p class="lead">Indexed static assets for validating and authoring Docuchango documentation projects.</p></header>
<section class="grid"><article class="card"><h2>Config schema</h2><p><a href="/docuchango/schemas/docs-project.schema.json">docs-project.schema.json</a></p></article><article class="card"><h2>Frontmatter schemas</h2><p><a href="/docuchango/schemas/frontmatter/">ADR, RFC, Memo, PRD, and generic document schemas</a></p></article><article class="card"><h2>Templates</h2><p><a href="/docuchango/templates/">Init templates and reusable document templates</a></p></article><article class="card"><h2>Version</h2><p>Current package version: <code>{html.escape(version)}</code>. <a href="/docuchango/version.json">version.json</a></p></article><article class="card"><h2>Python support</h2><p>{python_tags}</p><p><a href="/docuchango/reports/python-conformance.html">Conformance report</a></p></article><article class="card"><h2>Security</h2><p>Status: <code>{security_status}</code>. {security_message}</p><p><a href="/docuchango/reports/security.html">Security report</a></p></article></section>""",
    )
    render_page(
        ROOT / "schemas" / "index.html",
        "Docuchango JSON schemas",
        "Index of Docuchango JSON schemas for docs-project.yaml and document frontmatter.",
        f"""<header><h1>JSON schemas</h1><p class="lead">Use these stable URLs for editor validation, automation, and prompt context.</p></header><section class="grid"><article class="card"><h2>Project config</h2><p><a href="/docuchango/schemas/docs-project.schema.json">docs-project.schema.json</a></p></article>{schema_cards}</section>""",
    )
    render_page(
        ROOT / "schemas" / "frontmatter" / "index.html",
        "Docuchango frontmatter schemas",
        "JSON Schema index for Docuchango ADR, RFC, Memo, PRD, and generic document frontmatter.",
        f"""<header><h1>Frontmatter schemas</h1><p class="lead">Generated from the Pydantic models in <code>docuchango.schemas</code>.</p></header><section class="grid">{schema_cards}</section>""",
    )
    render_page(
        ROOT / "templates" / "index.html",
        "Docuchango document templates",
        "Index of Docuchango Markdown templates for project initialization and reusable documentation workflows.",
        f"""<header><h1>Document templates</h1><p class="lead">Raw Markdown templates published for agents, editors, and bootstrap scripts.</p></header><section class="grid"><article class="card"><h2>Init templates</h2><ul>{init_templates}</ul></article><article class="card"><h2>Template library</h2><ul>{library_templates}</ul></article></section>""",
    )
    render_page(
        REPORTS_DIR / "python-conformance.html",
        "Docuchango Python conformance report",
        "Python version support, CI matrix, packaging checks, type checks, and coverage metadata for Docuchango.",
        f"""<header><h1>Python conformance</h1><p class="lead">Docuchango declares <code>{html.escape(requires_python)}</code> and tests these versions in CI.</p></header><section class="grid"><article class="card"><h2>Supported versions</h2><p>{python_tags}</p></article><article class="card"><h2>Quality gates</h2><ul><li>pytest with coverage across the Python matrix</li><li>ruff format and lint</li><li>mypy type checks</li><li>uv build and twine check</li><li>actionlint for workflows</li></ul></article><article class="card"><h2>Coverage</h2><p>{coverage_text}</p></article><article class="card"><h2>JSON</h2><p><a href="/docuchango/reports/python-conformance.json">python-conformance.json</a></p></article></section>""",
    )
    security_links = '<p><a href="/docuchango/reports/security-summary.json">security-summary.json</a></p>'
    if security_report is not None:
        security_links += '<p><a href="/docuchango/reports/security-report.json">security-report.json</a></p>'
    render_page(
        REPORTS_DIR / "security.html",
        "Docuchango security report",
        "Dependency vulnerability audit summary for Docuchango generated with pip-audit.",
        f"""<header><h1>Security report</h1><p class="lead">Dependency vulnerability audit summary generated during the Pages build.</p></header><section class="grid"><article class="card"><h2>Status</h2><p><code>{security_status}</code></p><p>{security_message}</p></article><article class="card"><h2>Dependencies</h2><p><code>{html.escape(str(security_summary["dependency_count"]))}</code></p></article><article class="card"><h2>Vulnerabilities</h2><p><code>{html.escape(str(security_summary["vulnerability_count"]))}</code></p></article><article class="card"><h2>Raw reports</h2>{security_links}</article></section>""",
    )

    urls = [
        "",
        "schemas/",
        "schemas/frontmatter/",
        "templates/",
        "reports/python-conformance.html",
        "reports/python-conformance.json",
        "reports/security.html",
        "reports/security-summary.json",
        "schemas/docs-project.schema.json",
        "version.json",
    ]
    if security_report is not None:
        urls.append("reports/security-report.json")
    urls.extend(f"schemas/frontmatter/{filename}" for filename in FRONTMATTER_SCHEMAS)
    urls.extend(f"templates/init/{path.name}" for path in sorted((ROOT / "templates" / "init").iterdir()))
    urls.extend(f"templates/library/{path.name}" for path in sorted((ROOT / "templates" / "library").iterdir()))
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += "".join(f"  <url><loc>{BASE_URL}{url}</loc></url>\n" for url in urls)
    sitemap += "</urlset>\n"
    write_text(ROOT / "sitemap.xml", sitemap)
    write_text(ROOT / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}sitemap.xml\n")
    write_text(ROOT / ".nojekyll", "")


if __name__ == "__main__":
    main()
