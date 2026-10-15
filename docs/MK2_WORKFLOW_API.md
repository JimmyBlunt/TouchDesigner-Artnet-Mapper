# MK2 workflow contract — 0.2.3

`pixelblaze_mapper.mk2_workflow.Controller` is the pure interaction layer. It never
opens USB devices, writes files, loads materials, changes TouchDesigner parameters,
or deletes automation. Adapters execute its returned commands on the main thread.
`tests/test_mk2_workflow.py` is the durable device-independent acceptance suite.

## Public interface and ordering

```python
controller = Controller(config=None, clock=time.monotonic)
controller.set_context(host.context())
commands = controller.dispatch(event)
# Execute each command, report failures, then refresh authoritative context.
commands = controller.tick()  # At least 10 Hz; handles 20-second editing timeout.
surface = controller.snapshot()
saved = controller.export_config()
```

Snapshots/configs are independent copies. `set_context` merges top-level fields;
supplied nested objects replace previous nested objects. Host state confirms mode,
active material, live parameters, playback and recording. An emitted runtime
command does not optimistically update these values. Refresh context between
successive encoder events so relative changes accumulate from confirmed values.

## Host context

| Field | Value |
| --- | --- |
| `mode` | `material` or `show`; STEP requests a latched change. |
| `active_material` | Descriptor of the Material Player's active material. |
| `catalog` | Ordered array of material descriptors; lightweight entries allowed. |
| `materials` | Optional `{material_id: full_descriptor}` for lazy pad editing. |
| `show` | Current clip object described below. |
| `recording` | `false`, `new_cue`, or `automation`. |
| `transitions` | Ordered supported transition identifiers. |
| `allow_automation_recording` | Defaults true after user confirmation. False disables REC+ERASE when host cannot safely record. |
| `config` | Optional authoritative saved v2 config; use only for actual external configuration updates, not every frame. |

A material descriptor contains `id`, `label`, `image` (approved image key),
`category`, `available` (optional bool), `compatibility` and `parameters`.
Unsupported or missing materials cannot load or receive new assignments.
The adapter hydrates a selected pad descriptor before editing or supplies it via
`materials` immediately afterward. Hydration itself does not activate materials.

Parameters are ordered records with `id`, `label`/`name`, `abbreviation`, `value`,
`min`, `max`, `step`, `type`, `section` (`td` or `native`), and `editable`.
`minimum`/`maximum` aliases are supported. Editable types are float/number,
int/integer, bool/boolean and enum (numeric index plus optional `options`). Unknown
types and nonfinite values remain displayed but cannot emit edits. First eight
parameters default to section TD; subsequent ones default native. The adapter
provides the requested eight common controls. Each page holds eight parameters;
up to eight pages are accessible. Overflow is explicitly reported for the UI.

`show` contains `id`, `material`, `parameters`, `playing`, `elapsed`, `duration`,
`transition`, `transition_duration`, `transition_progress`, `automated_ids`, and
`modified_ids`. The controller derives clamped progress and remaining time.
Show groups select eight-parameter blocks; pads 1–8 select individual parameters
for the large readout. Top buttons select parameter pages and restore overview.

## Normalized input events

All indices are zero-based. Physical pad 1 is index 0 (bottom-left); the hardware
adapter handles USB row ordering.

```json
{"type":"button","name":"top","index":0,"down":true}
{"type":"button","name":"top","index":0,"down":false}
{"type":"encoder","index":0,"delta":1}
{"type":"wheel","delta":-1}
{"type":"wheel_press"}
```

Buttons: `step`, `browse`, `scene`, `top` (0–7), `group` (0–7), `pad` (0–15),
`play`, `previous`, `next`, `restart`, `rec`, `erase`. `wheel` or `wheel_press`
button down events also work. Send releases; repeated down events are debounced.
An unchorded REC starts a new cue on release. REC+ERASE works in either press order
and starts only existing-clip automation recording, never an accidental new cue.
While recording, REC down stops. Mode/cue changes, other transport controls and
clip metadata editing are blocked during recording. Encoders are inert in normal Show Mode and active while
recording. REC+ERASE must replace only captured parameter curves and retain
untouched curves; the host owns that recording operation.

## Returned command objects

