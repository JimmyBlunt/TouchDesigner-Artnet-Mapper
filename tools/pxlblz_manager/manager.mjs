import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { randomUUID } from 'node:crypto';
import { createRequire } from 'node:module';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import assert from 'node:assert/strict';
import { fromSnapshot, validateBundle, changedBundle, routeDifferences, digest, nativeConfig } from './core.mjs';
import { surfaceMap, diagnosticPattern } from './surface.mjs';

export const ROOT=path.dirname(fileURLToPath(import.meta.url));
export const settings=JSON.parse(fs.readFileSync(path.join(ROOT,'settings.json'),'utf8'));
export const requireIDE=createRequire(path.join(settings.ideRoot,'package.json'));
export const runFile=promisify(execFile);
export const DATA=path.join(ROOT,'data');
fs.mkdirSync(DATA,{recursive:true});
export const read=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\uFEFF/,''));
export function atomic(p,data) {
  fs.mkdirSync(path.dirname(p),{recursive:true});
  const tmp=p+'.'+randomUUID()+'.tmp';
  fs.writeFileSync(tmp,JSON.stringify(data,null,2)+'\n');
  fs.renameSync(tmp,p);
}
function manifest(dir,bundle){
  const hashes=Object.fromEntries(fs.readdirSync(dir).filter(name=>name!=='manifest.json').map(name=>[name,digest(fs.readFileSync(path.join(dir,name),'utf8'))]));
  atomic(path.join(dir,'manifest.json'),{createdAt:bundle.createdAt,summary:bundle.summary,hashes});
}
export async function request(url,{method='GET',body,headers={}}={}) {
  let response;
  try {response=await fetch(url,{method,headers:{...headers,...(body===undefined?{}:{'Content-Type':'application/json'})},
    ...(body===undefined?{}:{body:JSON.stringify(body)}),signal:AbortSignal.timeout(30000)});}
  catch {throw Error(`Lokaler Dienst ${new URL(url).origin} nicht erreichbar. Dienst starten und Einstellungen prüfen.`);}
  const text=await response.text();
  let value;try{value=JSON.parse(text);}catch{throw Error(`Ungültige Antwort: HTTP ${response.status}`);}
  if(!response.ok||value.ok===false||value.success===false) throw Error(value.error||`HTTP ${response.status}`);
  return value;
}
export async function td(script) {
  const response=await request(settings.tdUrl,{method:'POST',body:{script}});
  return typeof response.data.result==='string'?JSON.parse(response.data.result):response.data.result;
}
export async function ide(endpoint,options={}) {
  // Use the already provisioned local developer identity, not a browser cookie.
  assert(['localhost','127.0.0.1'].includes(new URL(settings.ideUrl).hostname),'Nur lokale Studio-Instanz erlaubt');
  const vars=fs.readFileSync(path.join(settings.ideRoot,'.dev.vars'),'utf8');
  const match=vars.match(/^\s*SESSION_SECRET\s*=\s*(.+?)\s*$/m);
  assert(match,'Lokaler SESSION_SECRET fehlt');
  const secret=match[1].replace(/^(['"])(.*)\1$/,'$2');
  const {createSessionToken}=await import(pathToFileURL(path.join(settings.ideRoot,'src/cloudflare/auth.ts')));
  const token=await createSessionToken({userId:'github:local-dev',primaryProvider:'github',primaryHandle:'local-dev',
    githubUserId:'local-dev',githubLogin:'local-dev',displayName:'Local Dev',avatarUrl:null},secret);
  return request(settings.ideUrl+endpoint,{...options,headers:{...options.headers,Cookie:'pxlblz_session='+encodeURIComponent(token)}});
}

export class Manager {
  constructor({data=DATA}={}) {this.data=data;fs.mkdirSync(data,{recursive:true});this.statePath=path.join(data,'state.json');
    this.state=fs.existsSync(this.statePath)?read(this.statePath):{};this.lastReport=null;}
  save(){atomic(this.statePath,this.state);}
  bundle(){assert(this.state.bundle,'Zuerst Prüfen und Exportieren');return read(this.state.bundle);}
  async capture(workspace=false){return td(`include_workspace = ${workspace?'True':'False'}\n`+fs.readFileSync(path.join(ROOT,'snapshot.py'),'utf8'));}
  async verify() {
    const [snapshot,router]=await Promise.all([this.capture(),request(settings.routerUrl+'/api/config')]);
    const bundle=fromSnapshot(snapshot,router.config);
    const differences=routeDifferences(bundle.config,router.config);
    let candidate=null;
    if(this.state.bundle) {try{candidate=validateBundle(this.bundle());}catch(e){candidate={error:e.message};}}
    const report={checkedAt:new Date().toISOString(),summary:bundle.summary,differences,candidate,
      snapshotFingerprint:bundle.sourceFingerprint,
      warnings:[`${bundle.summary.maskedOnOutputs} Ausgangsplätze werden durch die Maske schwarz gehalten.`,
        `${bundle.summary.unroutedAssigned} Layoutpunkte haben keinen Ausgang (Platzhalter prüfen).`],
      readyToExport:true,routerMatches:differences.length===0,source:snapshot.project};
    this.lastReport=report;
    atomic(path.join(this.data,'last-check.json'),report);
    return report;
  }
  async checkpoint(label) {
    const id=Date.now()+'-'+randomUUID().slice(0,8);
    const dir=path.join(this.data,'backups',id);fs.mkdirSync(dir,{recursive:true});
    const router=await request(settings.routerUrl+'/api/config');
    const saved={label,state:this.state,routerConfig:router.config,routerPath:router.path,createdAt:new Date().toISOString()};
    if(this.state.bundle)saved.bundle=this.bundle();
    atomic(path.join(dir,'backup.json'),saved);
    this.state={...this.state,lastBackup:dir};this.save();return dir;
  }
  async exportPackage() {
    const [snapshot,router]=await Promise.all([this.capture(true),request(settings.routerUrl+'/api/config')]);
    const bundle=fromSnapshot(snapshot,router.config);
    await this.checkpoint('export');
    const dir=path.join(this.data,'packages',Date.now()+'-'+randomUUID().slice(0,8));fs.mkdirSync(dir,{recursive:true});
    atomic(path.join(dir,'bundle.json'),bundle);
    atomic(path.join(dir,'map.json'),bundle.coordinates);
    atomic(path.join(dir,'active_mask.json'),bundle.mask);
    atomic(path.join(dir,'routes.json'),nativeConfig(bundle.config));
    fs.writeFileSync(path.join(dir,'workspace.json'),snapshot.workspace);
    manifest(dir,bundle);
    await this.validateRouter(path.join(dir,'routes.json'));
    this.state={...this.state,bundle:path.join(dir,'bundle.json'),packageDir:dir,testedHash:null,syncedHash:null};this.save();
    return {packageDir:dir,summary:bundle.summary};
  }
  async validateRouter(file){return (await runFile(settings.routerExe,['--config',file,'--list-routes','--dry-run'],{windowsHide:true,timeout:15000,maxBuffer:2e6})).stdout;}
  async fix() {
    // Regenerate only derived fields from authoritative source data. Never rescan/reindex.
    const before=this.state.bundle?this.bundle():null;
    const exported=await this.exportPackage();
    return {...exported,repairs:before?routeDifferences(this.bundle().config,before.config):['Map, Aktivmaske und Router-Konfiguration konsistent erstellt'],
      hardwareChanged:false};
  }
  async change(patch) {
    const before=this.bundle(),updated=changedBundle(before,patch);
    await this.checkpoint('change '+patch.route);
    const dir=path.join(this.data,'packages',Date.now()+'-'+randomUUID().slice(0,8));
    fs.cpSync(this.state.packageDir,dir,{recursive:true});
    atomic(path.join(dir,'bundle.json'),updated);atomic(path.join(dir,'routes.json'),nativeConfig(updated.config));
    manifest(dir,updated);
    await this.validateRouter(path.join(dir,'routes.json'));
    const difference=routeDifferences(updated.config,before.config);
    this.state={...this.state,bundle:path.join(dir,'bundle.json'),packageDir:dir,testedHash:null,syncedHash:null};this.save();
    return {difference,summary:updated.summary,hardwareChanged:false};
  }
  async bake(source,count) {
    const esbuild=requireIDE('esbuild');
    const result=await esbuild.build({entryPoints:[path.join(settings.ideRoot,'src/engine/maps/bake.ts')],
      bundle:true,format:'esm',platform:'node',write:false,logLevel:'silent'});
    const {bakeMapSource}=await import('data:text/javascript;base64,'+Buffer.from(result.outputFiles[0].text).toString('base64'));
    return bakeMapSource(source,count);
  }
  async sync({projection=this.state.projection||'surface',diagnostic=false}={}) {
    assert(['surface','spatial'].includes(projection),'Unbekannte Projektion');
    const b=this.bundle();validateBundle(b);
    assert.equal(this.state.testedHash,digest(b),'Paket zuerst mit Ausgabe testen prüfen');
    const check=await this.verify();assert.equal(check.snapshotFingerprint,b.sourceFingerprint,'TouchDesigner wurde geändert: Paket neu exportieren');
    await this.checkpoint('sync');
    const surface=projection==='surface'?surfaceMap(b):null;
    const source=JSON.stringify(surface?.points||b.coordinates),baked=await this.bake(source,b.coordinates.length);
    assert.equal(baked.points.length,b.coordinates.length);
    const mapId=randomUUID(),patternId=randomUUID();
    const map={id:mapId,name:`SchrankAll · ${projection==='surface'?'2D Fläche – Seiten + Rückwand':'3D Raum'} · ${b.coordinates.length}`,
      generator:'custom',dim:baked.dim,params:{},points:baked.points,source,updatedAt:Date.now()};
    const all=await ide('/api/patterns');
    const original=all.patterns.find(p=>p.id===settings.patternId);
    assert(original,'Ausgangs-Pattern nicht im lokalen Benutzerkonto gefunden');
    atomic(path.join(this.state.lastBackup,'original-pattern.json'),original);
    const pattern={...original,id:patternId,name:original.name+' · Gesamtinstallation',
      settings:{...original.settings,mapId,pixelCount:b.coordinates.length},updatedAt:Date.now()};
    if(diagnostic){pattern.name='Schrank · Smooth Trail · 2D-Fläche';pattern.src=diagnosticPattern(b);pattern.controls={};}
    await ide('/api/maps',{method:'POST',body:map});
    await ide('/api/patterns',{method:'POST',body:pattern});
    const maps=await ide('/api/maps'),patterns=await ide('/api/patterns');
    assert.equal(maps.maps.find(m=>m.id===mapId)?.source,source,'Map-Rückleseprüfung fehlgeschlagen');
    assert.equal(patterns.patterns.find(p=>p.id===patternId)?.settings?.mapId,mapId,'Pattern-Zuordnung fehlt');
    if(surface){atomic(path.join(this.data,'surface-map.json'),surface.points);atomic(path.join(this.data,'surface-report.json'),surface.report);}
    this.state={...this.state,mapId,patternId,projection,syncedHash:digest(b)};this.save();
    return {mapId,patternId,projection,url:this.patternUrl(false),output:'aus',originalPatternUnchanged:true,
      warning:!diagnostic&&original.src?.includes('MATRIX_PIXELS')?'Dieses Pattern enthält Testboard-spezifische Rasterlogik. Für freie Flächen den Smooth-Trail-Test oder ein allgemeines render2D-Pattern verwenden.':null};
  }
  patternUrl(output=false){return `${settings.ideUrl}/PXLBLZ-IDE/studio/patterns/${this.state.patternId||settings.patternId}?pxout=${output?1:0}&pxoutUrl=${encodeURIComponent(`ws://127.0.0.1:${settings.port}/pixels`)}`;}
  async applyRouting() {
    const b=this.bundle();validateBundle(b);
    assert.equal(this.state.testedHash,digest(b),'Paket zuerst testen');
    assert.equal(this.state.syncedHash,digest(b),'Paket zuerst nach PXLBLZ synchronisieren');
    const check=await this.verify();assert.equal(check.snapshotFingerprint,b.sourceFingerprint,'TouchDesigner wurde geändert: Paket neu exportieren');
    const before=await this.checkpoint('apply-routing');
    const original=read(path.join(before,'backup.json'));
    // Stop TD's sender before assigning overlapping universes to PXLBLZ.
    await td("import json\nfrom pixelblaze_mapper.routing_transaction import stop_outputs\nr=op('/project1/multi_controller_output')\nstop_outputs(r)\nresult=json.dumps({'output':'off'})");
    try {
      await request(settings.routerUrl+'/api/config/check',{method:'POST',body:nativeConfig(b.config)});
      await request(settings.routerUrl+'/api/config',{method:'PUT',body:nativeConfig(b.config)});
      const current=await request(settings.routerUrl+'/api/config');
      assert.equal(routeDifferences(b.config,current.config).length,0,'Router-Rückleseprüfung fehlgeschlagen');
    }catch(e){await request(settings.routerUrl+'/api/config',{method:'PUT',body:original.routerConfig});throw e;}
    this.state.appliedHash=digest(b.config);this.save();
    return {applied:true,output:'gesperrt bis Ausgabe einschalten',backup:before};
  }
  async rollback() {
    assert(this.state.lastBackup,'Keine Sicherung vorhanden');
    const backup=read(path.join(this.state.lastBackup,'backup.json'));
    await request(settings.routerUrl+'/api/config/check',{method:'POST',body:backup.routerConfig});
    await request(settings.routerUrl+'/api/config',{method:'PUT',body:backup.routerConfig});
    const verify=await request(settings.routerUrl+'/api/config');
    assert.equal(routeDifferences(backup.routerConfig,verify.config).length,0,'Wiederherstellung nicht bestätigt');
    this.state=backup.state;this.save();
    return {restored:true,label:backup.label,output:'aus',note:'Importierte Kopien bleiben als wiederverwendbare Bibliothekseinträge erhalten.'};
  }
}
