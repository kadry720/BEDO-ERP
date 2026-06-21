from __future__ import annotations

import os
from collections.abc import Callable, Iterable
from typing import Any

from frappe.app import application as frappe_application


StartResponse = Callable[[str, list[tuple[str, str]], Any], Callable[[bytes], Any]]


def application(environ: dict[str, Any], start_response: StartResponse) -> Iterable[bytes]:
    site_name = (
        os.environ.get("BEDO_FRAPPE_SITE_HEADER")
        or os.environ.get("FRAPPE_SITE_NAME_HEADER")
        or os.environ.get("FRAPPE_SITE_NAME")
        or ""
    ).strip()
    if site_name:
        environ["HTTP_X_FRAPPE_SITE_NAME"] = site_name
    return frappe_application(environ, start_response)
