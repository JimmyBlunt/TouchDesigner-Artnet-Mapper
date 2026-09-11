# Optional external packet worker

`pixelblaze_mapper/external_packet_sender.py` isolates paced UDP sending from the
TouchDesigner main thread. It does not generate or repeat animation frames.
The native producer remains responsible for mapping, masking and frame rate.

```
sender = ExternalPacketSender(
    python_executable, local_address, target_address,
    target_port=6454, local_port=6454, gap_ms=2.0)
sender.submit([(artdmx_bytes, (target_address, 6454)), ...])
sender.status()
sender.close()
```

Each instance supports one explicit target and one local binding. The Python
executable must be a real standalone interpreter, not TouchDesigner.exe.
The subprocess is hidden on Windows. Readiness is bounded at two seconds;
startup failure kills the worker before any submission can occur.

Submission uses an authenticated localhost UDP envelope capped at 60,000 bytes.
Every packet must contain exactly 510 ArtDMX payload bytes, universes must be
unique within the batch, and targets must match the configured endpoint.
`submit` validates synchronously, then queues without waiting for physical UDP
transmission. It returns false on a busy local socket and raises on malformed
data or a dead worker. This is not acknowledgement of receiver delivery.

After each paced batch, the worker drains queued frames and selects the newest
one. `stale_batches` counts superseded valid submissions. Queue draining is
bounded to prevent producer starvation of the send loop. There is no catch-up
replay and no autonomous resend of unchanged source data.

Packet gaps use `perf_counter` deadlines: longer waits sleep until about one
millisecond remains, while the final <=2 ms uses a short busy wait in the
isolated worker. This avoids relying on Windows millisecond sleep precision.
The tradeoff is CPU use in one worker process during packet spacing. Each
packet receives a fresh wait; an OS scheduling stall never causes compensating
short gaps. Batch durations and FPS intervals also use `perf_counter`.

Before the first valid batch, a bounded five-second startup grace allows TD to
return from its start callback and reach its first frame tick. No LED packets
are sent during this grace. If it expires, the process exits with
`startup_watchdog`. Once the first valid batch arrives, the watchdog immediately
changes to one second and never returns to the longer startup grace.

If no further valid batch arrives for one second, the worker sends black payloads for
all universes in the last accepted frames, twice, and exits. Explicit `close`
uses the same cleanup, waits at most approximately two seconds, and reports
`forced_termination` if graceful shutdown failed. Blackout counters acknowledge
only local UDP sends; only controller telemetry can establish actual receipt.
No submitted frames means no touched universes and no physical blackout sends.

The worker writes status at most once per half-second during transmission and
once on exit. Stats include accepted/sent/stale/rejected batches, sent/blackout
packet counts, timing and errors. `actual_send_fps` is an EMA of intervals
between completed batch starts in the worker; `active_seconds` measures the
first-to-last completed batch-start span and `active_average_fps` divides
the number of completed intervals by that span. Blackout sends are excluded.
These rates describe physical UDP send calls, not TD enqueue rate or confirmed
controller frame completion. Atomic file replacement retries briefly on
Windows because concurrent status reads can temporarily deny replacement.
Temporary configuration, authentication token and status files are removed on
close; the final status stays cached in the Python object.
Cleanup errors are reported separately as `cleanup_errors`. A failed stop-marker
write cannot bypass IPC closing or bounded worker wait/kill. Temporary cleanup
failures and surviving processes allow another `close()` attempt while new
submissions remain blocked. Failed initial config-file writes are cleaned up too.

Validation: fourteen tests in `tests/test_external_packet_sender.py` use
localhost endpoints and ephemeral ports. They cover exact bytes and two black
frames on close, idle-watchdog cleanup, stale-frame collapse, nonblocking
submission, endpoint constraints, packet shape, authentication, empty/duplicate
universes and the IPC size limit. Two startup regressions verify that a first TD
tick delayed by 1.2 seconds works, subsequent idle still blackens after one
second, and startup without any data exits after the bounded five-second grace
without sending any LED packets. No test sends to a physical LED controller.
A deterministic clock test checks that packet waits never return early and
only the coarse portion uses sleep.
A bounded-queue regression verifies that the 129th datagram remains queued
after processing 128 batches. Worker status also reports configured `gap_ms`.
Failure-injection tests cover stop-marker errors, retryable temporary cleanup,
and constructor config-write failure without a leftover temporary directory.

Native opt-in installation, save/restore behavior, scan exclusion and receiver
performance testing are separate integration work. This module alone makes no
claim of 30 FPS or guaranteed controller delivery.
