# Controller 251: receiver contract versus actual sender

Read-only source review, 2026-10-18. No firmware, serial-port, controller configuration or live-output changes were made for this review.

## Source identity and limits

Repository: JimmyBlunt/ArtNet-Controller-ESP-Teensy41. The historical [OTA verification](https://github.com/JimmyBlunt/ArtNet-Controller-ESP-Teensy41/blob/6d021ba401a7b3482e3d42d69b5011844daa8933/reports/esp-artnet-rx-20261002/final-verification.json) records source `4049b602cf9b8a04321a2ddeb6d26c4cd7b20758`, environment `esp32-wifi-esp251`, and flashed SHA-256 `e4fbdbdecf9649a3d635f499be9fca4abd1d3658df0237e4ccaab6acbd1e6b7b` on 2026-10-02 Sydney time. Branch head `6d021ba401a7b3482e3d42d69b5011844daa8933` adds reports/screenshots only: comparison against `4049b60` contains no firmware source changes. Parser, assembler, output configuration and scheduling therefore match between these two commits.

This is a historical deployment record, **not proof of today's installed binary**. The current API has no build hash, uptime or reset reason. The historical [acceptance report](https://github.com/JimmyBlunt/ArtNet-Controller-ESP-Teensy41/blob/6d021ba401a7b3482e3d42d69b5011844daa8933/reports/esp-artnet-rx-20261002/README.md) explicitly failed performance acceptance: 99.0663% reception in its 30-second run and 97.3845% in its final 10-second smoke test, with extra traffic present. Those results are not current measurements or a controlled before/after comparison.

The historical esp32-wifi-esp251 environment extends esp32-wifi-flex8 and defines LED_PROFILE_WIFI/LED_PROFILE_FLEX8; its NetworkManager selects the WiFi backend. This describes that recorded build only. The user's current physical network connection and today's deployed backend remain unconfirmed; a reported network LED alone does not establish Ethernet or WiFi. References to wireless loss below are conditional possibilities, not identification of the live transport.

## ArtDMX bytes

Receiver implementation: [ArtNetReceiver.cpp lines 13–25](https://github.com/JimmyBlunt/ArtNet-Controller-ESP-Teensy41/blob/4049b602cf9b8a04321a2ddeb6d26c4cd7b20758/firmware/esp32_artnet/firmware/src/ArtNetReceiver.cpp#L13). Destination UDP port is [6454](https://github.com/JimmyBlunt/ArtNet-Controller-ESP-Teensy41/blob/4049b602cf9b8a04321a2ddeb6d26c4cd7b20758/firmware/esp32_artnet/firmware/include/ArtNetReceiver.h#L11), bound to all local interfaces. No sender hostname, source-IP, source-port or physical-port filtering exists in this parser. `flex8-ws2812-apa102` is a compiled hardware profile, not an Art-Net hostname or packet field.

| Offset | Receiver contract | Current TD packet captured at sendto |
|---|---|---|
| 0–7 | Exact ASCII `Art-Net` plus NUL | `41 72 74 2d 4e 65 74 00` |
| 8–9 | Little-endian opcode `0x5000` | `00 50` |
| 10–11 | Parser does not validate protocol revision | `00 0e` = revision 14 |
| 12 | Sequence; zero disables sequence rejection | `00` |
| 13 | Physical byte ignored by parser | `00` |
| 14–15 | Little-endian wire universe; config uses zero-based addresses | `9c 00` through `a2 00` = U156–162 |
| 16–17 | Big-endian payload length, even, 2–512 bytes | `01 fe` = 510 |
| 18 onward | At least declared payload bytes must exist | 510 RGB-channel bytes; total UDP payload 528 bytes |

Both 510 and 512 channel bytes are accepted. Composition uses only complete RGB triples in channels 0–509; the last two bytes of a 512-byte payload are ignored. Short even payloads are accepted and still count as a received universe, but missing pixels then remain black. Actual TD payloads are full 510 bytes. The raw receive queue rejects datagrams larger than 530 bytes. No 512-byte padding is necessary.

The current runtime sendto capture supplied by the coordinating diagnostic recorded seven packets to `10.0.0.251:6454`, local `10.0.0.125:6454`, U156–162, protocol 14, sequence 0, physical 0, payload 510, packet gaps 1.42–1.76 ms, total frame span 9.97 ms. This is an application send observation, **not a NIC/WLAN delivery capture**. The serializer in `pixelblaze_mapper/build_multi_controller_output.py:611` produces this header; `realtime_packer.py:57` initializes each payload to 510 zero bytes before mapped writes.

## Port mapping and padding

FLEX8 builds the receive set from each enabled output's own startUniverse, pixelCount and startPixel, not the global status startUniverse. Noncontiguous universes are supported. See [UniverseAssembler.cpp lines 20–38](https://github.com/JimmyBlunt/ArtNet-Controller-ESP-Teensy41/blob/4049b602cf9b8a04321a2ddeb6d26c4cd7b20758/firmware/esp32_artnet/firmware/src/UniverseAssembler.cpp#L20). Global `/api/status.startUniverse=0` therefore does not mean the configured inputs should be U0–6.

| Physical output | Hardware logical pixels | Pins data/clock | Expected universes and used pixels | TD universe-aligned destination |
|---|---|---|---|---|
| 0, 299 APA102 | 0–298 | 16/17 | U156:170; U157:129 | 0–298 |
| 1, 357 APA102 | 299–655 | 25/26 | U158:170; U159:170; U160:17 | 340–696 |
| 2, 196 APA102 | 656–851 | 13/14 | U161:170; U162:26 | 850–1045 |

Hardware readback: `docs/panel8-rescan-299-20261018/controller-readback.json` from the repository root. The latest runtime sender audit has 299, 357 and **195 mapped** pixels; output 2's last configured pixel remains intentionally black in the zero-filled 196th slot. That still supplies a complete seven-universe frame.

The tail padding in U157, U160 and U162 is excluded by each route's pixelCount. The receiver compacts the three outputs into 852 logical pixels; the sender reserves 1190 transport slots (7 × 170). These are different coordinate spaces and the gaps are expected. Every configured output is below the FLEX8 allocation/validation limit of 1200 CRGB pixels per pin pair; no 299-specific overflow was found. See [LedOutputs.cpp](https://github.com/JimmyBlunt/ArtNet-Controller-ESP-Teensy41/blob/4049b602cf9b8a04321a2ddeb6d26c4cd7b20758/firmware/esp32_artnet/firmware/src/LedOutputs.cpp#L20).

## Sequence, boundaries and output timing

Sequence handling is **per universe**, not a global packet counter or globally enforced frame ID. Nonzero sequence compares to that universe's previous nonzero sequence, modulo 255; distance 0 or >127 is rejected when the previous packet was less than two seconds ago. Sequence 0 bypasses this. Sharing an advancing sequence across all universes in a frame is not inherently rejected by this source because each universe has its own previous sequence. The older sender comment describing reuse incompatibility must not be treated as this source's algorithm. No sender change is needed: current sequence 0 is explicitly accepted. [Assembler lines 62–73](https://github.com/JimmyBlunt/ArtNet-Controller-ESP-Teensy41/blob/4049b602cf9b8a04321a2ddeb6d26c4cd7b20758/firmware/esp32_artnet/firmware/src/UniverseAssembler.cpp#L62).

There is no special U156 frame-start marker. A repeated universe before all seven are collected discards the existing group, increments framesIncomplete and starts a new group with that packet. Timeout is 100 ms from the group's **first** accepted packet, not its last. Timeout discards, rather than outputs, the incomplete group. ArtSync is unsupported: the parser accepts only opcode 0x5000, so an ArtSync packet cannot commit a frame. [Assembler lines 74–122](https://github.com/JimmyBlunt/ArtNet-Controller-ESP-Teensy41/blob/4049b602cf9b8a04321a2ddeb6d26c4cd7b20758/firmware/esp32_artnet/firmware/src/UniverseAssembler.cpp#L74), [default timeout](https://github.com/JimmyBlunt/ArtNet-Controller-ESP-Teensy41/blob/4049b602cf9b8a04321a2ddeb6d26c4cd7b20758/firmware/esp32_artnet/firmware/include/UniverseAssembler.h#L25).

There is no delayed-compose race between consecutive queued packets: after **each** pop/accept the loop immediately checks frameReady and composes; the separate RX task only writes the FIFO. Incomplete frames are not passed to LED output. Multiple complete groups drained in one loop may replace one pending output, so framesComplete can exceed outputFrames. A complete group can nevertheless mix sender frames when arrival order crosses frame boundaries because sequence 0 and this assembler provide no frame identity. [main.cpp lines 251–282](https://github.com/JimmyBlunt/ArtNet-Controller-ESP-Teensy41/blob/4049b602cf9b8a04321a2ddeb6d26c4cd7b20758/firmware/esp32_artnet/firmware/src/main.cpp#L251).

Consequently `rxPackets=202*7` alone does not prove 202 complete ordered sets, and `framesComplete + framesIncomplete` is not a sender-frame identity check. rxPackets includes datagrams before parsing and is sampled separately from assembler counters; pending/queued packets and packet order matter. A strictly ordered stream of 202 full seven-packet sets with no expiry/discard produces 202 complete groups, not sporadic incomplete groups.

## RGB versus BGR: current combination is coherent

The assembler initially treats each received triple as R,G,B. `colorForFixedDriver` then computes the requested **wire byte order** and inversely adjusts CRGB storage to compensate for the fixed FastLED APA102 `<BGR>` driver. Thus firmware `colorOrder=RGB` preserves the received byte order on the LED wire; it does not undo a sender-side BGR transform. [LedColorOrder.h lines 11–25](https://github.com/JimmyBlunt/ArtNet-Controller-ESP-Teensy41/blob/4049b602cf9b8a04321a2ddeb6d26c4cd7b20758/firmware/esp32_artnet/firmware/include/LedColorOrder.h#L11).

Current TD BGR + firmware RGB produces physical BGR relative to the original TD RGB, consistent with APA102's BGR serialization. Example: original TD red `(255,0,0)` → UDP `(0,0,255)` → firmware CRGB `(255,0,0)` → FastLED BGR wire `(0,0,255)`. TD RGB + firmware BGR would be equivalent. Setting both to BGR would double-swap red and blue. No color-order correction is justified by the apparent differing labels; visual physical calibration remains the final color check.

## Remaining receive loss and supported diagnostic controls

RX runs on core 0, priority 2, 4096-byte stack, blocking socket timeout 20 ms, then a 64-datagram static FIFO. LED output and assembler run in the loop task. SO_RCVBUF is requested only if compiled into lwIP and does not enlarge the SDK's compiled UDP mailbox. rxPackets increments immediately on queue push, before parser/universe checks. Therefore fewer rxPackets than sent, with zero queue/oversize/socket errors, locates missing datagrams before application queueing (or before transmission at the sender), not in the LED mapping. It does not distinguish WLAN/AP loss from the lwIP mailbox. [Receiver](https://github.com/JimmyBlunt/ArtNet-Controller-ESP-Teensy41/blob/4049b602cf9b8a04321a2ddeb6d26c4cd7b20758/firmware/esp32_artnet/firmware/src/ArtNetReceiver.cpp#L29), [queue counters](https://github.com/JimmyBlunt/ArtNet-Controller-ESP-Teensy41/blob/4049b602cf9b8a04321a2ddeb6d26c4cd7b20758/firmware/esp32_artnet/firmware/include/ArtNetRxQueue.h#L33).

Current independent black-frame evidence: `controller251-new-supply-standalone-black10.json` has 299×7=2093 sent, 2083 received, 289 complete, 10 incomplete; the subsequent no-HTTP-during-stream `controller251-new-supply-standalone-quiet-black10.json` has 2093 sent, 2088 received, 294 complete, 5 incomplete. Both retained heapMinFree=84176 with zero timeout/queue/socket errors. Distinguish these two runs. Black payload still clocks every LED and therefore does not eliminate output CPU work.

APA templates are fixed at 4 MHz and runtime validation requires spiHz==4000000. The checked build does not enable FASTLED_ALL_PINS_HARDWARE_SPI; FastLED 3.10.3 defaults to software SPI without that macro. The examined APA/bitbang path does not explicitly disable interrupts for an entire frame; no global-interrupt-stall diagnosis is established. [Runtime validation](https://github.com/JimmyBlunt/ArtNet-Controller-ESP-Teensy41/blob/4049b602cf9b8a04321a2ddeb6d26c4cd7b20758/firmware/esp32_artnet/firmware/src/ConfigManager.cpp#L188), [FastLED selection](https://github.com/FastLED/FastLED/blob/3.10.3/src/fastspi.h), [bitbang implementation](https://github.com/FastLED/FastLED/blob/3.10.3/src/fastspi_bitbang.h).

There is no runtime API knob for RX queue size, socket mailbox, receiver priority or assembler timeout. targetFps 1–60 is supported and controls output rate only. A temporary lower targetFps at unchanged 10-fps ingress could isolate output contention, with fewer physical updates by design; configuration must be restored afterwards. This was not performed by this review. A NIC packet capture with exact universe/order/timing, compared to receiver deltas after the sender stops and the queue drains, is the next non-firmware diagnostic. It can establish sender delivery to the NIC, but cannot alone distinguish subsequent WLAN loss from receiver-stack loss. Increasing receiver task priority is not an established fix: the historical priority-17 experiment was inconclusive and reverted.
