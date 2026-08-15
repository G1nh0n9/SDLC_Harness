# ruff: noqa: E501

from __future__ import annotations

import html
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ARCHITECTURE = DOCS / "architecture"
FULL_MARKDOWN = ARCHITECTURE / "full-architecture.md"
FULL_HTML = DOCS / "agent-harness-architecture.html"

SECTIONS = [
    "overview-and-scope.md",
    "architecture-at-a-glance.md",
    "operating-model-overview.md",
    "worked-mission-overview.md",
    "runtime-overview.md",
    "reliability-overview.md",
    "trust-overview.md",
    "prior-work-overview.md",
    "reference-overview.md",
]

FIGURES = {
    "operating-model-overview.md": (
        "## 2. Areas of responsibility",
        """
<figure class="architecture-figure">
  <div class="figure-scroll"><img src="../assets/architecture/responsibility-and-decision-flow.svg" alt="Requirements and Outcomes, Engineering and Software Delivery, and Verification and Quality Assurance contribute to a joint baseline and deliver work through a policy-controlled decision flow."></div>
  <figcaption><strong>Figure 2. Responsibility and decision flow.</strong> The three areas plan jointly, but Engineering delivers the candidate and QA evaluates it independently. Only the Policy and State Engine can change authoritative workflow state.</figcaption>
</figure>

""",
    ),
    "worked-mission-overview.md": (
        "## 2. Walkthrough",
        """
<figure class="architecture-figure">
  <div class="figure-scroll"><img src="../assets/architecture/mission-lifecycle.svg" alt="The export-ownership mission moves from its approved baseline through expert work, candidate freeze, verification, and the release decision. If a must-pass acceptance criterion fails, correction continues in a child candidate."></div>
  <figcaption><strong>Figure 3. Life of the worked mission.</strong> Each transition requires the specified records. A failed must-pass acceptance criterion leaves the reviewed candidate unchanged and sends correction to a child candidate.</figcaption>
</figure>

""",
    ),
}

LINK_MAP = {
    "overview-and-scope.md": "#1-purpose-and-scope",
    "architecture-at-a-glance.md": "#2-architecture-at-a-glance",
    "operating-model-overview.md": "#3-core-concepts-and-operating-model",
    "worked-mission-overview.md": "#4-worked-mission-export-ownership",
    "runtime-overview.md": "#5-runtime-architecture",
    "reliability-overview.md": "#6-reliability-and-recovery",
    "trust-overview.md": "#7-trust-boundaries",
    "prior-work-overview.md": "#8-prior-work",
    "reference-overview.md": "#9-reference-and-next-reading",
    "reference.md": "#9-reference-and-next-reading",
    "purpose-and-scope.md": "architecture/purpose-and-scope.md",
    "operating-model.md": "architecture/operating-model.md",
    "worked-mission.md": "architecture/worked-mission.md",
    "runtime.md": "architecture/runtime.md",
    "reliability.md": "architecture/reliability.md",
    "trust.md": "architecture/trust.md",
    "prior-work.md": "architecture/prior-work.md",
    "full-architecture.md": "architecture/full-architecture.md",
    "content-coverage.md": "architecture/content-coverage.md",
    "../architecture.md": "architecture.md",
    "../agent-harness-architecture.html": "agent-harness-architecture.html",
    "../user-guide.md": "user-guide.md",
    "../requirements.md": "requirements.md",
    "../adr/README.md": "adr/README.md",
    "../expert-organization-design.md": "expert-organization-design.md",
    "../agent-reliability-survey.md": "agent-reliability-survey.md",
    "../agent-harness-governance.md": "agent-harness-governance.md",
}


def shift_headings(text: str) -> str:
    lines: list[str] = []
    fenced = False
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
            lines.append(line)
            continue
        if not fenced and re.match(r"^#{2,6} ", line):
            line = "#" + line
        lines.append(line)
    return "\n".join(lines).rstrip() + "\n"


def load_section(number: int, filename: str) -> str:
    source = ARCHITECTURE / filename
    text = source.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError(f"missing H1 in {source}")
    title = lines[0][2:].strip()
    body = "\n".join(lines[1:]).lstrip()
    if filename == "prior-work.md":
        body = body.split("\n## Sources", 1)[0].rstrip() + "\n"
    if filename in FIGURES:
        marker, figure = FIGURES[filename]
        if marker not in body:
            raise ValueError(f"figure marker not found in {source}: {marker}")
        body = body.replace(marker, figure + marker, 1)
    return f"## {number}. {title}\n\n{shift_headings(body)}\n"


def rewrite_markdown_links(text: str) -> str:
    for old, new in LINK_MAP.items():
        text = text.replace(f"]({old})", f"]({new})")
    return text


