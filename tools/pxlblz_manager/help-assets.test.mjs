import test from 'node:test';
import assert from 'node:assert/strict';
import {helpAsset} from './help-assets.mjs';
test('help serves guides, animations and the public catalog',()=>{
 assert.equal(helpAsset('/release-help/pxlblz_manager.html').type,'text/html; charset=utf-8');
 assert.equal(helpAsset('/release-help/diagrams/sequencer-overlap.gif').type,'image/gif');
 assert.equal(helpAsset('/release-help/catalog.json').type,'application/json; charset=utf-8');
});
test('help rejects traversal and private runtime reports',()=>{
 for(const url of ['/release-help/../README.md','/release-help/%2e%2e/README.md','/release-help/qa/baseline-live.json','/config/material_pads.json'])assert.equal(helpAsset(url),null);
});
