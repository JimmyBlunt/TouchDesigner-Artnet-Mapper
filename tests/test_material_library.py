import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pixelblaze_mapper.material_library import (
    Compatibility,
    MaterialCatalog,
    MaterialImportError,
    MaterialLibraryError,
    MaterialRecord,
    build_catalog,
    extract_isf_metadata,
    import_material,
    import_materials,
    load_catalog,
    search_catalog,
    write_catalog,
)


ISF_PARTICLES = '''/*{
  "ISFVSN": "2",
  "NAME": "Star Particles",
  "DESCRIPTION": "Noisy particle field with {braces} in text",
  "CATEGORIES": ["Generator", "Particles"],
  "INPUTS": [{"NAME": "particleSize", "TYPE": "float", "DEFAULT": 0.2}]
}*/
void main() { gl_FragColor = vec4(1.0); }
'''


class MaterialTree:
    def __init__(self, base: Path):
        self.root = base / "MadMapper-Materials"
        (self.root / "Factory" / "Noise").mkdir(parents=True)
        (self.root / "Factory" / "Particles").mkdir(parents=True)
        (self.root / "Helpers").mkdir(parents=True)
        (self.root / ".git").mkdir()
        (self.root / "Factory" / "Noise" / "fluid_noise.fs").write_text(
            "vec4 materialColorForPixel(vec2 uv) { return vec4(uv, 0., 1.); }",
            encoding="utf-8",
        )
        (self.root / "Factory" / "Noise" / "fluid_noise.png").write_bytes(b"preview")
        (self.root / "Factory" / "Noise" / "cellular.frag").write_text(
            "void mainImage(out vec4 c, in vec2 p) { c=vec4(p,0.,1.); }",
            encoding="utf-8",
        )
        (self.root / "Factory" / "Particles" / "star_particles.fs").write_text(
            ISF_PARTICLES, encoding="utf-8"
        )
        (self.root / "Factory" / "td_native.frag").write_text(
            "layout(location=0) out vec4 fragColor; void main(){fragColor=TDOutputSwizzle(vec4(1));}",
            encoding="utf-8",
        )
        (self.root / "Helpers" / "noise.glsl").write_text(
            "float noise(vec2 p) { return p.x; }", encoding="utf-8"
        )
        (self.root / "Helpers" / "only_vertex.vert").write_text(
            "void main(){gl_Position=vec4(0);}", encoding="utf-8"
        )
        (self.root / "Helpers" / "compute.comp").write_text(
            "void main(){}", encoding="utf-8"
        )
        (self.root / ".git" / "ignored.frag").write_text(
            "void main(){}", encoding="utf-8"
        )
        (self.root / "README.md").write_text("not a shader", encoding="utf-8")


