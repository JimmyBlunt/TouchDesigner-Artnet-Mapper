import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

from pixelblaze_mapper.sync_madmapper_library import (
    build_official_catalog,
    extract_regular_materials,
    sync_official_source,
)


def _archive(path: Path) -> None:
    members = {
        "MadMapper-Materials-ref/Materials/Factory/Test/Test.fs": b"/*{}*/\nvec4 materialColorForPixel(vec2 uv){return vec4(uv,0,1);}",
        "MadMapper-Materials-ref/Materials/Factory/Test/thumbnail.png": b"PNG",
        "MadMapper-Materials-ref/Libraries/MadCommon.glsl": b"float luma(vec3 c){return c.r;}",
        "MadMapper-Materials-ref/README.md": b"readme",
        "MadMapper-Materials-ref/LaserMaterials/Bad Path /.info": b"must not extract",
    }
    with tarfile.open(path, "w:gz") as bundle:
        for name, value in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(value)
            bundle.addfile(info, io.BytesIO(value))


class SourceSyncTests(unittest.TestCase):
    def test_extract_filters_laser_tree_and_keeps_regular_materials(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "source.tar.gz"
            _archive(archive)
            result = extract_regular_materials(archive, root / "out")
            self.assertEqual(4, result["files"])
            self.assertTrue((root / "out/Materials/Factory/Test/Test.fs").is_file())
            self.assertTrue((root / "out/Libraries/MadCommon.glsl").is_file())
            self.assertFalse((root / "out/LaserMaterials").exists())

    def test_sync_is_immutable_and_idempotent_for_same_ref(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "source.tar.gz"
            _archive(archive)
            first = sync_official_source(root / "sources", ref="abc123", archive_path=archive)
            second = sync_official_source(root / "sources", ref="abc123", archive_path=archive)
            self.assertEqual(first, second)
            manifest = json.loads((first / "source-snapshot.json").read_text(encoding="utf-8"))
            self.assertEqual("abc123", manifest["ref"])
            self.assertEqual(4, manifest["files"])

    def test_official_catalog_contains_td_adapter_compatibility(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "source.tar.gz"
            _archive(archive)
            source = sync_official_source(root / "sources", ref="abc123", archive_path=archive)
            catalog_path = build_official_catalog(source, root / "catalog.json")
            data = json.loads(catalog_path.read_text(encoding="utf-8"))
            self.assertEqual(1, len(data["materials"]))
            self.assertEqual("adaptable", data["materials"][0]["compatibility"])
            self.assertIn("automatic TouchDesigner wrapper available", data["materials"][0]["compatibility_reasons"][0])

    def test_existing_unmanaged_destination_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "source.tar.gz"
            _archive(archive)
            unmanaged = root / "sources/madmapper-materials-abc123"
            unmanaged.mkdir(parents=True)
            with self.assertRaises(FileExistsError):
                sync_official_source(root / "sources", ref="abc123", archive_path=archive)


if __name__ == "__main__":
    unittest.main()
