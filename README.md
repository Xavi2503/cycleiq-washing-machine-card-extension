# CycleIQ

CycleIQ is a native Home Assistant learning and prediction integration for appliances such as washing machines and dryers.

CycleIQ is **backend-only**. It does not replace, patch, inject into, or depend on private internals of any dashboard card.

It works especially well with [sionetta's Washing Machine Animated Card](https://github.com/sionetta/wm_animated_ha_card), but its entities are normal Home Assistant entities and can be used by any dashboard, automation, template or card.

## What CycleIQ does

- automatically follows appliance cycles;
- stores persistent learning history;
- configurable learning history limit per appliance (5–200 cycles, default 40);
- analyses power and cumulative energy patterns;
- predicts remaining time;
- predicts expected end time;
- predicts expected total duration;
- provides prediction confidence;
- learns separate cycle/program profiles;
- keeps the short 30–45 minute dryer cycle separate from longer dryer programs;
- learns prediction bias from completed cycles;
- stabilizes predictions to prevent unnecessary finish-time jumping;
- rejects invalid or unrealistic training cycles;
- creates automatic CSV training logs under `/config/cycleiq/logs/`;
- exposes last start, end, duration and energy;
- exposes a Cycle Active binary sensor;
- provides a Reset learned data button.

## Architecture

CycleIQ owns the **intelligence and data**.

Dashboard cards own the **presentation**.

That means CycleIQ only publishes standard Home Assistant entities such as:

- remaining time;
- expected end;
- expected duration;
- confidence;
- cycle profile;
- learned-cycle count;
- last start;
- last end;
- last duration;
- last energy;
- cycle active.

No CycleIQ JavaScript resource is required.

### Washing Machine Animated Card

The stock Washing Machine Animated Card already supports CycleIQ's remaining-time sensor through its generic `remaining_entity` option.

Example:

```yaml
type: custom:washing-machine-card
status_entity: binary_sensor.wasmachine_draait
power_entity: sensor.wasmachine_power
remaining_entity: sensor.wasmachine_resterende_tijd
```

For additional values such as expected end, confidence, profile, start/end and duration, CycleIQ intentionally waits for native generic entity-display support in the card rather than patching its DOM or private methods.

## HACS installation

1. Add this repository to HACS as category **Integration**.
2. Download CycleIQ.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration → CycleIQ**.
5. Add one entry per appliance.
6. Select the appliance power sensor and cumulative energy sensor.
7. Choose automatic power detection or an existing reliable status entity.

No Pyscript installation, manual Python copying, manual log directory or JavaScript resource is required.

## Upgrading from CycleIQ 0.3.x

CycleIQ 0.3.x bundled an experimental frontend extension for the Washing Machine Animated Card.

CycleIQ 0.4.0 removes that extension completely.

During startup, CycleIQ attempts to remove the old `/cycleiq/frontend/` Lovelace resource automatically. The predictor, persistent learning data, CSV logs and CycleIQ entities remain intact.

The old injected row:

`START | EXPECTED | REMAINING | END | DURATION`

is therefore no longer created by CycleIQ itself. Those values remain available as normal Home Assistant entities and can be displayed by native/generic card features.

## Migrating older predictor learning data

If you used the earlier Pyscript predictor, CycleIQ can import its persisted cycle history once during setup.

In **Existing learning-data entity (optional)** select the entity whose attributes contain the old `cycles` list, for example:

```text
pyscript.wasmachine_leerdata
pyscript.droger_leerdata
```

CycleIQ sanitizes imported history, keeps the newest valid cycles up to the configured limit, normalizes short dryer cycles into the dedicated short profile, and then stores the data in Home Assistant storage.

After import, CycleIQ no longer depends on the legacy entity.

## CSV logbook

CycleIQ creates one append-only CSV file per appliance:

```text
/config/cycleiq/logs/<name>_<entry-id>_prediction_log.csv
```

The log contains start, prediction, finish and evaluation rows. Evaluation rows compare previous predictions with the actual result so prediction quality can be reviewed and bias correction can improve future estimates.

Logging failures never stop the predictor.

## Short dryer cycles

For dryers, completed cycles between **30 and 45 minutes** are normalized into a dedicated short profile.

During a new run CycleIQ compares short and long historical candidates separately. A short follow-up cycle soon after a longer cycle is an additional signal, but timing alone never forces classification. If the evidence is ambiguous, confidence is deliberately limited.

## Version 0.4.0

Version 0.4.0 changes the integration boundary:

- removed the bundled card-patching JavaScript;
- removed DOM/private-method dependencies on Washing Machine Animated Card;
- removed automatic frontend resource registration;
- added migration cleanup for the legacy CycleIQ frontend resource;
- retained the complete learning/prediction backend and all Home Assistant entities.

This keeps CycleIQ independent from dashboard implementation details and lets cards consume its data through stable, generic Home Assistant entities.

## License

MIT.
