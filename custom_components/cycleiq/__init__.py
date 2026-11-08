"""CycleIQ integration."""

from __future__ import annotations

import logging

from homeassistant.components import lovelace
from homeassistant.components.frontend import remove_extra_js_url
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .predictor import AppliancePredictor

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]

_LOGGER = logging.getLogger(__name__)

# CycleIQ <= 0.3.x bundled a frontend module that patched private internals of
# sionetta's card. CycleIQ 0.4+ is backend-only. These constants exist solely
# to clean up that legacy resource during migration.
_LEGACY_FRONTEND_PREFIX = "/cycleiq/frontend/"
_LEGACY_EXTRA_JS_URLS = (
    "/cycleiq/frontend/cycleiq-washing-machine-card-extension.js?v=0.2.1",
    "/cycleiq/frontend/cycleiq-washing-machine-card-extension.js?v=0.3.0",
)


async def _async_remove_legacy_frontend(hass: HomeAssistant) -> None:
    """Remove the old CycleIQ card patch resource from pre-0.4 installations."""
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

            for item in list(resources.async_items()):
                item_url = str(item.get("url", ""))
                if item_url.startswith(_LEGACY_FRONTEND_PREFIX):
                    await resources.async_delete_item(item["id"])
                    _LOGGER.info(
                        "Removed legacy CycleIQ Lovelace frontend resource: %s",
                        item_url,
                    )

    # CycleIQ <= 0.3.x used add_extra_js_url as a fallback in YAML-resource
    # mode. Removing known legacy URLs is harmless when they were never added.
    for url in _LEGACY_EXTRA_JS_URLS:
        remove_extra_js_url(hass, url)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the backend-only CycleIQ integration."""
    hass.data.setdefault(DOMAIN, {})
    await _async_remove_legacy_frontend(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one CycleIQ appliance."""
    runtime = AppliancePredictor(hass, entry)
    await runtime.async_start()
    entry.runtime_data = runtime
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = runtime
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload one CycleIQ appliance."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_stop()
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unloaded


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload CycleIQ after options change."""
    await hass.config_entries.async_reload(entry.entry_id)
