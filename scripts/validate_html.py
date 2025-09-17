#!/usr/bin/env python3
"""Simple HTML structure validator for project pages.

The script performs lightweight checks tailored to prevent regressions that
have previously occurred in this repository:
- Ensures <section> elements live inside the <body> element.
- Ensures the closing </html> tag is the final content in the file.
- Ensures CSS declarations such as "body {" are not left outside of <style>
  blocks.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable


HTML_GLOB = "*.html"


def collect_html_files(base: Path) -> Iterable[Path]:
    for path in sorted(base.glob(HTML_GLOB)):
        if path.is_file():
            yield path


def check_sections_inside_body(content: str) -> list[str]:
    lower = content.lower()
    errors: list[str] = []
    body_open = lower.find("<body")
    body_close = lower.find("</body>")

    if body_open == -1 or body_close == -1:
        errors.append("<body> タグが正しく配置されていません。")
        return errors

    first_section = lower.find("<section")
    last_section = lower.rfind("</section")

    if first_section != -1 and first_section < body_open:
        errors.append("<section> が <body> の外にあります (先頭)。")
    if last_section != -1 and last_section > body_close:
        errors.append("<section> が <body> の外にあります (末尾)。")

    return errors


STYLE_BLOCK_PATTERN = re.compile(r"<style[\s\S]*?</style>", re.IGNORECASE)
CSS_SELECTOR_PATTERN = re.compile(r"\b(?:html|body|h[1-6]|section)[^{]{0,40}\{")


def check_orphan_css(content: str) -> list[str]:
    stripped = STYLE_BLOCK_PATTERN.sub("", content)
    if CSS_SELECTOR_PATTERN.search(stripped):
        return ["<style> タグの外に CSS が記述されています。"]
    return []


def check_trailing_content(content: str) -> list[str]:
    lower = content.lower()
    html_end = lower.rfind("</html>")
    if html_end == -1:
        return ["</html> タグが見つかりません。"]
    trailing = content[html_end + len("</html>"):]
    if trailing.strip():
        return ["</html> タグの後に不要なコンテンツがあります。"]
    return []


CHECKS = (
    check_sections_inside_body,
    check_orphan_css,
    check_trailing_content,
)


def validate_file(path: Path) -> list[str]:
    content = path.read_text(encoding="utf-8")
    errors: list[str] = []
    for check in CHECKS:
        errors.extend(check(content))
    return errors


def main() -> int:
    base = Path(__file__).resolve().parent.parent
    has_error = False

    for html_file in collect_html_files(base):
        errors = validate_file(html_file)
        if errors:
            has_error = True
            print(f"[NG] {html_file.name}")
            for message in errors:
                print(f"  - {message}")
        else:
            print(f"[OK] {html_file.name}")

    return 1 if has_error else 0


if __name__ == "__main__":
    sys.exit(main())
