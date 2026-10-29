# CycleIQ

CycleIQ is a learning predictor and companion extension for [sionetta's Washing Machine Animated Card](https://github.com/sionetta/wm_animated_ha_card). It does **not** replace or modify the original card.

## What stays in sionetta's card
Animation, appliance UI, status/power display, themes/languages, normal last-cycle fields and the official `remaining_entity` support remain owned by the original card.

## What CycleIQ adds
- local cycle learning and persistent history;
- remaining-time, expected-end and expected-duration prediction;
- confidence and learned program profiles;
- dedicated 30–45 minute dryer follow-up profile (shown as **Kort ±35 min** on Dutch HA);
- profile-specific bias correction and prediction stabilization;
- automatic CSV training logs under `/config/cycleiq/logs/`;
- last start/end/duration/energy sensors;
- Cycle Active binary sensor and reset-learning button;
- the in-card row **START | EXPECTED | REMAINING | END | DURATION**;
- automatic registration of the CycleIQ frontend module.

## HACS installation
1. Install/update **Washing Machine Animated Card** by sionetta through HACS.
2. Add this repository to HACS as category **Integration** while it is still a custom repository.
3. Download CycleIQ and restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration → CycleIQ**.
5. Add one entry per appliance and select its power + cumulative energy sensor. Choose automatic power detection or an existing reliable status entity.

A fresh CycleIQ install requires **no Pyscript file**, **no manually created log folder**, and **no manual JavaScript resource**.

## Migrating existing predictor learning data

If you already used the earlier Pyscript predictor, CycleIQ can import its persisted cycle history once during setup.

In the optional **Existing learning-data entity** field select the entity whose attributes contain the `cycles` list, for example:

```text
pyscript.wasmachine_leerdata
pyscript.droger_leerdata
```

CycleIQ sanitizes the imported history, keeps at most 40 valid cycles, normalizes 30–45 minute dryer cycles into the dedicated short profile, and then stores the result in its own Home Assistant storage. After the import, CycleIQ no longer depends on the legacy entity.

Existing CSV files are left untouched as historical archives. New CycleIQ prediction/evaluation rows are written to `/config/cycleiq/logs/`.

## Card connection
CycleIQ entities include metadata linking them to the configured power sensor. The frontend extension uses that metadata to fill missing CycleIQ-related entity options in a matching Washing Machine Animated Card automatically. Explicit YAML settings always win.

Example:

```yaml
type: custom:washing-machine-card
appliance_type: dryer
status_entity: binary_sensor.droger_cycle_active
power_entity: sensor.droger_power
plug_entity: switch.droger
language: nl
```

The exact entity IDs depend on the name selected during setup.

## CSV logbook
CycleIQ creates one append-only file per appliance:

```text
/config/cycleiq/logs/<name>_<entry-id>_prediction_log.csv
```

It contains start, prediction, finish and evaluation rows. Evaluation rows record the real remaining time and the prediction error so learning quality can be reviewed later. Logging errors never stop the predictor.

## Dryer short cycles
For dryers, completed cycles between **30 and 45 minutes** are normalized into one dedicated short profile. During a new run CycleIQ compares short and long historical candidates separately. A short cycle soon after a long cycle is an extra signal, but timing alone does not force the classification. If short/long evidence is ambiguous, confidence is deliberately capped instead of showing an unrealistically high percentage.

## Compatibility and fail-safe behavior
Initial target: Washing Machine Animated Card **v1.5.0**.

CycleIQ patches the already-loaded card only when compatible internals are present. If they are not, CycleIQ logs a warning and leaves the original card untouched.

## Development status
Version 0.2.0 is the first native HACS-integration architecture. Test this branch before replacing the current 0.1.0 development plugin installation.

## License
MIT.
