"""Frontend registration for CycleIQ."""
from __future__ import annotations
import logging
from pathlib import Path
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace import LOVELACE_DATA
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.core import HomeAssistant
from .const import FRONTEND_FILE, FRONTEND_URL, VERSION
_LOGGER = logging.getLogger(__name__)
_REGISTERED = False

async def async_register_frontend(hass: HomeAssistant) -> None:
    global _REGISTERED
    if _REGISTERED: return
    frontend_dir = Path(__file__).parent / "frontend"
    frontend_file = frontend_dir / FRONTEND_FILE
    if not frontend_file.exists():
        _LOGGER.warning("CycleIQ frontend file is missing: %s", frontend_file); return
    await hass.http.async_register_static_paths([StaticPathConfig(FRONTEND_URL, str(frontend_dir), False)])
    url_base = f"{FRONTEND_URL}/{FRONTEND_FILE}"
    url = f"{url_base}?v={VERSION}"
    lovelace = hass.data.get(LOVELACE_DATA)
    if lovelace is None:
        add_extra_js_url(hass, url); _REGISTERED = True; return
    resources = lovelace.resources
    if isinstance(resources, ResourceStorageCollection):
        await resources.async_get_info()
        existing = next((item for item in resources.async_items() if str(item.get("url","")).startswith(url_base)), None)
        if existing is None:
            await resources.async_create_item({"res_type":"module","url":url})
        elif existing.get("url") != url:
            await resources.async_update_item(existing["id"], {"res_type":"module","url":url})
    else:
        add_extra_js_url(hass, url)
    _REGISTERED = True