def build_markdown() -> str:
    introduction = """# Evidence-Based Multi-Agent Software Development Harness

> **Architecture guide**
>
> This guide explains the target operating model through one mission. It is not an implementation-status report, a release claim, or a substitute for approved requirements and decision records. Linked deep dives preserve the complete state, event, schema, and source-attribution detail.

An agent's completion claim is not evidence. The architecture below places identity, authority, state transitions, artifact binding, independent judgment, and release behind a policy boundary.

<figure class="architecture-figure">
  <div class="figure-scroll"><img src="../assets/architecture/logical-enforcement-architecture.svg" alt="The Policy and State Engine coordinates the Mission Service, Goal and Quality Planner, Workspace Broker, Task Runner, Candidate Manager, Handoff Verifier, and Quality and Release Decision. Each logical component writes durable records."></div>
  <figcaption><strong>Figure 1. System boundary and logical responsibilities.</strong> The Candidate Manager, Handoff Verifier, and Quality and Release Decision are logical responsibilities, not required deployment units. Blue paths show policy control; dark paths carry work and evidence.</figcaption>
</figure>

## How to read this document

- **Purpose and Scope** explains why the harness is needed and what it promises.
- **Architecture at a Glance** gives the smallest useful system picture.
- **Core Concepts and Operating Model** defines the concepts and decision rights.
- **Worked Mission: `export-ownership`** follows one request to a verified release.
- **Runtime Architecture** maps the same steps to logical components.
- **Reliability and Recovery** adds interruption, retry, and external operations with uncertain outcomes.
- **Trust Boundaries** separates target enforcement from external controls.
- **Prior Work** explains established methods and the harness-specific synthesis.
- **Reference and Next Reading** links deep dives, normative material, and role-specific paths.

Read sections 1 through 7 in order on a first pass. Sections 8 and 9 provide design context and lookup paths. Each chapter links to the detailed source material that it intentionally leaves out.

"""
    sections = "\n".join(load_section(index, name) for index, name in enumerate(SECTIONS, 1))
    prior_work = (ARCHITECTURE / "prior-work.md").read_text(encoding="utf-8")
    _, source_text = prior_work.split("\n## Sources\n", 1)
    sources = "\n## Sources\n\n" + source_text.strip() + "\n"
    return introduction + sections + sources


