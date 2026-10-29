"""Binary sensor platform for CycleIQ."""
from __future__ import annotations
from typing import Any
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import ALGORITHM_VERSION, DOMAIN
from .predictor import AppliancePredictor

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    runtime: AppliancePredictor = entry.runtime_data
    async_add_entities([CycleActiveBinarySensor(runtime, entry)])

class CycleActiveBinarySensor(BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "cycle_active"
    _attr_icon = "mdi:progress-clock"
    def __init__(self, runtime: AppliancePredictor, entry: ConfigEntry) -> None:
        self.runtime, self.entry = runtime, entry
        self._attr_unique_id = f"{entry.entry_id}_cycle_active"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": runtime.name, "manufacturer": "CycleIQ", "model": f"Learning predictor ({runtime.appliance_type})"}
        self._remove_listener = None
    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass(); self._remove_listener = self.runtime.add_listener(self._handle_update)
    async def async_will_remove_from_hass(self) -> None:
        if self._remove_listener is not None: self._remove_listener(); self._remove_listener = None
        await super().async_will_remove_from_hass()
    @callback
    def _handle_update(self) -> None: self.async_write_ha_state()
    @property
    def is_on(self) -> bool: return self.runtime.active
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"algorithm_version": ALGORITHM_VERSION,"cycleiq_key":"cycle_active","cycleiq_entry_id":self.entry.entry_id,"source_power_entity":self.runtime.power_entity,"source_energy_entity":self.runtime.energy_entity}
