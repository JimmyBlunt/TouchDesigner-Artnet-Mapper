# Sender audit, 2026-09-12

Scope: independent source audit and offline tests only. This agent made no
TouchDesigner bridge calls, network sends, or controller changes. Live tests and
receiver measurements are coordinated separately by the root agent.

## Findings

1. A target of 30 FPS permits 33.33 ms per frame. The previous sender waits
   between all 29 universes: 28 requested sleeps of 1 ms. Sleep requests are not
   exact scheduling deadlines. Even their nominal 28 ms leaves only 5.33 ms for
   cooking, packing, UDP sends and other TD work. The stored previous native
   evidence measured approximately 64–66 ms total sending and 11–12 ms packing
   at the 5 FPS setting (`../controller-replacement-248-20260911/steady-live-verification.json`).
   CPU-side timing cannot explain or guarantee receiver completion, but this
   particular synchronous 1 ms configuration cannot sustain 30 FPS as measured.

2. The effective live path includes `SPARSE_SOURCE_MASK_V1`, not merely the
   original builder string. With missing/retired ranges present,
   `output_slot_mask.channels` reads each TD channel's `.vals` and masks Python
   lists. The current rear-panel packer therefore already avoids a native TD
   channel lookup per RGB component. It packs 2,983 mapped slots from the 6,524
   source slots into 29 exact 510-byte payloads. Holes, missing pixels and
   unmapped output 6 remain zero.

3. `_compiled_router` avoids recompiling unchanged routing, but serializes the
   configuration table signature for each due frame. Controller selection also
   reads its table each TD tick. This is bounded by the small number of routing
   rows and should be measured separately before adding cache invalidation
   complexity. A stale routing cache would be a correctness regression.

4. `pack_ms` starts after `source.cook(force=False)`, so it excludes source graph
   evaluation. `send_ms` surrounds both cooking and packing plus network waits.
   `actual_send_fps` is local scheduling telemetry, not received/complete FPS.
   At multiple controller rates, its aggregate event count is also not an
   individual controller's rate. Native tests should distinguish all of these.

5. The previous implementation's `max(0, min(255, int(round(...))))` adds three
   redundant builtin calls per component. Since the argument to `round` is a
   Python float and no `ndigits` is given, its result is already a builtin
   integer. Replacing these calls with integer comparisons preserves ties-to-even,
   conversion, overflow and nonfinite exceptions. Clamping before rounding
   would change exception behavior and was intentionally not done.

## Implemented pure packer optimization

`pixelblaze_mapper/realtime_packer.py` now clips the rounded integer using two
comparisons. Existing accepted value types and validation stay unchanged.

The reproducible benchmark
`tools/benchmark_rear_panel_packer_20260912.py` alternates old/new order over seven
80-frame repeats for the actual five-panel topology. It checks every payload
against the validated reference packer before timing. No network access occurs.

| Brightness | Previous median | Optimized median | Reduction |
| --- | ---: | ---: | ---: |
| 20% | 3.629 ms | 1.898 ms | 47.7% |
| 70% | 3.525 ms | 1.732 ms | 50.9% |

Raw repeat times and environment are in `packer-benchmark.json`. These are
offline Python-tuple measurements, not a claim that LED output doubled.
The change saves approximately 1.7–1.8 ms in this benchmark; receiver and
packet-spacing bottlenecks still require separate work.

Validation: **21 tests passed**, using Python 3.12.13:

```
python -m unittest tests.test_realtime_packer_fastpath tests.test_realtime_packer tests.test_generated_sender_runtime tests.test_sender_packet_gap tests.test_sender_pacing
```

Coverage includes halfway neighbors, clipping, signed zero, random data,
bool/numeric subclasses/Fraction/NumPy scalar fallback, NaN/infinity/overflow
exception parity, reference byte equality, generated send-loop timing and
per-controller pacing. The new production-topology test also checks 29
510-byte universes, black U138, black U142–U148 and representative missing LEDs.

## Recommended native measurements and remaining work

- Verify module `__file__` before installation. The root agent found a local
  shadow checkout ahead of this repository on the running TD import path.
  Editing this repository does not by itself replace the cached native module.
- Reload the optimized module only while the sender is stopped, then invalidate
  the compiled packer cache so native instances use the new implementation.
- Measure source cook, table signature, mask/snapshot, pack and send separately
  if packing remains a significant fraction of the frame budget.
- `source.numpyArray()` should be considered only as a measured alternative to
  the existing three `.vals` snapshots. Array shape/dtype, ownership and byte
  rounding need native verification. Merely passing NumPy scalar sequences to
  the current converter introduces numeric ABC checks and is not a demonstrated
  improvement. A future vectorized gather/scatter packer needs float64
  multiplication and exact clipping/rounding parity tests to avoid byte changes.
- Reduce or remove per-packet main-thread sleeps only after bounded receiver
  experiments identify a reliable packet schedule. An external sender isolates
  TD timing, but its local FPS is still not proof of receiver frame completion.
- Preserve missing-slot masking, controller-specific destinations and scan/output
  exclusion in any alternate sender. Do not silently omit configured output 6
  universes: its black frames may be required for receiver frame assembly.

Whether additional controllers improve throughput must be decided from receiver
output timing, per-port LED lengths and firmware scheduling; this sender audit
does not infer a controller pixel limit from the 5 FPS preview alone.
