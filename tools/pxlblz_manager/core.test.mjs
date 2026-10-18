import test from 'node:test';
import assert from 'node:assert/strict';
import {changedBundle,maskFrame,validateBundle,routeDifferences,nativeConfig} from './core.mjs';
const fixture=()=>({coordinates:[[0,0,0],[1,0,0],[0,1,0]],mask:[1,0,1],config:{version:2,
  input:{pixel_count:3,variable_size:false,fps_target:30},artnet:{udp_port:6454,unicast:true},
  controllers:[{name:'A',target_ip:'127.0.0.1',enabled:true,fps_target:30}],
  routes:[{name:'port1',enabled:true,target_ip:'127.0.0.1',physical_port:1,pixel_start:0,pixel_count:3,universe_start:0,color_order:'RGB',brightness:.5}]}});
test('black holes keep source indices; brightness applies once; input stays immutable',()=>{
  const b=fixture(),frame=Buffer.from([100,20,10,255,255,255,80,40,20]);
  assert.deepEqual([...maskFrame(frame,b)],[50,10,5,0,0,0,40,20,10]);assert.equal(frame[3],255);
  assert.throws(()=>maskFrame(Buffer.alloc(6),b),/Framegröße/);
});
test('map and routing invariants reject corrupt input',()=>{
  for(const mutate of [b=>b.mask.pop(),b=>b.coordinates[0][0]=NaN,b=>b.config.input.pixel_count=2,
    b=>b.config.input.variable_size=true,b=>b.config.routes[0].pixel_count=4,
    b=>b.config.routes[0].target_ip='999.0.0.1',b=>b.config.routes[0].brightness=2]){
    const b=fixture();mutate(b);assert.throws(()=>validateBundle(b));
  }
});
test('overlapping destination universes are rejected',()=>{
  const b=fixture();b.config.routes.push({...b.config.routes[0],name:'duplicate',physical_port:2});
  assert.throws(()=>validateBundle(b),/Überlappende Art-Net/);
});
test('route draft is independent and validates before mutation',()=>{
  const b=fixture(),c=changedBundle(b,{route:'port1',changes:{target_ip:'127.0.0.2',brightness:.3}});
  assert.equal(b.config.routes[0].target_ip,'127.0.0.1');assert.equal(c.config.controllers[0].target_ip,'127.0.0.2');
  assert.throws(()=>changedBundle(b,{route:'port1',changes:{pixel_start:5}}));
});
test('drift detects unsafe frame mode, destinations and controller state',()=>{
  const b=fixture().config,c=structuredClone(b);c.input.variable_size=true;c.controllers[0].enabled=false;c.routes[0].universe_start=1;
  assert.equal(routeDifferences(b,c).length,3);assert.deepEqual(routeDifferences(b,nativeConfig(b)),[]);
  const omitted=nativeConfig(b);delete omitted.input.variable_size;assert.deepEqual(routeDifferences(b,omitted),[]);
});
