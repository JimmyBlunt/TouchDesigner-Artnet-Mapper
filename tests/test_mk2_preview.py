"""Execute the shipped preview JS in Node: one retry, then accessible fallback.

Node is required for this functional acceptance test (PATH or Codex runtime).
This checks actual JS event handlers; the parent UI QA also verifies real images.
"""
from pathlib import Path
import shutil
import subprocess
import unittest


SCRIPT = Path(__file__).resolve().parents[1]/'pixelblaze_mapper'/'timeline_assets'/'pads.js'


def find_node():
    installed = shutil.which('node')
    bundled = Path.home()/'.cache'/'codex-runtimes'/'codex-primary-runtime'/'dependencies'/'node'/'bin'/'node.exe'
    if installed:
        return installed
    if bundled.is_file():
        return str(bundled)
    raise RuntimeError('MK2 preview acceptance tests require Node.js on PATH or the bundled Codex runtime.')


HARNESS = r'''
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const elements=new Map();
const sandbox={
  $:(id)=>{if(!elements.has(id))elements.set(id,{});return elements.get(id);},
  node:(tag,attributes={},text='')=>({tag,...attributes,textContent:text,replaceWith(replacement){this.replacement=replacement;}})
};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),sandbox,{filename:'pads.js'});
const make=sandbox.padPreviewImage;
'''


class PreviewTests(unittest.TestCase):
    def run_js(self, script):
        result = subprocess.run([find_node(), '-e', HARNESS+script, str(SCRIPT)], capture_output=True,
                                text=True, encoding='utf-8', timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)

    def test_initial_success_keeps_image_without_retry_or_fallback(self):
        self.run_js(r'''
const image=make('material_1');
assert.equal(image.src,'/api/pad_image?id=material_1');
assert.equal(image.loading,'lazy');
assert.equal(image.alt,'');
image.onload();
assert.equal(image.onerror,null);
assert.equal(image.onload,null);
assert.equal(image.replacement,undefined);
assert.equal(image.src,'/api/pad_image?id=material_1');
''')

    def test_one_cache_busted_retry_then_success_preserves_image(self):
        self.run_js(r'''
const image=make('material_2');
image.onerror();
assert.equal(image.src,'/api/pad_image?id=material_2&retry=1');
assert.equal(image.replacement,undefined);
image.onload();
assert.equal(image.onerror,null);
assert.equal(image.replacement,undefined);
''')

    def test_second_failure_replaces_broken_image_with_accessible_placeholder(self):
        self.run_js(r'''
const image=make('material_3');
image.onerror();
image.onerror();
assert.equal(image.src,'/api/pad_image?id=material_3&retry=1');
assert.equal(image.onerror,null);
assert.equal(image.onload,null);
assert.equal(image.replacement.tag,'span');
assert.equal(image.replacement.class,'padPlaceholder');
assert.equal(image.replacement.role,'img');
assert.equal(image.replacement['aria-label'],'Kein Vorschaubild verfügbar');
assert.equal(image.replacement.textContent,'Kein Bild');
''')

    def test_retries_are_per_image_and_preserve_approved_backend_route(self):
        self.run_js(r'''
const id='https://example.invalid/x?image=1&unsafe=2';
const a=make(id),b=make('material_4');
a.onerror();
assert.equal(a.src,'/api/pad_image?id='+encodeURIComponent(id)+'&retry=1');
assert.equal(b.src,'/api/pad_image?id=material_4');
b.onerror();
assert.equal(b.src,'/api/pad_image?id=material_4&retry=1');
a.onerror();
assert.equal(b.replacement,undefined);
''')


if __name__ == '__main__':
    unittest.main()
