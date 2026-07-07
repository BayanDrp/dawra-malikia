from __future__ import annotations

import html
import re


def h(text: str | None) -> str:
    if text is None:
        return ""
    return html.escape(str(text), quote=True)


def sanitize_user_agent(ua: str | None) -> str | None:
    if ua is None:
        return None
    cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", ua)
    return cleaned[:500]