| `action` | Additional fields / adapter responsibility |
| --- | --- |
| `set_mode` | `mode`; apply player mode, then report actual mode. |
| `load_material` | `material_id`, `values`; load preset without changing show automatically. |
| `load_cue` | `cue_id`; compatibility for legacy cue pads. |
| `set_parameter` | `material_id`, `parameter_id`, `value`; apply/record safely. |
| `set_show_field` | `cue_id`, `field`, `value`; apply immediately, preserve host validations. |
| `transport` | `command`: play/previous/next/restart. |
| `record_start` | `kind`: new_cue/automation. |
| `record_stop` | Stop the current recording safely. |
| `flash_pad` | `group`, `index`, `color: red`; snapshot also holds timed flash state. |
| `persist_config` | `request_id`, complete `config`; write atomically and acknowledge. |

Configuration remains unchanged until a matching successful acknowledgement:

```json
{"type":"command_result","request_id":1,"success":true}
```

On disk failure use `success:false,error:"…"`. The previous config remains active
and the dialog permits retry. Old acknowledgements cannot commit a newer pending
write. Runtime failures can be reported with `command_result`, `success:false`
and `error` without a request ID. Never feed an uncommitted config back as host
state, since an explicit `set_context({config:…})` means an authoritative update.

## Persistence and modal editing

Schema 2 holds `hardware`, and eight `groups`, named A–H, each containing exactly
16 `pads`. A pad is `{kind:'material', target:'id', values:{parameter_id:value}}`.
Empty target means unassigned. Legacy schema `{hardware,pads:[16]}` migrates into
group A without losing saved cue assignments; groups B–H start empty. Saved
values must be finite numbers or booleans. Unknown future schema versions fail
validation instead of discarding assignments.

Since 0.2.3, the additive `favorites` field contains unique stable material IDs,
including `core:` IDs. Existing configurations default to an empty list. Missing
catalog entries retain their saved IDs so a temporary absence does not delete a
favorite. The browser shows only currently available catalog entries. Pad banks,
presets and the running material are independent of favorite membership.

In `browse`, top button indices 0/1 select `all`/`favorites`; index 7 toggles the
selected material's membership. All other top buttons are inert in this screen.
Wheel press still loads, or opens assignment confirmation for `browse_purpose=assign`.
Favorite toggles emit `persist_config` with `purpose='favorites'`; only a successful
acknowledgement updates membership. They keep the browser open and never load a
material. A failed write retains membership and permits retry. Removing the last
favorite leaves an empty list; pressing the wheel cannot load a hidden item.
Filtering is session-local; favorite membership survives application restarts.
`browse_catalog()` and `browse_selected_id()` expose the filtered selection for
host detail hydration. Catalog refreshes preserve selection by stable ID when possible.

SCENE opens `pad_grid`. Wheel selects one of 16 pads; press opens `pad_menu`.
Filled material pads expose select/edit/browse/delete; empty pads only browse.
Assignment browsing leads to `confirm_assign`, default Confirm, without loading.
Deletion also requires confirmation. Pad editing operates on a draft, never on
the active player. After exactly 20 seconds idle, a clean draft returns to the
grid; a changed draft shows Save/Cancel. Returning values to their initial values
counts as clean. Dirty navigation also asks Save/Cancel. An external mode change
preserves a dirty draft and displays Save/Cancel with a notice before returning to
the new mode. A concurrent pad reassignment cannot receive an older draft.
No saved values change
before the host acknowledges successful persistence.

## Display snapshot

The renderer receives `mode`, `screen` (`home`, `browse`, `pad_grid`, `pad_menu`,
`pad_edit`, `confirm_assign`, `confirm_delete`, `confirm_edit`), `material`,
`parameter_pages:[{label,parameters}]`, `page`, `bank`, `pad_index`, `cards`,
`browse_items`, `browse_index`, `browse_purpose`, `menu`/`options`, `choice`,
`confirm`, `show`, `recording`, `rec_pending`, `parameter_group`, `parameter_index`,
`parameter_focused`, `focused_parameter`, `parameter_overflow`, `group_activity`,
`group_has_content`, `pad_flash`, `dirty`, `saving`, and `error`.

`focused_parameter` stays null until a Show pad selects a parameter, so initial
screens show all eight values. Parameters carry `automated` and `modified` flags.
`group_activity` marks Show blocks; `group_has_content` marks Material pad banks.
`cards` are the active bank's 16 assignments with number, label, image and available.
Browse records include a one-based `number` plus zero-based `assignments` records
`{group,pad}`. A material can have multiple assignments. `confirm` holds kind,
label, group, pad, options and choice. `show.focus` is duration/transition/
transition_duration and `show.editing` marks wheel value entry. Display colors and
HID capabilities remain the hardware adapter's responsibility.

Favorite display fields: `browse_filter` (`all`/`favorites`), `favorites_count`
(all saved IDs, including temporarily unavailable ones), and `favorite` on every
`browse_items` entry. The entries and their numbering refer to the filtered list.
