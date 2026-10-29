"""Frontend registration for CycleIQ."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components import lovelace
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
    lovelace_data = hass.data.get(lovelace.LOVELACE_DATA)

    if lovelace_data is not None:
        resources = lovelace_data.resources

        if (
            isinstance(resources, lovelace.resources.ResourceStorageCollection)
            and resources.store is not None
        ):
            if not resources.loaded:
                await resources.async_load()
                resources.loaded = True

            namespace = f"{FRONTEND_URL}/"
            for item in resources.async_items():
                item_url = item.get("url", "")
                if item_url.startswith(namespace):
                    if item_url != url:
                        await resources.async_update_item(item["id"], {"url": url})
                        _LOGGER.info(
                            "CycleIQ Lovelace resource updated: %s -> %s",
                            item_url,
                            url,
                        )
                    _REGISTERED = True
                    return

            await resources.async_create_item(
                {"res_type": "module", "url": url}
            )
            _LOGGER.info("CycleIQ Lovelace resource registered automatically: %s", url)
            _REGISTERED = True
            return

    # YAML resource mode is read-only from integrations. Keep an automatic
    # fallback so CycleIQ can still load without copying files manually.
    add_extra_js_url(hass, url)
    _LOGGER.warning(
        "CycleIQ could not use Lovelace resource storage (likely YAML resource mode). "
        "Loaded as an extra frontend module instead: %s",
        url,
    )
    _REGISTERED = True
