# CycleIQ

**Predictor Extension for Washing Machine Animated Card**

CycleIQ is an optional companion extension for
[sionetta/wm_animated_ha_card](https://github.com/sionetta/wm_animated_ha_card).

It does not replace the original card. Install and update the official
Washing Machine Animated Card normally through HACS. CycleIQ then adds the
predictor-specific cycle row inside that same card.

## Current layout

CycleIQ v0.1.0 adds:

**START | EXPECTED | REMAINING | END | DURATION**

The official card continues to handle the appliance UI, animation, power,
status and \`remaining_entity\`.

## Extra configuration

Add the predictor-specific entities to the normal
\`custom:washing-machine-card\` YAML:

\`\`\`yaml
type: custom:washing-machine-card
status_entity: input_boolean.washer_running
power_entity: sensor.washer_power

last_wash_entity: input_datetime.washer_last_start
last_end_entity: input_datetime.washer_last_end
duration_entity: input_number.washer_last_duration

remaining_entity: sensor.washer_remaining_time
expected_end_entity: sensor.washer_expected_end
\`\`\`

CycleIQ activates when \`expected_end_entity\` or \`last_end_entity\` is present.

## Compatibility

Initial target: Washing Machine Animated Card v1.5.0.

CycleIQ is fail-safe: if the expected card internals are not available, it
leaves the original card untouched.

## Status

v0.1.0 is the first development version and should be tested as a HACS custom
Dashboard repository before wider release.
