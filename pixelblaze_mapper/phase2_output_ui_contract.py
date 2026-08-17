"""Phase 2 OUTPUT(DMX) UI contract.

This module deliberately contains no DMX allocator implementation.  It defines
the state exchanged between TouchDesigner and the pure Python allocator owned
by the mapper I/O layer.  Production DMX nodes are outside this contract.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Mapping, Protocol


CONTRACT_VERSION = "td.pixelblaze.output-config/v1"
ALLOCATOR_MODULE_CANDIDATES = (
    "pixelblaze_mapper.dmx_config",
    "pixelblaze_mapper.dmx_allocator",
    "pixelblaze_mapper.dmx_config",
    "pixelblaze_mapper",
)


@dataclass(frozen=True)
class OutputDraft:
    pixel_count: int = 3714
    pixel_format: str = "rgb"
    channel_order: str = "GRB"
    auto_allocate: bool = True
    start_universe: int = 0
    start_channel: int = 1
    protocol: str = "artnet_unicast"
    target_address: str = "10.0.0.244"
    local_address: str = "10.0.0.173"
    port: int = 6454
    rate: int = 30
    priority: int = 100
    art_sync: bool = True


@dataclass(frozen=True)
class UniverseRow:
    channel: str
    logical: int
    net: int
    subnet: int
    universe: int
    pixel_start: int
    pixel_count: int
    dmx_start: int
    dmx_end: int
    state: str


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    code: str
    message: str
    field: str = ""


@dataclass(frozen=True)
class AllocationResult:
    pixel_count: int
    channels_required: int
    universe_count: int
    last_universe_pixels: int
    capacity_pixels: int
    rows: tuple[UniverseRow, ...] = field(default_factory=tuple)
    issues: tuple[ValidationIssue, ...] = field(default_factory=tuple)

    @property
    def blocked(self) -> bool:
        return any(item.severity.lower() == "blocked" for item in self.issues)


class AllocatorProtocol(Protocol):
    def __call__(self, config: Mapping[str, Any]) -> Any: ...


def draft_payload(draft: OutputDraft) -> dict[str, Any]:
    """Return the stable dictionary handed to the shared allocator."""

    payload = asdict(draft)
    payload["contract"] = CONTRACT_VERSION
    return payload


def find_shared_allocator() -> tuple[Callable[[Mapping[str, Any]], Any] | None, str]:
    """Discover, but never replace, the mapper I/O agent's allocator.

    The canonical implementation is ``dmx_config.build_plan(DmxConfig(...))``.
    The returned adapter accepts the stable UI dictionary and constructs the
    canonical config. Until this is importable the UI remains a read-only
    baseline mockup and Review/Apply stays disabled.
    """

    import importlib

    for module_name in ALLOCATOR_MODULE_CANDIDATES:
        try:
            module = importlib.import_module(module_name)
        except (ImportError, ModuleNotFoundError):
            continue
        build_plan = getattr(module, "build_plan", None)
        config_type = getattr(module, "DmxConfig", None)
        if callable(build_plan) and config_type is not None:
            def adapter(config: Mapping[str, Any], _build=build_plan, _type=config_type):
                canonical = _type(
                    pixel_count=int(config["pixel_count"]),
                    source_order=str(config.get("source_order", "RGB")).upper(),
                    output_order=str(config.get("channel_order", "GRB")).upper(),
                    start_universe=int(config.get("start_universe", 0)),
                    start_channel=int(config.get("start_channel", 1)),
                    payload_slots=int(config.get("payload_slots", 510)),
                    target_address=str(config.get("target_address", "10.0.0.244")),
                    local_address=str(config.get("local_address", "10.0.0.173")),
                    port=int(config.get("port", 6454)),
                )
                return _build(canonical)
            return adapter, f"{module_name}.build_plan"
    return None, "allocator pending"


def build_with_shared_allocator(draft: OutputDraft) -> tuple[AllocationResult | None, str]:
    """Build a normalized UI result using only the shared canonical allocator."""

    allocator, status = find_shared_allocator()
    if allocator is None:
        return None, status
    plan = allocator(draft_payload(draft))
    config = plan.config
    rows = tuple(
        UniverseRow(
            channel=universe.channel,
            logical=universe.sequence,
            net=universe.address.net,
            subnet=universe.address.subnet,
            universe=universe.address.universe,
            pixel_start=universe.start_pixel,
            pixel_count=universe.pixel_count,
            dmx_start=universe.start_channel,
            dmx_end=universe.start_channel + universe.active_slots - 1,
            state="DRAFT",
        )
        for universe in plan.universes
    )
    capacity = sum(
        (config.payload_slots - universe.leading_padding) // config.channels_per_pixel
        for universe in plan.universes
    )
    return AllocationResult(
        pixel_count=config.pixel_count,
        channels_required=plan.flat_sample_count,
        universe_count=plan.universe_count,
        last_universe_pixels=plan.last_pixel_count,
        capacity_pixels=capacity,
        rows=rows,
        issues=(),
    ), status


def baseline_live_rows() -> tuple[UniverseRow, ...]:
    """Return the verified read-only 3714/22 snapshot for initial UI display.

    This is not used to allocate imported maps.  It only mirrors the known live
    production state while the shared allocator adapter is unavailable.
    """

    rows: list[UniverseRow] = []
    for logical in range(22):
        count = 170 if logical < 21 else 144
        rows.append(
            UniverseRow(
                channel=f"Universe{logical}",
                logical=logical,
                net=logical // 256,
                subnet=(logical // 16) % 16,
                universe=logical % 16,
                pixel_start=logical * 170,
                pixel_count=count,
                dmx_start=1,
                dmx_end=count * 3,
                state="LIVE",
            )
        )
    return tuple(rows)


PUBLIC_PARAMETERS: tuple[tuple[str, str, str], ...] = (
    ("Enabled", "toggle", "Draft output enabled; never exported directly to production"),
    ("Pixelcount", "int", "Pixel slots from selected mapper draft"),
    ("Pixelformat", "menu", "rgb in Phase 2"),
    ("Channelorder", "menu", "RGB channel permutation"),
    ("Autoallocate", "toggle", "Use shared allocator"),
    ("Startuniverse", "int", "Logical Art-Net Port-Address"),
    ("Startchannel", "int", "One-based DMX slot"),
    ("Protocol", "menu", "artnet_unicast or artnet_broadcast"),
    ("Targetaddress", "str", "Art-Net destination"),
    ("Localaddress", "str", "Local NIC address"),
    ("Port", "int", "UDP port"),
    ("Rate", "int", "Frames per second"),
    ("Priority", "int", "Output priority"),
    ("Artsync", "toggle", "Send ArtSync"),
    ("Universesrequired", "int", "Allocator result"),
    ("Lastuniversepixels", "int", "Allocator result"),
    ("Draftstate", "str", "MATCHES LIVE / MODIFIED / BLOCKED"),
    ("Validationstate", "str", "OK / WARNING / BLOCKED"),
    ("Allocatorstatus", "str", "Shared allocator binding state"),
    ("Revertdraft", "pulse", "Restore draft from live snapshot"),
    ("Reviewapply", "pulse", "Integration-owned and disabled in Phase 2 UI"),
)
