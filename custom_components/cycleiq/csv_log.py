"""CSV training log for CycleIQ."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import slugify

_LOGGER = logging.getLogger(__name__)

FIELDS = [
    "timestamp",
    "event",
    "machine",
    "cycle_id",
    "elapsed_min",
    "power_w",
    "energy_kwh",
    "predicted_end",
    "predicted_remaining_min",
    "predicted_total_duration_min",
    "confidence_pct",
    "profile",
    "actual_end",
    "actual_duration_min",
    "actual_energy_kwh",
    "actual_remaining_min",
    "error_actual_minus_predicted_min",
    "algorithm_version",
]


class CycleIQCsvLog:
    """Append-only per-appliance CSV training log."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, name: str) -> None:
        self.hass = hass
        safe_name = slugify(name) or "appliance"
        self.path = Path(
            hass.config.path(
                "cycleiq",
                "logs",
                f"{safe_name}_{entry.entry_id[:8]}_prediction_log.csv",
            )
        )

    def schedule(self, row: dict[str, Any]) -> None:
        """Schedule a non-blocking append."""
        self.hass.async_create_task(self.async_append(row))

    async def async_append(self, row: dict[str, Any]) -> None:
        """Write one row outside the event loop; logging must never stop prediction."""
        try:
            await self.hass.async_add_executor_job(self._append_sync, row)
        except (OSError, ValueError, csv.Error) as err:
            _LOGGER.warning("CycleIQ prediction log could not be written: %s", err)

    def _append_sync(self, row: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        needs_header = not self.path.exists() or self.path.stat().st_size == 0
        with self.path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=FIELDS,
                extrasaction="ignore",
            )
            if needs_header:
                writer.writeheader()
            writer.writerow({field: row.get(field, "") for field in FIELDS})
