"""Install a Windows-safe snapshot of the official MadMapper material source.

The upstream repository currently contains a LaserMaterials path with a
trailing space, which makes a normal Git checkout fail on Windows.  This
module downloads the repository archive but extracts only the regular
``Materials`` and shared ``Libraries`` trees plus their documentation.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile
import urllib.request

from pixelblaze_mapper.madmapper_td_adapter import adapt_material
from pixelblaze_mapper.material_library import (
    Compatibility,
    MaterialCatalog,
    build_catalog,
    write_catalog,
)


OFFICIAL_REPOSITORY = "https://github.com/madmappersoftware/MadMapper-Materials"
DEFAULT_REF = "d7ff211281f1878feeccd8ead05ce855c0eac5ee"
ARCHIVE_URL = OFFICIAL_REPOSITORY + "/archive/{ref}.tar.gz"
ALLOWED_ROOTS = frozenset({"Materials", "Libraries"})
ALLOWED_FILES = frozenset({"README.md", "MaterialsDoc.md", "LICENSE"})


def _safe_ref(ref: str) -> str:
    value = "".join(character for character in ref if character.isalnum() or character in "-_.")
    if not value or value in {".", ".."}:
        raise ValueError("invalid source ref")
    return value


def _selected_relative_path(member_name: str) -> PurePosixPath | None:
    parts = PurePosixPath(member_name).parts
    if len(parts) < 2:
        return None
    relative = PurePosixPath(*parts[1:])
    if any(part in {"", ".", ".."} for part in relative.parts):
        return None
    if relative.parts[0] in ALLOWED_ROOTS or relative.as_posix() in ALLOWED_FILES:
        return relative
    return None


def extract_regular_materials(archive: str | Path, destination: str | Path) -> dict[str, int]:
    """Safely extract the regular material subset from a GitHub tar archive."""
    target_root = Path(destination).resolve()
    target_root.mkdir(parents=True, exist_ok=True)
    files = 0
    bytes_written = 0
    with tarfile.open(archive, mode="r:*") as bundle:
        for member in bundle:
            relative = _selected_relative_path(member.name)
            if relative is None or member.isdir():
                continue
            if not member.isfile() or member.issym() or member.islnk():
                continue
            target = (target_root / Path(*relative.parts)).resolve()
            if target_root not in target.parents:
                raise ValueError("archive member escapes destination")
            source = bundle.extractfile(member)
            if source is None:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                raise FileExistsError("source snapshot is immutable: %s" % target)
            with source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
            files += 1
            bytes_written += member.size
    if not (target_root / "Materials").is_dir():
        raise ValueError("archive did not contain a Materials tree")
    return {"files": files, "bytes": bytes_written}


def sync_official_source(
    source_parent: str | Path,
    *,
    ref: str = DEFAULT_REF,
    archive_path: str | Path | None = None,
) -> Path:
    """Create or reuse one immutable, ref-addressed official source snapshot."""
    safe_ref = _safe_ref(ref)
    parent = Path(source_parent).resolve()
    destination = parent / ("madmapper-materials-" + safe_ref[:12])
    manifest = destination / "source-snapshot.json"
    if manifest.is_file():
        data = json.loads(manifest.read_text(encoding="utf-8"))
        if data.get("ref") != ref or data.get("repository") != OFFICIAL_REPOSITORY:
            raise ValueError("existing snapshot manifest does not match requested source")
        return destination
    if destination.exists():
        raise FileExistsError("unmanaged source destination already exists: %s" % destination)

    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="madmapper-download-", dir=str(parent)) as temporary:
        archive = Path(archive_path).resolve() if archive_path else Path(temporary) / "source.tar.gz"
        if archive_path is None:
            request = urllib.request.Request(
                ARCHIVE_URL.format(ref=ref),
                headers={"User-Agent": "TouchDesigner-Artnet-Mapper/1.0"},
            )
            with urllib.request.urlopen(request, timeout=60) as response, archive.open("wb") as output:
                shutil.copyfileobj(response, output)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        staging = Path(temporary) / "staging"
        counts = extract_regular_materials(archive, staging)
        snapshot = {
            "schema_version": 1,
            "repository": OFFICIAL_REPOSITORY,
            "ref": ref,
            "archive_sha256": digest,
            "scope": ["Materials", "Libraries", "README.md", "MaterialsDoc.md", "LICENSE"],
            "excluded": ["LaserMaterials (different rendering contract; Windows-incompatible upstream path)"],
            **counts,
        }
        (staging / "source-snapshot.json").write_text(
            json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        staging.replace(destination)
    return destination


def apply_touchdesigner_compatibility(
    catalog: MaterialCatalog, library_roots: tuple[str | Path, ...]
) -> MaterialCatalog:
    """Replace generic ISF status with the conservative TD adapter result."""
    records = []
    for record in catalog.materials:
        result = adapt_material(record.source_path, library_roots=library_roots)
        if result.adaptable:
            reasons = (
                "automatic TouchDesigner wrapper available; live compile is still required",
                *result.warnings,
            )
            records.append(replace(
                record,
                compatibility=Compatibility.ADAPTABLE,
                compatibility_reasons=tuple(dict.fromkeys(reasons)),
            ))
        else:
            records.append(replace(
                record,
                compatibility=Compatibility.UNSUPPORTED,
                compatibility_reasons=result.reasons or ("manual TouchDesigner port required",),
            ))
    return MaterialCatalog(
        source_id=catalog.source_id,
        source_label=catalog.source_label,
        source_root=catalog.source_root,
        materials=tuple(records),
    )


def build_official_catalog(source_root: str | Path, catalog_path: str | Path) -> Path:
    snapshot = Path(source_root)
    catalog = build_catalog(
        snapshot / "Materials",
        source_id="madmapper-official",
        source_label="MadMapper Official Materials",
    )
    catalog = apply_touchdesigner_compatibility(catalog, (snapshot, snapshot / "Libraries"))
    return write_catalog(catalog, catalog_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install and index official MadMapper materials")
    parser.add_argument("--source-parent", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--ref", default=DEFAULT_REF)
    parser.add_argument("--archive", type=Path, help="Use a local GitHub tar archive instead of downloading")
    args = parser.parse_args(argv)
    source = sync_official_source(args.source_parent, ref=args.ref, archive_path=args.archive)
    catalog = build_official_catalog(source, args.catalog)
    print(json.dumps({"source": str(source), "catalog": str(catalog)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
