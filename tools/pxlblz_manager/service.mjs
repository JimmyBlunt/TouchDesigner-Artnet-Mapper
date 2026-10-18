import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { randomBytes } from 'node:crypto';
import assert from 'node:assert/strict';
import { Manager, ROOT, settings, request, requireIDE, td } from './manager.mjs';
import { maskFrame, digest, routeDifferences } from './core.mjs';
import { testPackage } from './selftest.mjs';
import { helpAsset } from './help-assets.mjs';

const {WebSocket,WebSocketServer}=requireIDE('ws');
const manager=new Manager();
const token=randomBytes(24).toString('hex');
let busy=false,output=false,socket=null,lastInput=0,lastError=null,activeBundle=null,exclusiveTest=false,stopGeneration=0;
const stats={received:0,sent:0,rejected:0,dropped:0};
function disarm(){stopGeneration++;output=false;if(socket?.readyState===WebSocket.OPEN&&activeBundle)socket.send(Buffer.alloc(activeBundle.mask.length*3));socket?.close();socket=null;activeBundle=null;}
async function arm(){
  disarm();
  const generation=stopGeneration;
  const b=manager.bundle();assert.equal(manager.state.testedHash,digest(b),'Paket zuerst testen');
  assert.equal(manager.state.syncedHash,digest(b),'Paket zuerst synchronisieren');
  const check=await manager.verify();assert.equal(check.snapshotFingerprint,b.sourceFingerprint,'TouchDesigner wurde geändert: neu exportieren');
  const r=await request(settings.routerUrl+'/api/config');
  assert.equal(routeDifferences(b.config,r.config).length,0,'Router-Zuordnung passt nicht. Routing zuerst anwenden.');
  await td("import json\ns=op('/project1/multi_controller_output/artnet_510_sender_callbacks').module.status()\nresult=json.dumps({'enabled':bool(s.get('enabled'))})").then(s=>assert(!s.enabled,'TouchDesigner sendet noch'));
  assert.equal(generation,stopGeneration,'Einschalten wurde durch Stop abgebrochen');
  const current=new WebSocket(settings.routerWs);socket=current;
  current.on('error',e=>{if(socket===current){lastError=e.message;disarm();}});
  current.on('close',()=>{if(socket===current)disarm();});
  await new Promise((resolve,reject)=>{const timer=setTimeout(()=>{current.terminate();reject(Error('Router-Verbindung Zeitlimit'));},5000);current.once('open',()=>{clearTimeout(timer);resolve();});current.once('error',e=>{clearTimeout(timer);reject(e);});});assert.equal(generation,stopGeneration,'Einschalten wurde durch Stop abgebrochen');activeBundle=b;output=true;
}
function forward(data){
  stats.received++;lastInput=Date.now();
  if(!output||socket?.readyState!==WebSocket.OPEN){stats.dropped++;return;}
  try {const frame=maskFrame(data,activeBundle);
    if(socket.bufferedAmount>=frame.length){stats.dropped++;return;}
    socket.send(frame);stats.sent++;
  }catch(e){stats.rejected++;lastError=e.message;disarm();}
}
const gateway=new WebSocketServer({noServer:true,maxPayload:65536*3});
gateway.on('connection',ws=>{ws.on('message',(data,binary)=>{if(exclusiveTest){stats.dropped++;return;}if(binary)forward(data);else{stats.rejected++;ws.close(1003);}});ws.on('error',()=>{});});
const send=(res,status,data)=>{res.writeHead(status,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(data));};
const server=http.createServer(async(req,res)=>{
  try {
    const host=req.headers.host;
    if(![`localhost:${settings.port}`,`127.0.0.1:${settings.port}`].includes(host))return send(res,403,{error:'Host nicht erlaubt'});
    const url=new URL(req.url,`http://${host}`);
    if(req.method==='GET'&&url.pathname==='/favicon.ico'){res.writeHead(204);return res.end();}
    if(req.method==='GET'&&url.pathname==='/release-help.js'){res.writeHead(200,{'Content-Type':'text/javascript; charset=utf-8','Cache-Control':'no-store'});return res.end(fs.readFileSync(path.join(ROOT,'release-help.js')));}
    if(req.method==='GET'&&url.pathname.startsWith('/release-help/')){
      const asset=helpAsset(url.pathname);if(!asset)return send(res,404,{error:'Hilfe nicht gefunden'});
      res.writeHead(200,{'Content-Type':asset.type,'Cache-Control':'no-store'});return fs.createReadStream(asset.target).pipe(res);
    }
    if(req.method==='GET'&&url.pathname==='/'){res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});return res.end(fs.readFileSync(path.join(ROOT,'ui.html'),'utf8').replaceAll('__TOKEN__',token));}
    if(req.method==='GET'&&url.pathname==='/api/session')return send(res,200,{token});
    if(req.method==='GET'&&url.pathname.startsWith('/download/')){
      const name=url.pathname.slice(10);
      if(!['map.json','active_mask.json','routes.json','workspace.json','bundle.json','manifest.json'].includes(name)||!manager.state.packageDir)return send(res,404,{error:'Paket fehlt'});
      res.writeHead(200,{'Content-Type':'application/json','Content-Disposition':`attachment; filename="${name}"`});
      return fs.createReadStream(path.join(manager.state.packageDir,name)).pipe(res);
    }
    if(req.method==='GET'&&url.pathname==='/api/state')return send(res,200,{busy,output,lastError,stats,lastInput,
      report:manager.lastReport,state:manager.state,testCurrent:manager.state.bundle&&manager.state.testedHash===digest(manager.bundle()),summary:manager.state.bundle?manager.bundle().summary:null,
      routes:manager.state.bundle?manager.bundle().config.routes:[],patternUrl:manager.patternUrl(false),liveUrl:manager.patternUrl(true)});
    if(req.method!=='POST'||!url.pathname.startsWith('/api/'))return send(res,404,{error:'Nicht gefunden'});
    if(req.headers['x-manager-token']!==token)return send(res,403,{error:'Sitzung neu laden'});
    if(req.headers.origin&&!['http://localhost:'+settings.port,'http://127.0.0.1:'+settings.port].includes(req.headers.origin))return send(res,403,{error:'Fremder Ursprung nicht erlaubt'});
    if(url.pathname==='/api/stop'){disarm();return send(res,200,{ok:true,result:{output:false}});}
    if(busy)return send(res,409,{error:'Ein Vorgang läuft bereits'});
    let raw='';for await(const chunk of req){raw+=chunk;if(raw.length>100000)throw Error('Anfrage zu groß');}
    const args=raw?JSON.parse(raw):{};const action=url.pathname.slice(5);
    if(!['verify','export','fix','change','test','sync','surface','apply','rollback','output','stop','live-test'].includes(action))return send(res,404,{error:'Unbekannte Aktion'});
    busy=true;let result;
    try {
      if(!['verify','output','live-test'].includes(action))disarm();
      switch(action){
        case 'verify':result=await manager.verify();break;
        case 'export':result=await manager.exportPackage();break;
        case 'fix':result=await manager.fix();break;
        case 'change':result=await manager.change(args);break;
        case 'test':result=await testPackage(manager);break;
        case 'sync':result=await manager.sync(args);break;
        case 'surface':result=await manager.sync({projection:'surface',diagnostic:true});break;
        case 'apply':result=await manager.applyRouting();break;
        case 'rollback':result=await manager.rollback();break;
        case 'output':await arm();result={output:true};break;
        case 'stop':disarm();result={output:false};break;
        case 'live-test':{
          const b=manager.bundle(),r=b.config.routes.find(r=>r.name===args.route);assert(r,'Ausgang auswählen');
          const local=Number(args.localIndex??0);assert(Number.isInteger(local)&&local>=0&&local<r.pixel_count,'LED außerhalb des Ausgangs');
          const source=r.pixel_start+local;assert(b.mask[source]===1,'Diese LED besitzt keine Messposition und bleibt maskiert');
          exclusiveTest=true;
          try{await arm();const frame=Buffer.alloc(b.mask.length*3);frame[source*3]=8;frame[source*3+1]=8;frame[source*3+2]=8;
          forward(frame);await new Promise(resolve=>setTimeout(resolve,750));result={testedSource:source,durationMs:750};}
          finally{disarm();exclusiveTest=false;}break;
        }
      }
      lastError=null;send(res,200,{ok:true,result});
    }finally{busy=false;}
  }catch(e){lastError=e.message;send(res,400,{error:e.message});}
});
server.on('upgrade',(req,socket,head)=>{
  const allowed=[settings.ideUrl,`http://localhost:${settings.port}`,`http://127.0.0.1:${settings.port}`];
  if(![`localhost:${settings.port}`,`127.0.0.1:${settings.port}`].includes(req.headers.host)||req.url!=='/pixels'||(req.headers.origin&&!allowed.includes(req.headers.origin))){socket.destroy();return;}
  gateway.handleUpgrade(req,socket,head,ws=>gateway.emit('connection',ws,req));
});
let checking=false;
setInterval(async()=>{if(checking||busy)return;checking=true;try{
  if(output){const r=await request(settings.routerUrl+'/api/config');if(routeDifferences(manager.bundle().config,r.config).length){lastError='Routing wurde verändert. Ausgabe automatisch gesperrt.';disarm();}}
}catch(e){lastError=e.message;if(output)disarm();}finally{checking=false;}},2000).unref();
setInterval(async()=>{if(busy||checking)return;checking=true;try{const r=await manager.verify();if(output&&r.snapshotFingerprint!==activeBundle?.sourceFingerprint){lastError='TouchDesigner-Layout verändert. Ausgabe gesperrt; neu exportieren.';disarm();}}catch(e){lastError=e.message;if(output)disarm();}finally{checking=false;}},30000).unref();
server.listen(settings.port,'127.0.0.1',()=>console.log(`PXLBLZ Manager: http://127.0.0.1:${settings.port}`));
process.on('SIGINT',()=>{disarm();server.close();process.exit(0);});
