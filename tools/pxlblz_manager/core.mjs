import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

export const digest = value => createHash('sha256').update(JSON.stringify(value)).digest('hex');
export const clone = value => structuredClone(value);
const integer = (n, lo, hi) => Number.isInteger(n) && n >= lo && n <= hi;
export function table(rows) {
  assert(Array.isArray(rows) && rows.length, 'Tabelle fehlt');
  return rows.slice(1).map(r => Object.fromEntries(rows[0].map((key, i) => [key, r[i]])));
}
export function validateBundle(bundle) {
  const { coordinates: p, mask, config } = bundle;
  assert(Array.isArray(p) && integer(p.length, 1, 65536), 'Map muss 1..65536 Punkte enthalten');
  assert(p.every(v => Array.isArray(v) && v.length === 3 && v.every(Number.isFinite)), 'Ungültige XYZ-Koordinaten');
  assert(Array.isArray(mask) && mask.length === p.length && mask.every(v => v === 0 || v === 1), 'Maske passt nicht zur Map');
  assert.equal(config.input.pixel_count, p.length, 'Router-Pixelzahl passt nicht zur Map');
  assert.equal(config.input.variable_size, false, 'Feste Framegröße erforderlich');
  assert.equal(config.version, 2, 'Router-Schema muss Version 2 sein');
  assert(integer(config.artnet.udp_port, 1, 65535), 'Ungültiger UDP-Port');
  assert(integer(config.input.fps_target, 1, 240), 'Ungültige Bildrate');
  const targets = new Set();
  const occupied = new Set();
  for (const c of config.controllers) {
    assert(!targets.has(c.target_ip), 'Controller-IP doppelt'); targets.add(c.target_ip);
    assert(integer(c.fps_target, 1, 240), 'Ungültige Controller-Bildrate');
  }
  const routed = new Set();
  const levels=new Map(),ports=new Set();
  for (const r of config.routes.filter(r => r.enabled)) {
    assert(typeof r.name === 'string' && r.name.length, 'Routenname fehlt');
    assert(typeof r.target_ip === 'string' && r.target_ip.split('.').length === 4 &&
      r.target_ip.split('.').every(v => /^\d+$/.test(v) && integer(Number(v), 0, 255)), 'Ungültige IPv4-Adresse');
    assert(targets.has(r.target_ip), 'Route ohne Controller');
    assert(integer(r.pixel_start, 0, p.length - 1) && integer(r.pixel_count, 1, p.length - r.pixel_start), 'Quellbereich außerhalb der Map');
    assert(integer(r.universe_start, 0, 32767) && r.universe_start + Math.ceil(r.pixel_count / 170) <= 32768, 'Ungültiger Universenbereich');
    assert(integer(r.physical_port, 1, 64), 'Ungültiger physischer Port');
    assert(['RGB','RBG','GRB','GBR','BRG','BGR'].includes(r.color_order), 'Ungültige Farbreihenfolge');
    assert(Number.isFinite(r.brightness) && r.brightness >= 0 && r.brightness <= 1, 'Helligkeit muss 0..1 sein');
    const portKey=`${r.target_ip}/${r.physical_port}`;
    assert(!ports.has(portKey),'Physischer Ausgang doppelt');ports.add(portKey);
    for (let u = 0; u < Math.ceil(r.pixel_count / 170); u++) {
      const key = `${r.target_ip}/${r.universe_start + u}`;
      assert(!occupied.has(key), `Überlappende Art-Net-Universen: ${key}`); occupied.add(key);
    }
    for (let i = r.pixel_start; i < r.pixel_start + r.pixel_count; i++) {
      assert(!levels.has(i)||levels.get(i)===r.brightness,'Überlappende Quellen mit unterschiedlicher Helligkeit');
      routed.add(i);levels.set(i,r.brightness);
    }
  }
  return { slots: p.length, assigned: mask.reduce((a,b)=>a+b,0), unused: mask.filter(v=>!v).length,
    routed: routed.size, maskedOnOutputs: [...routed].filter(i=>!mask[i]).length,
    unroutedAssigned: mask.filter((v,i)=>v&&!routed.has(i)).length, routes: config.routes.filter(r=>r.enabled).length,
    universes: occupied.size };
}

