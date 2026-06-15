"""Text cleanup for chart labels."""

from __future__ import annotations

import re

_HTML_TAG = re.compile(r"<[^>]+>")


def clean_chart_label(text: str) -> str:
    s = _HTML_TAG.sub("", str(text or ""))
    s = s.replace("&nbsp;", " ").strip()
    return s