def render_html(markdown_text: str) -> str:
    converter = markdown.Markdown(
        extensions=["extra", "sane_lists", "toc"],
        extension_configs={"toc": {"permalink": False, "toc_depth": "2-4"}},
        output_format="html5",
    )
    body = converter.convert(rewrite_markdown_links(markdown_text))
    body = body.replace('src="../assets/', 'src="assets/')
    body = re.sub(
        r"(<table>.*?</table>)",
        r'<div class="table-scroll">\1</div>',
        body,
        flags=re.DOTALL,
    )
    toc = converter.toc
    title = "Evidence-Based Multi-Agent Software Development Harness: Architecture"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      --ink: #172033;
      --muted: #526077;
      --line: #d7dee8;
      --line-strong: #aeb9c8;
      --paper: #ffffff;
      --subtle: #f5f7fa;
      --blue: #1f5fbf;
      --blue-light: #eaf2ff;
      --amber: #8a5a00;
      --amber-light: #fff8e6;
      --red: #a33a3a;
      --sidebar: 276px;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{ margin: 0; color: var(--ink); background: var(--paper); font: 16px/1.68 "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
    a {{ color: var(--blue); text-underline-offset: 2px; }}
    .site-header {{ height: 58px; border-bottom: 1px solid var(--line); display: flex; align-items: center; padding: 0 28px; background: #fff; position: sticky; top: 0; z-index: 30; }}
    .product {{ color: var(--ink); font-weight: 670; text-decoration: none; letter-spacing: -.01em; }}
    .product::before {{ content: ""; display: inline-block; width: 9px; height: 9px; margin-right: 10px; background: var(--blue); }}
    .header-meta {{ margin-left: auto; color: var(--muted); font-size: .84rem; }}
    .layout {{ max-width: 1420px; margin: 0 auto; display: grid; grid-template-columns: var(--sidebar) minmax(0, 980px); gap: 54px; padding: 0 28px 90px; }}
    aside {{ position: sticky; top: 76px; align-self: start; height: calc(100vh - 88px); overflow: auto; padding: 32px 12px 32px 0; font-size: .83rem; }}
    .toc-heading {{ margin: 0 0 10px; font-weight: 680; color: var(--ink); }}
    .toc ul {{ list-style: none; margin: 0; padding: 0; }}
    .toc li {{ margin: 0; }}
    .toc li li a {{ padding-left: 24px; font-size: .78rem; }}
    .toc li li li {{ display: none; }}
    .toc a {{ display: block; border-left: 2px solid var(--line); padding: 5px 8px 5px 12px; color: var(--muted); text-decoration: none; line-height: 1.35; }}
    .toc a:hover {{ color: var(--blue); border-left-color: var(--blue); }}
    main {{ min-width: 0; padding-top: 38px; }}
    h1 {{ margin: 0 0 22px; font-size: clamp(2.3rem, 4.4vw, 3.2rem); line-height: 1.12; letter-spacing: -.035em; font-weight: 680; }}
    h2 {{ margin: 64px 0 18px; padding-top: 18px; border-top: 1px solid var(--line); font-size: 2rem; line-height: 1.25; letter-spacing: -.025em; scroll-margin-top: 72px; }}
    h3 {{ margin: 38px 0 12px; font-size: 1.42rem; line-height: 1.3; scroll-margin-top: 72px; }}
    h4 {{ margin: 28px 0 9px; font-size: 1.12rem; line-height: 1.35; scroll-margin-top: 72px; }}
    p {{ margin: 0 0 16px; }}
    main p, main li {{ overflow-wrap: anywhere; }}
    ul, ol {{ margin: 10px 0 20px; padding-left: 26px; }}
    li {{ margin: 5px 0; }}
    blockquote {{ margin: 18px 0 24px; padding: 14px 18px; border-left: 4px solid var(--blue); background: var(--blue-light); color: #26364d; }}
    blockquote + blockquote {{ border-left-color: #bf7a00; background: var(--amber-light); }}
    blockquote p:last-child {{ margin-bottom: 0; }}
    .table-scroll {{ max-width: 100%; overflow-x: auto; margin: 20px 0 30px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 0; font-size: .9rem; }}
    th, td {{ text-align: left; vertical-align: top; padding: 10px 12px; border-bottom: 1px solid var(--line); }}
    th {{ background: var(--subtle); color: #2b394e; font-weight: 670; border-top: 1px solid var(--line); }}
    code {{ font-family: "Cascadia Code", Consolas, monospace; font-size: .88em; background: var(--subtle); border: 1px solid var(--line); padding: 1px 4px; border-radius: 3px; overflow-wrap: anywhere; }}
    pre {{ max-width: 100%; overflow-x: auto; padding: 16px 18px; background: #f4f6f9; border: 1px solid var(--line); line-height: 1.5; }}
    pre code {{ border: 0; padding: 0; background: transparent; overflow-wrap: normal; }}
    .architecture-figure {{ margin: 32px 0 38px; padding: 20px; border: 1px solid var(--line-strong); background: #fff; overflow: hidden; }}
    .figure-scroll {{ max-width: 100%; overflow-x: auto; }}
    .architecture-figure img {{ display: block; width: 100%; height: auto; }}
    .architecture-figure figcaption {{ margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--line); color: var(--muted); font-size: .86rem; }}
    .document-end {{ margin-top: 72px; padding: 24px 0; border-top: 1px solid var(--line); color: var(--muted); font-size: .82rem; }}
    @media (max-width: 940px) {{
      .layout {{ display: block; padding: 0 22px 70px; }}
      aside {{ display: none; }}
      .site-header {{ padding: 0 22px; }}
      .header-meta {{ max-width: 120px; text-align: right; line-height: 1.2; }}
      .architecture-figure {{ margin-left: -22px; margin-right: -22px; padding: 16px 22px; border-left: 0; border-right: 0; }}
      .figure-scroll img {{ min-width: 820px; }}
      .table-scroll, pre {{ max-width: calc(100vw - 44px); }}
    }}
    @media print {{
      .site-header, aside {{ display: none; }}
      .layout {{ display: block; max-width: none; padding: 0; }}
      h2 {{ break-before: page; }}
      .architecture-figure {{ break-inside: avoid; }}
      a {{ color: inherit; text-decoration: none; }}
    }}
  </style>
</head>
<body>
  <header class="site-header">
    <a class="product" href="architecture.md">Evidence-Based Development Harness</a>
    <div class="header-meta">Architecture guide and deep-dive map</div>
  </header>
  <div class="layout">
    <aside aria-label="Document table of contents">
      <div class="toc-heading">On this page</div>
      <nav class="toc">{toc}</nav>
    </aside>
    <main>
      {body}
      <div class="document-end">Generated from the architecture source documents by <code>scripts/render_architecture.py</code>.</div>
    </main>
  </div>
</body>
</html>
"""


def main() -> None:
    markdown_text = build_markdown()
    FULL_MARKDOWN.write_text(markdown_text, encoding="utf-8")
    FULL_HTML.write_text(render_html(markdown_text), encoding="utf-8")
    print(f"wrote {FULL_MARKDOWN} ({len(markdown_text.splitlines())} lines)")
    print(f"wrote {FULL_HTML} ({FULL_HTML.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
