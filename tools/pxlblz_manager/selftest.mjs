import fs from 'node:fs';
import path from 'node:path';
import net from 'node:net';
import dgram from 'node:dgram';
import { spawn } from 'node:child_process';
import assert from 'node:assert/strict';
import { once } from 'node:events';
import { maskFrame, validateBundle, digest } from './core.mjs';
import { requireIDE, settings, atomic } from './manager.mjs';
const {WebSocket}=requireIDE('ws');

async function freePort(){const s=net.createServer();s.listen(0,'127.0.0.1');await once(s,'listening');const p=s.address().port;await new Promise(r=>s.close(r));return p;}
export async function testPackage(manager) {
  const bundle=manager.bundle(),summary=validateBundle(bundle);
  const baked=await manager.bake(JSON.stringify(bundle.coordinates),bundle.coordinates.length);
  assert.equal(baked.points.length,bundle.coordinates.length);
  const udp=dgram.createSocket('udp4');udp.bind(0,'127.0.0.1');await once(udp,'listening');
  const udpPort=udp.address().port,wsPort=await freePort();
  const config=structuredClone(bundle.config);
  config.artnet.udp_port=udpPort;
  config.controllers=[{name:'LOOPBACK_TEST',target_ip:'127.0.0.1',enabled:true,fps_target:30}];
  config.routes.forEach(r=>r.target_ip='127.0.0.1');
  const dir=path.join(manager.data,'tests',Date.now().toString());fs.mkdirSync(dir,{recursive:true});
  const file=path.join(dir,'loopback-routes.json');atomic(file,config);
  const frame=Buffer.alloc(bundle.coordinates.length*3);
  for(let i=0;i<bundle.coordinates.length;i++) {frame[3*i]=(i*17+13)%201;frame[3*i+1]=(i*11+29)%199;frame[3*i+2]=(i*7+41)%197;}
  const masked=maskFrame(frame,bundle),expected=new Map();
  for(const r of config.routes.filter(r=>r.enabled)) {
    for(let base=0;base<r.pixel_count;base+=170) {
      const pixels=Math.min(170,r.pixel_count-base),rawBytes=pixels*3;
      const bytes=Buffer.alloc(rawBytes+(rawBytes%2));
      for(let i=0;i<pixels;i++) for(let c=0;c<3;c++) {
        const source=r.pixel_start+base+i;
        const channel='RGB'.indexOf(r.color_order[c]);
        bytes[i*3+c]=bundle.mask[source]?Math.floor(frame[source*3+channel]*r.brightness+0.5):0;
      }
      expected.set(r.universe_start+base/170,bytes);
    }
  }
  const received=new Map();let packetError=null;
  udp.on('message',packet=>{try{
    assert.equal(packet.subarray(0,8).toString(),'Art-Net\0');assert.equal(packet.readUInt16LE(8),0x5000);
    const u=packet.readUInt16LE(14),size=packet.readUInt16BE(16);
    assert(expected.has(u),`Unerwartetes Universum ${u}`);
    assert.equal(packet.length,18+size);
    assert.deepEqual(packet.subarray(18),expected.get(u),`Falsche LED-/Masken-/Farbwerte in Universum ${u}`);
    received.set(u,true);
  }catch(e){packetError=e;}});
  const child=spawn(settings.routerExe,['--config',file,'--input','ws','--ws-listen',`127.0.0.1:${wsPort}`,
    '--status-listen','','--duration','8s'],{windowsHide:true,stdio:['ignore','pipe','pipe']});
  let log='';child.stdout.on('data',d=>log+=d);child.stderr.on('data',d=>log+=d);
  let ws;
  try {
    const until=Date.now()+5000;
    while(!log.includes('Pixel input listening')) {
      if(child.exitCode!==null)throw Error('Testrouter abgebrochen: '+log);
      if(Date.now()>until)throw Error('Testrouter wurde nicht bereit');
      await new Promise(r=>setTimeout(r,60));
    }
    ws=new WebSocket(`ws://127.0.0.1:${wsPort}/pixels`);await once(ws,'open');ws.send(masked);
    const deadline=Date.now()+3000;
    while(received.size<expected.size&&!packetError&&Date.now()<deadline)await new Promise(r=>setTimeout(r,25));
    if(packetError)throw packetError;
    assert.equal(received.size,expected.size,'Art-Net-Universen fehlen');
    assert.throws(()=>maskFrame(Buffer.alloc(3),bundle),/Framegröße/);
    const result={passed:true,time:new Date().toISOString(),mapParser:true,mask:true,indexOrder:true,colorOrder:true,
      universes:received.size,frameBytes:masked.length,summary,hardwareOutput:false,bundleHash:digest(bundle)};
    atomic(path.join(dir,'result.json'),result);
    manager.state.testedHash=digest(bundle);manager.state.lastTest=result;manager.save();return result;
  } finally {ws?.terminate();child.kill();udp.close();fs.writeFileSync(path.join(dir,'router.log'),log);}
}
