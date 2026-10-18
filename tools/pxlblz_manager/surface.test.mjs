import test from 'node:test';
import assert from 'node:assert/strict';
import {surfaceMap} from './surface.mjs';
function fixture(){const rear=[[0,1,.3],[1,1,.3],[0,1,.8],[1,1,.8]],side=[[0,.5,.3],[1,.5,.3],[0,1,.3],[1,1,.3]];
  return {objects:[{id:'rear',name:'Rear'},{id:'side',name:'Side'}],coordinates:[...rear,...side,[0,0,0]],
    world:[...rear.map((point,index)=>({point,index,object_id:'rear'})),...side.map((point,i)=>({point,index:i+4,object_id:'side'}))]};}
test('unfolding joins hinge continuously and keeps LED index order',()=>{
  const b=fixture(),before=JSON.stringify(b),s=surfaceMap(b);
  assert.equal(JSON.stringify(b),before);assert.equal(s.points.length,9);
  assert.deepEqual(s.points[0],s.points[6]);assert.deepEqual(s.points[1],s.points[7]);
  assert.deepEqual(s.points[4],[0,0]);assert.deepEqual(s.points[3],[1,1]);
  assert(s.report.panels.every(p=>p.span.every(v=>v>.4)));
});
test('inactive origin never expands map bounds or invents a remote dot',()=>{
  const s=surfaceMap(fixture());assert.deepEqual(s.points[8],s.points[0]);assert(s.points.flat().every(v=>v>=0&&v<=1));
});
test('unknown tilted faces block automatic unwrap',()=>{
  const b=fixture();b.world[0].point=[0,0,0];assert.throws(()=>surfaceMap(b),/unklar/);
});
