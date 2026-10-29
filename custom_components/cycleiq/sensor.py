"""Sensor platform for CycleIQ."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import ALGORITHM_VERSION, DOMAIN
from .predictor import AppliancePredictor

@dataclass(frozen=True, kw_only=True)
class CycleIQSensorDescription(SensorEntityDescription):
    pass

SENSORS = (
    CycleIQSensorDescription(key="remaining_time",translation_key="remaining_time",icon="mdi:timer-sand",device_class=SensorDeviceClass.DURATION,native_unit_of_measurement=UnitOfTime.MINUTES,state_class=SensorStateClass.MEASUREMENT),
    CycleIQSensorDescription(key="expected_end",translation_key="expected_end",icon="mdi:clock-end",device_class=SensorDeviceClass.TIMESTAMP),
    CycleIQSensorDescription(key="expected_duration",translation_key="expected_duration",icon="mdi:timeline-clock-outline",device_class=SensorDeviceClass.DURATION,native_unit_of_measurement=UnitOfTime.MINUTES,state_class=SensorStateClass.MEASUREMENT),
    CycleIQSensorDescription(key="confidence",translation_key="confidence",icon="mdi:percent-circle-outline",native_unit_of_measurement=PERCENTAGE,state_class=SensorStateClass.MEASUREMENT),
    CycleIQSensorDescription(key="cycle_profile",translation_key="cycle_profile",icon="mdi:shape-outline"),
    CycleIQSensorDescription(key="learned_cycles",translation_key="learned_cycles",icon="mdi:brain"),
    CycleIQSensorDescription(key="last_start",translation_key="last_start",icon="mdi:clock-start",device_class=SensorDeviceClass.TIMESTAMP),
    CycleIQSensorDescription(key="last_end",translation_key="last_end",icon="mdi:clock-end",device_class=SensorDeviceClass.TIMESTAMP),
    CycleIQSensorDescription(key="last_duration",translation_key="last_duration",icon="mdi:timer-outline",device_class=SensorDeviceClass.DURATION,native_unit_of_measurement=UnitOfTime.MINUTES,state_class=SensorStateClass.MEASUREMENT),
    CycleIQSensorDescription(key="last_energy",translation_key="last_energy",icon="mdi:lightning-bolt",device_class=SensorDeviceClass.ENERGY,native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR),
)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    runtime: AppliancePredictor = entry.runtime_data
    async_add_entities(CycleIQSensor(runtime, entry, description) for description in SENSORS)

class CycleIQSensor(SensorEntity):
    _attr_has_entity_name = True
    def __init__(self, runtime: AppliancePredictor, entry: ConfigEntry, description: CycleIQSensorDescription) -> None:
        self.runtime, self.entry, self.entity_description = runtime, entry, description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": runtime.name, "manufacturer": "CycleIQ", "model": f"Learning predictor ({runtime.appliance_type})"}
        self._remove_listener = None
    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._remove_listener = self.runtime.add_listener(self._handle_update)
    async def async_will_remove_from_hass(self) -> None:
        if self._remove_listener is not None:
            self._remove_listener(); self._remove_listener = None
        await super().async_will_remove_from_hass()
    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
    @property
    def native_value(self) -> Any:
        return self.runtime.values.get(self.entity_description.key)
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"algorithm_version": ALGORITHM_VERSION,"cycleiq_key": self.entity_description.key,"cycleiq_entry_id": self.entry.entry_id,"detection_mode": self.runtime.mode,"active_cycle": self.runtime.active,"source_power_entity": self.runtime.power_entity,"source_energy_entity": self.runtime.energy_entity,"prediction_log": str(self.runtime.csv_log.path),"max_learning_cycles": self.runtime.max_cycles}