export function fromSnapshot(snapshot, currentRouter) {
  const map = table(snapshot.tables.map);
  const masks = table(snapshot.tables.mask);
  assert(map.every((r,i)=>Number(r.index)===i), 'Aktive Quellindizes sind nicht lückenlos');
  assert(masks.length===map.length && masks.every((r,i)=>Number(r.index)===i), 'Maskenindizes stimmen nicht');
  const coordinates = map.map(r=>[Number(r.tx),Number(r.ty),Number(r.tz)]);
  const mask = masks.map(r=>Number(r.enabled));
  const assigned = new Set();
  for (const w of snapshot.world) {
    assert(!assigned.has(w.index), 'Doppelte Layoutadresse'); assigned.add(w.index);
    assert(mask[w.index]===1, 'Entwurf und aktive Maske unterscheiden sich');
    assert(w.point.every((v,a)=>Math.abs(v-coordinates[w.index][a])<=1e-7),
      '3D-Entwurf unterscheidet sich von der aktiven Map. Gewünschten Stand zuerst in TouchDesigner übernehmen.');
  }
  assert.equal(assigned.size,mask.reduce((a,b)=>a+b,0),'Aktive Map und Entwurf sind nicht deckungsgleich');
  const controllers = table(snapshot.tables.controllers).filter(c=>c.enabled==='1');
  const segments = table(snapshot.tables.segments);
  const routes=[];
  for(const c of controllers) for(const s of segments.filter(s=>s.controller===c.name)) {
    assert.equal(s.reverse,'0','Umgekehrte Route muss ausdrücklich umgerechnet werden');
    const dest=Number(s.destination_start);
    assert.equal(dest%170,0,'Route mit Kanaloffset benötigt gesonderte Zuordnung');
    const universe=Number(c.start_universe)+dest/170;
    const existing=currentRouter.routes.find(r=>r.target_ip===c.target_ip&&r.universe_start===universe);
    const port=existing?.physical_port ?? Number(s.name.match(/PORT_(\d+)/)?.[1]??s.name.match(/_(\d+)$/)?.[1]);
    routes.push({name:s.name,enabled:true,target_ip:c.target_ip,physical_port:port,
      pixel_start:Number(s.source_start),pixel_count:Number(s.count),universe_start:universe,
      color_order:existing?.color_order||s.color_override||c.color_order,brightness:Number(c.brightness)});
  }
  const bundle={schema:'pxlblz-installation-package',version:1,createdAt:new Date().toISOString(),
    coordinates,mask,source:snapshot.project,sourceFingerprint:digest(snapshot.tables),
    objects:snapshot.objects,world:snapshot.world,
    config:{version:2,input:{pixel_count:coordinates.length,fps_target:30,stale_timeout_ms:1000,on_stale:'blackout',variable_size:false},
      artnet:{udp_port:6454,unicast:true},controllers:controllers.map(c=>({name:c.name,target_ip:c.target_ip,enabled:true,fps_target:30})),routes}};
  bundle.summary=validateBundle(bundle);
  return bundle;
}

export function maskFrame(frame, bundle) {
  assert.equal(frame.length,bundle.mask.length*3,'Falsche RGB-Framegröße');
  const out=Buffer.from(frame);
  for(let i=0;i<bundle.mask.length;i++) if(!bundle.mask[i]) out.fill(0,i*3,i*3+3);
  const applied=new Set();
  for(const r of bundle.config.routes.filter(r=>r.enabled)) for(let i=r.pixel_start;i<r.pixel_start+r.pixel_count;i++) {
    if(applied.has(i))continue;applied.add(i);
    for(let c=0;c<3;c++)out[i*3+c]=Math.floor(out[i*3+c]*r.brightness+0.5);
  }
  return out;
}
// Native router does not implement brightness. The gateway applies it before sending RGB.
export function nativeConfig(config){const out=clone(config);out.routes.forEach(r=>delete r.brightness);return out;}
export function routeDifferences(expected, actual) {
  const diffs=[];
  for(const section of ['input','artnet']) for(const [key,value] of Object.entries(expected[section]))
    if(key!=='pixel_count' && (key==='variable_size'?Boolean(actual[section]?.[key]):actual[section]?.[key])!==value) diffs.push(`${section}.${key}: ${actual[section]?.[key]} → ${value}`);
  for(const c of expected.controllers){
    const a=actual.controllers.find(a=>a.target_ip===c.target_ip);
    for(const key of ['enabled','fps_target']) if(a?.[key]!==c[key]) diffs.push(`${c.name}.${key}: ${a?.[key]} → ${c[key]}`);
  }
  if(expected.input.pixel_count!==actual.input.pixel_count) diffs.push(`Pixelzahl: ${actual.input.pixel_count} → ${expected.input.pixel_count}`);
  for(const r of expected.routes) {
    const a=actual.routes.find(a=>a.target_ip===r.target_ip&&a.physical_port===r.physical_port);
    if(!a) {diffs.push(`${r.name}: Ausgang fehlt`);continue;}
    for(const k of ['pixel_start','pixel_count','universe_start','color_order','brightness','enabled'])
      if(!(k==='brightness'&&(a[k]===undefined||r[k]===undefined)) && a[k]!==r[k]) diffs.push(`${r.name} · ${k}: ${a[k]??'Standard'} → ${r[k]}`);
  }
  for(const a of actual.routes) if(!expected.routes.some(r=>r.target_ip===a.target_ip&&r.physical_port===a.physical_port))
    diffs.push(`${a.name}: nicht im TouchDesigner-Layout enthalten`);
  return diffs;
}
export function changedBundle(bundle, patch) {
  const allowed=['target_ip','physical_port','pixel_start','pixel_count','universe_start','color_order','brightness','enabled'];
  assert(Object.keys(patch.changes).every(k=>allowed.includes(k)),'Nicht unterstützte Änderung');
  const out=clone(bundle),route=out.config.routes.find(r=>r.name===patch.route);
  assert(route,'Route nicht gefunden');
  const oldIp=route.target_ip;
  Object.assign(route,patch.changes);
  if(route.target_ip!==oldIp&&!out.config.controllers.some(c=>c.target_ip===route.target_ip)) {
    out.config.controllers.push({...out.config.controllers.find(c=>c.target_ip===oldIp),name:route.name,target_ip:route.target_ip});
  }
  out.config.controllers=out.config.controllers.filter(c=>out.config.routes.some(r=>r.target_ip===c.target_ip));
  out.summary=validateBundle(out);
  out.createdAt=new Date().toISOString();
  return out;
}