class MetadataAndScanningTests(unittest.TestCase):
    def test_relaxed_header_comments_and_single_quotes_preserve_urls(self):
        source = '''/*{
            "DESCRIPTION": "https://example.org/material", // explanation
            "INPUTS": [{"NAME": "enabled", "TYPE": "bool", "DEFAULT": 'true'},],
            "CREDIT": "Author's material",
        }*/'''
        metadata = extract_isf_metadata(source)
        self.assertEqual('https://example.org/material', metadata['DESCRIPTION'])
        self.assertEqual("Author's material", metadata['CREDIT'])
        self.assertEqual('true', metadata['INPUTS'][0]['DEFAULT'])

    def test_isf_metadata_extraction_ignores_bad_comment_and_handles_nested_json(self):
        source = "/* {not-json} */\n" + ISF_PARTICLES
        metadata = extract_isf_metadata(source)
        self.assertEqual(metadata["NAME"], "Star Particles")
        self.assertEqual(metadata["INPUTS"][0]["NAME"], "particleSize")
        self.assertIn("{braces}", metadata["DESCRIPTION"])
        self.assertEqual(extract_isf_metadata("/* ordinary comment */ void main(){}"), {})

    def test_madmapper_trailing_commas_and_comma_separated_tags_are_supported(self):
        source = '''/*{
          "RESOURCE_TYPE": "Material For MadMapper",
          "TAGS": "line, geometry, audio",
          "INPUTS": [{"NAME": "gain", "TYPE": "float", "MAX": 360.,},],
        }*/
        vec4 materialColorForPixel(vec2 uv) { return vec4(uv, 0., 1.); }
        '''
        metadata = extract_isf_metadata(source)
        self.assertEqual(metadata["TAGS"], "line, geometry, audio")
        self.assertEqual(metadata["INPUTS"][0]["NAME"], "gain")
        self.assertEqual(metadata["INPUTS"][0]["MAX"], 360.0)

    def test_scans_known_types_only_and_classifies_compatibility(self):
        with tempfile.TemporaryDirectory() as temp:
            tree = MaterialTree(Path(temp))
            catalog = build_catalog(tree.root, source_id="official", source_label="Official")
            self.assertEqual(len(catalog.materials), 7)
            by_name = {item.name: item for item in catalog.materials}
            self.assertEqual(by_name["Td Native"].compatibility, Compatibility.NATIVE)
            self.assertEqual(by_name["Fluid Noise"].kind, "madmapper_glsl")
            self.assertEqual(by_name["Cellular"].kind, "shadertoy_glsl")
            self.assertEqual(by_name["Star Particles"].kind, "isf")
            self.assertEqual(by_name["Noise"].compatibility, Compatibility.UNSUPPORTED)
            self.assertEqual(by_name["Only Vertex"].kind, "vertex_glsl")
            self.assertEqual(by_name["Compute"].compatibility, Compatibility.UNSUPPORTED)
            self.assertTrue(by_name["Fluid Noise"].preview_path.endswith("fluid_noise.png"))
            self.assertIn("noise_texture", by_name["Fluid Noise"].groups)
            self.assertIn("particles", by_name["Star Particles"].groups)
            self.assertNotIn("ignored.frag", {item.relative_path for item in catalog.materials})

    def test_scan_order_and_ids_are_stable_across_checkout_locations(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            one = MaterialTree(Path(first))
            two = MaterialTree(Path(second))
            cat_one = build_catalog(one.root, source_id="official")
            cat_two = build_catalog(two.root, source_id="official")
            keys_one = [(m.name, m.relative_path, m.id) for m in cat_one.materials]
            keys_two = [(m.name, m.relative_path, m.id) for m in cat_two.materials]
            self.assertEqual(keys_one, keys_two)
            changed_source = build_catalog(two.root, source_id="fork")
            self.assertNotEqual(
                [m.id for m in cat_two.materials], [m.id for m in changed_source.materials]
            )

    def test_preview_symlink_escape_is_not_catalogued(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            tree = MaterialTree(base)
            outside = base / "outside.png"
            outside.write_bytes(b"outside")
            preview = tree.root / "Factory" / "Particles" / "star_particles.png"
            preview.write_bytes(b"link-placeholder")
            real_resolve = Path.resolve

            def resolve_as_escaping_link(path, strict=False):
                if path == preview:
                    return outside
                return real_resolve(path, strict=strict)

            # Simulate a link after is_file() without needing Windows symlink
            # privileges; production logic only trusts the resolved destination.
            with patch.object(Path, "resolve", resolve_as_escaping_link):
                particles = next(
                    m for m in build_catalog(tree.root).materials if m.name == "Star Particles"
                )
            self.assertIsNone(particles.preview_path)

    def test_oversized_source_is_catalogued_but_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "source"
            root.mkdir()
            # A sparse/truncated read is unnecessary here: patch the module limit
            # so the behavioral test remains fast and deterministic.
            path = root / "large.frag"
            path.write_text("void main(){}", encoding="utf-8")
            import pixelblaze_mapper.material_library as library
            old_limit = library.MAX_INSPECT_BYTES
            library.MAX_INSPECT_BYTES = 4
            try:
                item = build_catalog(root).materials[0]
            finally:
                library.MAX_INSPECT_BYTES = old_limit
            self.assertEqual(item.compatibility, Compatibility.UNSUPPORTED)
            self.assertIn("inspection limit", item.compatibility_reasons[0])

    def test_official_layout_indexes_only_fs_and_keeps_folder_as_one_package(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "official"
            material_dir = root / "Materials" / "Factory" / "Arcs"
            online_dir = root / "Materials" / "Online Library" / "Flow"
            library_dir = root / "Libraries"
            material_dir.mkdir(parents=True)
            online_dir.mkdir(parents=True)
            library_dir.mkdir()
            (material_dir / "Arcs.fs").write_text(
                "/*{\"TAGS\":\"line, geometry\",}*/\n#include \"Mad.glsl\"\n"
                "vec4 materialColorForPixel(vec2 p){return vec4(p,0,1);}", encoding="utf-8"
            )
            (material_dir / "Arcs.vs").write_text("void main(){}", encoding="utf-8")
            (material_dir / "Arcs.info").write_text("metadata", encoding="utf-8")
            (material_dir / "thumbnail.jpeg").write_bytes(b"jpeg")
            (online_dir / "Flow.fs").write_text(
                "vec4 materialColorForPixel(vec2 p){return vec4(p,0,1);}", encoding="utf-8"
            )
            (library_dir / "Mad.glsl").write_text("float helper(){return 1.;}", encoding="utf-8")
            catalog = build_catalog(root, source_id="official")
            self.assertEqual([item.name for item in catalog.materials], ["Arcs", "Flow"])
            arcs, flow = catalog.materials
            self.assertIn("factory", arcs.groups)
            self.assertIn("lines_geometry", arcs.groups)
            self.assertIn("online_library", flow.groups)
            self.assertNotIn("lines_geometry", flow.groups)  # "Online" must not imply "line".
            self.assertEqual(arcs.metadata["_COMPANION_TYPES"], [".info", ".jpeg", ".vs"])
            self.assertTrue(arcs.preview_path.endswith("thumbnail.jpeg"))
            self.assertTrue(any("vertex shader" in reason for reason in arcs.compatibility_reasons))
            imported = import_material(catalog, arcs.id, Path(temp) / "imports")
            self.assertTrue((imported.directory / "Arcs.vs").is_file())
            self.assertTrue((imported.directory / "Arcs.info").is_file())
            self.assertTrue((imported.directory / "thumbnail.jpeg").is_file())


class SearchAndPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.tree = MaterialTree(Path(self.temporary.name))
        self.catalog = build_catalog(self.tree.root, source_id="official")

    def tearDown(self):
        self.temporary.cleanup()

    def test_exact_and_typo_tolerant_search(self):
        self.assertEqual(search_catalog(self.catalog, "fluid")[0].name, "Fluid Noise")
        fuzzy = search_catalog(self.catalog, "particels")
        self.assertEqual([item.name for item in fuzzy], ["Star Particles"])
        self.assertEqual(search_catalog(self.catalog, "definitely absent"), ())

    def test_facet_filters_have_and_semantics_and_limit(self):
        items = search_catalog(
            self.catalog, groups="noise_texture", compatibility="adaptable"
        )
        self.assertEqual(
            {item.name for item in items}, {"Cellular", "Fluid Noise", "Star Particles"}
        )
        self.assertEqual(
            [item.name for item in search_catalog(self.catalog, tags=("noise", "fluid"))],
            ["Fluid Noise"],
        )
        self.assertEqual(len(search_catalog(self.catalog, limit=2)), 2)
        with self.assertRaisesRegex(MaterialLibraryError, "limit"):
            search_catalog(self.catalog, limit=-1)

    def test_facets_are_counts_and_json_round_trip_is_exact(self):
        facets = self.catalog.facets()
        self.assertGreaterEqual(facets["compatibility"]["adaptable"], 3)
        self.assertIn("noise_texture", facets["groups"])
        target = Path(self.temporary.name) / "nested" / "catalog.json"
        write_catalog(self.catalog, target)
        loaded = load_catalog(target)
        self.assertEqual(loaded, self.catalog)
        self.assertFalse(target.with_suffix(".json.tmp").exists())

    def test_tampered_facets_and_schema_are_rejected(self):
        data = self.catalog.to_dict()
        data["facets"]["groups"]["fake"] = 99
        with self.assertRaisesRegex(MaterialLibraryError, "facets"):
            MaterialCatalog.from_dict(data)
        data = self.catalog.to_dict()
        data["schema_version"] = 2
        with self.assertRaisesRegex(MaterialLibraryError, "schema_version"):
            MaterialCatalog.from_dict(data)


class SafeImportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        base = Path(self.temporary.name)
        self.tree = MaterialTree(base)
        self.catalog = build_catalog(self.tree.root, source_id="official")
        self.import_root = base / "imports"
        self.fluid = next(m for m in self.catalog.materials if m.name == "Fluid Noise")

    def tearDown(self):
        self.temporary.cleanup()

    def test_import_creates_managed_copy_manifest_and_is_idempotent(self):
        first = import_material(self.catalog, self.fluid.id, self.import_root)
        self.assertTrue(first.created)
        self.assertEqual(first.source_path.read_bytes(), Path(self.fluid.source_path).read_bytes())
        manifest = json.loads(first.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["material_id"], self.fluid.id)
        self.assertEqual(manifest["source_relative_path"], self.fluid.relative_path)
        second = import_material(self.catalog, self.fluid.id, self.import_root)
        self.assertFalse(second.created)
        self.assertEqual(second.source_path, first.source_path)

    def test_never_overwrites_foreign_directory_or_changed_import(self):
        foreign = self.import_root / self.fluid.id
        foreign.mkdir(parents=True)
        (foreign / "user-file.txt").write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(MaterialImportError, "not managed"):
            import_material(self.catalog, self.fluid.id, self.import_root)
        self.assertEqual((foreign / "user-file.txt").read_text(encoding="utf-8"), "keep")

        other_root = Path(self.temporary.name) / "other-imports"
        imported = import_material(self.catalog, self.fluid.id, other_root)
        imported.source_path.write_text("changed by user", encoding="utf-8")
        with self.assertRaisesRegex(MaterialImportError, "differs"):
            import_material(self.catalog, self.fluid.id, other_root)
        self.assertEqual(imported.source_path.read_text(encoding="utf-8"), "changed by user")

    def test_forged_source_escape_and_relative_path_mismatch_are_rejected(self):
        outside = Path(self.temporary.name) / "secret.frag"
        outside.write_text("void main(){}", encoding="utf-8")
        data = self.fluid.to_dict()
        data["source_path"] = str(outside)
        escaped = MaterialRecord.from_dict(data)
        forged_catalog = MaterialCatalog(
            source_id=self.catalog.source_id, source_label=self.catalog.source_label,
            source_root=self.catalog.source_root, materials=(escaped,),
        )
        with self.assertRaisesRegex(MaterialImportError, "escapes"):
            import_material(forged_catalog, escaped.id, self.import_root)

        data = self.fluid.to_dict()
        data["relative_path"] = "different.frag"
        mismatch = MaterialRecord.from_dict(data)
        mismatch_catalog = MaterialCatalog(
            source_id=self.catalog.source_id, source_label=self.catalog.source_label,
            source_root=self.catalog.source_root, materials=(mismatch,),
        )
        with self.assertRaisesRegex(MaterialImportError, "relative path"):
            import_material(mismatch_catalog, mismatch.id, self.import_root)

    def test_import_selection_deduplicates_and_unknown_id_fails(self):
        cellular = next(m for m in self.catalog.materials if m.name == "Cellular")
        results = import_materials(
            self.catalog, (self.fluid.id, self.fluid.id, cellular.id), self.import_root
        )
        self.assertEqual([item.id for item in results], [self.fluid.id, cellular.id])
        with self.assertRaisesRegex(MaterialLibraryError, "unknown material"):
            import_material(self.catalog, "mat_00000000000000000000", self.import_root)


if __name__ == "__main__":
    unittest.main()
