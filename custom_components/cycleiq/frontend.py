"""Frontend registration for CycleIQ."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import FRONTEND_FILE, FRONTEND_URL, VERSION

_LOGGER = logging.getLogger(__name__)
_REGISTERED = False


async def async_register_frontend(hass: HomeAssistant) -> None:
    """Serve and register the bundled CycleIQ module automatically."""
    global _REGISTERED
    if _REGISTERED:
        return

    frontend_dir = Path(__file__).parent / "frontend"
    frontend_file = frontend_dir / FRONTEND_FILE
    if not frontend_file.exists():
        _LOGGER.warning("CycleIQ frontend file is missing: %s", frontend_file)
        return

    await hass.http.async_register_static_paths(
        [StaticPathConfig(FRONTEND_URL, str(frontend_dir), False)]
    )

    url = f"{FRONTEND_URL}/{FRONTEND_FILE}?v={VERSION}"
    add_extra_js_url(hass, url)

    _REGISTERED = True
    _LOGGER.info("CycleIQ frontend module registered automatically: %s", url)
