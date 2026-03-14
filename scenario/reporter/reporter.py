from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

# ============================================================
# Internal rendering models
# ------------------------------------------------------------
# We convert raw dicts into structured objects that are easier
# for the template to consume.
# ============================================================

@dataclass
class RenderLine:
    """
    Represents one visible terminal line in the log table.
    """
    text: str
    anno: bool = False
    anno_kind: str = ""
    anno_name: str = ""


@dataclass
class RenderTest:
    """
    Represents one test case block in the report.
    """
    id: str
    name: str
    description: str
    passed: bool
    feedback_text: str
    lines: list[RenderLine]


# ============================================================
# MAIN METHOD
# ============================================================

def reporter_generate_html(
    tests_data: list[dict[str, Any]],
    *,
    format_type: str = "default",
    css_href: str = "style.css",
    page_title: str = "Report",
    title_text: str = "תוצאות הבדיקה",
    subtitle_text: str = "",
    section_title: str = "פירוט תרחישי הבדיקה",
    footer_text: str = "לחץ על כל תרחיש כדי לראות פרטים נוספים",
) -> str:

    def _strip_newlines(s: str) -> str:
        return s.replace("\r", "").replace("\n", "")

    def _quote_kind(q: dict[str, Any]) -> str:
        t = q.get("type")
        if isinstance(t, dict):
            return str(t.get("en", ""))
        if isinstance(t, str):
            return t
        return ""

    def _quote_kind_he(q: dict[str, Any]) -> str:
        t = q.get("type")
        if isinstance(t, dict):
            return str(t.get("he", ""))
        return ""

    # ------------------------------------------------------------
    # Core transformation:
    # Convert raw log quotes into visible terminal lines.
    #
    # Important behavior:
    # printing + input/output are merged into one visible line.
    # ------------------------------------------------------------
    def _merge_quotes_to_lines(quotes: list[dict[str, Any]]) -> list[RenderLine]:

        lines: list[RenderLine] = []
        i = 0

        while i < len(quotes):
            q = quotes[i]
            kind = _quote_kind(q)
            value = _strip_newlines(str(q.get("value", "")))

            # Merge printing + next input/output
            if kind == "printing" and (i + 1) < len(quotes):
                next_q = quotes[i + 1]
                next_kind = _quote_kind(next_q)

                if next_kind in ("input", "output"):
                    merged_text = (
                        _strip_newlines(str(q.get("value", ""))) +
                        _strip_newlines(str(next_q.get("value", "")))
                    ).strip()

                    lines.append(
                        RenderLine(
                            text=merged_text,
                            anno=True,
                            anno_kind=_quote_kind_he(next_q),
                            anno_name=str(next_q.get("name", "")),
                        )
                    )

                    i += 2
                    continue

            # Standalone input/output
            if kind in ("input", "output"):
                lines.append(
                    RenderLine(
                        text=value.strip(),
                        anno=True,
                        anno_kind=_quote_kind_he(q),
                        anno_name=str(q.get("name", "")),
                    )
                )
                i += 1
                continue

            # Standalone printing
            if kind == "printing":
                lines.append(RenderLine(text=value))
                i += 1
                continue

            # Fallback
            lines.append(RenderLine(text=value))
            i += 1

        return lines

    render_tests: list[RenderTest] = []

    # Unittest
    if tests_data and "method_signature" in tests_data[0]:
        for t in tests_data:
            test_id = str(t.get("id", "unknown"))
            name = str(t.get("name", ""))
            description = str(t.get("description", ""))
            passed = bool((t.get("result") or {}).get("bool", False))
            
            if passed:
                feedback_text = ""
            else:
                feedback_text = str(((t.get("feedback") or {}).get("error")) or "")

            one_line = []
            one_line.append(RenderLine(
                            text=((t.get("log") or {}).get("text")) or [],
                            anno=False,
                            anno_kind="",
                            anno_name="",
                        ))

            render_tests.append(
                RenderTest(
                    id=test_id,
                    name=name,
                    description=description,
                    passed=passed,
                    feedback_text=feedback_text,
                    lines=one_line,
                )
            )
    # Scenario
    else:
        for t in tests_data:
            test_id = str(t.get("id", "unknown"))
            name = str(t.get("name", ""))
            description = str(t.get("description", ""))
            passed = bool((t.get("result") or {}).get("bool", False))
            feedback_text = str(((t.get("feedback") or {}).get("text")) or "")

            quotes = ((t.get("log") or {}).get("quotes")) or []

            render_tests.append(
                RenderTest(
                    id=test_id,
                    name=name,
                    description=description,
                    passed=passed,
                    feedback_text=feedback_text,
                    lines=_merge_quotes_to_lines(quotes),
                )
            )

    # ============================================================
    # Compute summary statistics (for the gauge)
    # ============================================================

    total = len(render_tests)
    passed_count = sum(1 for t in render_tests if t.passed)

    score_percent = int(round((passed_count / total) * 100)) if total else 0

    # SVG gauge uses "stroke-dashoffset" where 0 = 100% filled
    gauge_dashoffset = max(0, min(100, 100 - score_percent))

    if score_percent == 100:
      gauge_color = "#10B981"   # green
    elif score_percent == 0:
      gauge_color = "#EF4444"   # red
    else:
      gauge_color = "#FFC400"   # yellow


    # ============================================================
    # Render using Jinja2
    # ============================================================

    # Build Jinja environment
    templates_dir = Path(__file__).parent / "templates"

    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    if format_type == "vpl":
        template = env.get_template("vpl_report.html.j2")
    else:
        template = env.get_template("report.html.j2")

    html = template.render(
        page_title=page_title,
        css_href=css_href,
        title_text=title_text,
        subtitle_text=subtitle_text,
        section_title=section_title,
        footer_text=footer_text,
        tests=render_tests,
        total=total,
        passed=passed_count,
        score_percent=score_percent,
        gauge_color=gauge_color,
        gauge_dashoffset=gauge_dashoffset,
    )

    return score_percent, html
