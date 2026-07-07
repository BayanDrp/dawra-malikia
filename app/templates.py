from __future__ import annotations

from functools import lru_cache

from jinja2 import Environment, FileSystemLoader
from jinja2.bccache import BytecodeCache

from app.config import settings

_env: Environment | None = None


class _MemoryBytecodeCache(BytecodeCache):
    def __init__(self):
        self._cache: dict[str, bytes] = {}

    def load_bytecode(self, bucket):
        key = bucket.key
        if key in self._cache:
            bucket.bytecode_from_string(self._cache[key])

    def dump_bytecode(self, bucket):
        self._cache[bucket.key] = bucket.bytecode_to_string()

    def clear(self):
        self._cache.clear()


def get_env() -> Environment:
    global _env
    if _env is None:
        _env = Environment(
            loader=FileSystemLoader("templates"),
            autoescape=True,
            bytecode_cache=_MemoryBytecodeCache(),
        )
        _env.globals.update(
            APP_NAME=settings.APP_NAME,
            APP_VERSION=settings.APP_VERSION,
            SITE_URL=settings.SITE_URL,
        )
    return _env


@lru_cache(maxsize=32)
def _get_template(template_name: str):
    return get_env().get_template(template_name)


def preload_templates():
    for name in ("landing.html", "login.html", "admin.html", "confirmation.html",
                 "forgot_password.html", "reset_password.html", "base.html"):
        _get_template(name)
    get_env().from_string("").render()


def render_template(template_name: str, **context) -> str:
    from fastapi.responses import HTMLResponse

    template = _get_template(template_name)
    html = template.render(**context)
    return HTMLResponse(html)
