'use strict';
const $ = id => document.getElementById(id);
const NS = 'http://www.w3.org/2000/svg';
const colors = ['#62cecd','#9aadeb','#d9ae76','#bf96d7','#8bc696'];
let state = null, token = '', zoom = 10, expanded = new Set(), selected = null;
let busy = false, dragging = false, connected = false, pollBusy = false;
let sizes={};try{sizes=JSON.parse(localStorage.getItem('timelineSizes')||'{}');}catch{}
if(sizes.label) document.documentElement.style.setProperty('--label',sizes.label+'px');
const heightFor=(cue,name)=>sizes[cue.id+':'+(name||'head')]||(name?106:56);
const saveSizes=()=>{try{localStorage.setItem('timelineSizes',JSON.stringify(sizes));}catch{}};
const clone = value => JSON.parse(JSON.stringify(value));
const clamp = (x, lo, hi) => Math.min(hi, Math.max(lo, x));
const labelWidth = () => parseInt(getComputedStyle(document.documentElement).getPropertyValue('--label'));
const cueFor = id => state.show.cues.find(c => c.id === id);
const rowFor = id => state.rows.find(c => c.id === id);
const snap = t => {const step = Number($('snap').value); return step ? Math.round(t/step)*step : t;};
function format(t) {return `${String(Math.floor(t/60)).padStart(2,'0')}:${(t%60).toFixed(2).padStart(5,'0')}`;}
function node(tag, attrs={}, text='') {
  const el = document.createElement(tag);
  for (const [key,value] of Object.entries(attrs)) {if (key==='class') el.className=value; else el.setAttribute(key,value);}
  if (text) el.textContent=text;
  return el;
}
function svgNode(tag, attrs) {const el=document.createElementNS(NS,tag); for(const [k,v] of Object.entries(attrs)) el.setAttribute(k,v); return el;}
function message(text, error=false) {$('message').textContent=text; $('message').classList.toggle('error',error);}
function accept(next) {
  const wasConnected=connected;
  const changed = !state || (next.show && next.revision!==state.revision);
  token = next.token || token;
  state = {...state,...next};
  connected = !next.stale;
  if (changed && !dragging) {
    if(selected && !cueFor(selected.cue)) selected=null;
    render();
  }
  transport();
  midiStatus();
  if(typeof padsStatus === "function") padsStatus();
  if(!wasConnected && connected) message('Mit TouchDesigner verbunden.');
  if(next.stale) { $('connection').textContent='TouchDesigner wartet';message('TouchDesigner aktualisiert die Timeline nicht. Echtzeit-Wiedergabe in TouchDesigner prüfen.',true); }
  if(state.error) message(state.error,true);
}
async function poll() {
  if(pollBusy || busy || dragging || document.hidden) return;
  pollBusy=true;
  try {
    const response=await fetch('/api/state?revision='+(state?.revision||''),{signal:AbortSignal.timeout(4000)});
    if(!response.ok) throw Error('TouchDesigner-Verbindung unterbrochen');
    accept(await response.json());
  } catch(error) {connected=false; $('connection').textContent='Verbindung getrennt'; message(error.message,true);}
  finally {pollBusy=false;}
}
async function command(data) {
  if(busy || !state || !connected) return false;
  busy=true;
  try {
    const response=await fetch('/api/command',{method:'POST',headers:{'Content-Type':'application/json','X-Timeline-Token':token},body:JSON.stringify({...data,revision:state.revision}),signal:AbortSignal.timeout(8000)});
    const result=await response.json();
    if(!response.ok) throw Error(result.error || 'Änderung fehlgeschlagen');
    accept(result);
    message(data.action==='save' ? 'Show und Automation gespeichert.' : data.action==='midi_config'?'MIDI-Mapping gespeichert.':'Änderung übernommen.');
    return true;
  } catch(error) {message(error.message,true); if($('padsDialog').open) $('padsNotice').textContent=error.message; return false;}
  finally {busy=false; await poll();}
}
function transport() {
  if(!state) return;
  const t=state.transport;
  const time=(state.rows[t.index]?.start||0)+t.elapsed;
  $('clock').textContent=format(time);
  $('playhead').style.left=(labelWidth()+time*zoom)+'px';
  $('connection').textContent=t.recording ? 'Aufnahme läuft' : state.dirty ? 'Live · nicht gespeichert' : 'Live · gespeichert';
  $('undo').disabled=!connected || !state.undo || t.recording;
  $('redo').disabled=!connected || !state.redo || t.recording;
  $('play').disabled=!connected || t.state==='playing' || t.recording;
  $('pause').disabled=!connected || t.state!=='playing' || t.recording;
  $('stop').disabled=!connected || t.recording;
  $('save').disabled=!connected || t.recording;
  if($('follow').checked && t.state==='playing' && !dragging) {
    const viewport=$('scroll'), x=time*zoom;
    if(x<viewport.scrollLeft || x>viewport.scrollLeft+viewport.clientWidth-labelWidth()-40) viewport.scrollLeft=Math.max(0,x-80);
  }
}
function curveFor(cue, name) {
  if(name==='@transition') return clone(state.automation.transitions?.[cue.id] || {points:[[0,0],[1,1]],mode:'linear',enabled:true});
  const edit=state.automation.edits?.[cue.id]?.[name];
  if(edit) return clone(edit);
  const points=state.automation.tracks[cue.id]?.[name];
  return {points:points ? [...new Map(points)].sort((a,b)=>a[0]-b[0]) : [[0,state.parameters[cue.id][name]||0],[cue.duration,state.parameters[cue.id][name]||0]],mode:'linear',enabled:true};
}
function interpolate(points,t,mode) {
  if(t<=points[0][0]) return points[0][1];
  if(t>=points.at(-1)[0]) return points.at(-1)[1];
  let low=0,high=points.length-1;
  while(high-low>1) {const mid=(low+high)>>1;if(points[mid][0]<=t)low=mid;else high=mid;}
  {
    const [a,av]=points[low], [b,bv]=points[high]; let f=(t-a)/(b-a);
    if(mode==='step') f=0;
    if(mode==='smooth') f=f*f*(3-2*f);
    if(mode==='ease_in') f=f*f;
    if(mode==='ease_out') f=1-(1-f)**2;
    return av+(bv-av)*f;
  }
}
function geometry(cue, name, curve) {
  const transition=name==='@transition', duration=transition ? 1 : cue.duration;
  const original=state.automation.tracks[cue.id]?.[name]||[];
  const values=curve.points.concat(original).map(p=>p[1]);
  let min=Math.min(0,...values), max=Math.max(1,...values);
  if(transition) {min=0; max=1;}
  else if(max-min<.001) max=min+1;
  const width=Math.max(1,(transition ? cue.transition_duration : cue.duration)*zoom);
  const height=heightFor(cue,name), bottom=height-12, span=height-24;
  return {duration,width,min,max,height,bottom,span,x:t=>t/duration*width,y:v=>bottom-(v-min)/(max-min)*span};
}
function pathFor(points,mode,g) {
  // Sample each segment, preserving every event in dense recordings.
  const times=[0,g.duration];
  for(let i=0;i<points.length;i++) {
    const start=points[i][0], end=points[i+1]?.[0] ?? g.duration;
    if(start<=g.duration) times.push(start);
    if(mode==='step' && end>0 && end<=g.duration) times.push(end-1e-7);
    if(mode!=='linear' && mode!=='step') for(let j=1;j<12;j++) if(start+(end-start)*j/12<=g.duration) times.push(start+(end-start)*j/12);
  }
  return times.sort((a,b)=>a-b).map((t,i)=>`${i?'L':'M'}${g.x(t).toFixed(2)},${g.y(interpolate(points,t,mode)).toFixed(2)}`).join(' ');
}
function select(cue, name=null, point=null) {selected={cue,name,point}; render();}
function render() {
  if(!state) return;
  $('showName').textContent=state.show.name;
  const total=state.rows.at(-1)?.end||0;
  $('summary').textContent=`${state.show.cues.length} Clips · ${format(total)}`;
  const width=Math.max(400,total*zoom+180,$('scroll').clientWidth-labelWidth());
  $('arrangement').style.width=(width+labelWidth())+'px';
  let interval=[.5,1,2,5,10,15,30,60,120,300].find(n=>n*zoom>=65)||600;
  $('arrangement').style.setProperty('--grid',interval*zoom+'px');
  $('ticks').style.width=width+'px'; $('ticks').replaceChildren();
  renderLoop();
  for(let t=0;t<=width/zoom;t+=interval) {const tick=node('span',{class:'tick'},format(t).slice(0,-3));tick.style.left=t*zoom+'px';$('ticks').append(tick);}
  $('tracks').replaceChildren();
  if(!state.show.cues.length) $('tracks').append(node('p',{class:'empty'},'Die Show ist leer. Im Show-Editor ein Material hinzufügen oder eine Aufnahme erstellen.'));
  state.show.cues.forEach((cue,index)=>{
    const row=rowFor(cue.id), track=node('section',{class:'track','aria-label':cue.name});
    track.style.setProperty('--color',colors[index%colors.length]);
    const head=node('div',{class:'row head-row'+(heightFor(cue)<42?' compact':'')}), label=node('div',{class:'track-label track-title'+(selected?.cue===cue.id?' selected':'')});
    head.style.setProperty('--height',heightFor(cue)+'px');
    const toggle=node('button',{'aria-expanded':expanded.has(cue.id),'aria-label':`${cue.name} Spur ${index+1} aufklappen`});
    toggle.append(node('span',{class:'number'},String(index+1).padStart(2,'0')),node('span',{},expanded.has(cue.id)?'▾':'▸'));
    const title=node('span',{class:'track-name'},cue.name);title.append(node('small',{},`${cue.duration.toFixed(1)} s · ${cue.effect.startsWith('madmapper:')?'Material':'Effekt'}`));toggle.append(title);
    toggle.onclick=()=>{expanded.has(cue.id)?expanded.delete(cue.id):expanded.add(cue.id);select(cue.id);};label.append(toggle);head.append(label);
    const grid=node('div',{class:'grid'});grid.style.width=width+'px';
    const clip=node('div',{class:'clip'+(selected?.cue===cue.id?' selected':''),tabindex:'0',role:'button','aria-label':`${cue.name} Clip ${index+1}, ${cue.duration.toFixed(1)} Sekunden`});
    clip.style.left=row.start*zoom+'px';clip.style.width=Math.max(8,cue.duration*zoom)+'px';
    const fade=node('div',{class:'fade-region'});fade.style.width=cue.transition_duration*zoom+'px';
    const handle=node('div',{class:'resize',title:'Clip-Länge ändern'});
    clip.append(fade,node('span',{class:'clip-caption'},cue.name),handle);
    clip.onpointerdown=event=>clipDrag(event,cue,clip,event.target===handle);
    clip.onkeydown=e=>{if(e.key==='Enter'){expanded.add(cue.id);select(cue.id);}};
    grid.append(clip);head.append(grid);track.append(head);
    addRowResize(head,cue,null);
    if(expanded.has(cue.id)) {
      const names=[...new Set([...Object.keys(state.automation.tracks[cue.id]||{}),...Object.keys(state.automation.edits?.[cue.id]||{})])];
      for(const name of names) track.append(laneRow(cue,name,width));
      if(cue.transition!=='cut') track.append(laneRow(cue,'@transition',width));
      const add=node('div',{class:'row add-row'}), addLabel=node('div',{class:'track-label'}), dropdown=node('select',{'aria-label':`Parameter hinzufügen Spur ${index+1}`});
      dropdown.append(node('option',{value:''},'+ Parameter hinzufügen'));
      for(const name of Object.keys(state.parameters[cue.id]).filter(n=>!names.includes(n))) dropdown.append(node('option',{value:name},name));
      dropdown.onchange=async()=>{const name=dropdown.value;if(!name)return;selected={cue:cue.id,name,point:null};await setCurve(cue,name,curveFor(cue,name));};
      addLabel.append(dropdown);add.append(addLabel);track.append(add);
    }
    $('tracks').append(track);
  });
  inspector(); transport();
}
function laneRow(cue,name,width) {
  const curve=curveFor(cue,name), g=geometry(cue,name,curve), row=rowFor(cue.id), isTransition=name==='@transition';
  const active=selected?.cue===cue.id && selected.name===name;
  const container=node('div',{class:'row lane'+(active?' selected':'')+(!curve.enabled?' disabled':'')});
  container.style.setProperty('--height',g.height+'px');
  const label=node('div',{class:'track-label'}), title=node('span',{},isTransition?'Übergang · '+cue.transition:name);
  label.append(title,node('small',{},isTransition?`${cue.transition_duration.toFixed(2)} s · ${curve.mode}`:`${g.min.toFixed(2)} … ${g.max.toFixed(2)} · ${state.automation.edits?.[cue.id]?.[name]?'bearbeitet':'aufgenommen'}`));
  label.onclick=()=>select(cue.id,name);container.append(label);
  const grid=node('div',{class:'grid'});grid.style.width=width+'px';grid.style.overflow='hidden';
  const svg=svgNode('svg',{class:'curve',width:g.width,height:g.height,role:'img','aria-label':`${cue.name}: ${isTransition?'Übergang':name} Automationskurve`});
  svg.style.left=(isTransition?row.fade_start:row.start)*zoom+'px';
  svg.append(svgNode('path',{class:'baseline',d:`M0,${g.bottom} H${g.width}`}));
  const original=state.automation.tracks[cue.id]?.[name];
  if(original) svg.append(svgNode('path',{class:'original',d:pathFor(original,'linear',g)}));
  const line=svgNode('path',{d:pathFor(curve.points,curve.mode,g)});svg.append(line);
  curve.points.forEach(([time,value],i)=>{
    if(time>g.duration) return;
    const point=svgNode('circle',{class:'point'+(active&&selected.point===i?' active':''),cx:g.x(time),cy:g.y(value),r:active&&selected.point===i?5:3.5});
    const title=svgNode('title',{});title.textContent=`${isTransition?(time*cue.transition_duration).toFixed(2):time.toFixed(2)} s · ${value.toFixed(3)}`;point.append(title);
    if(isTransition && (i===0 || i===curve.points.length-1)) {
      const edge=i===0?'start':'end';
      point.dataset.fadeEdge=edge;point.style.cursor='ew-resize';
      point.setAttribute('aria-label',edge==='start'?'Überblendungsstart ziehen':'Überblendungsende und Clip-Ende ziehen');
      title.textContent=edge==='start'?'Überblendungsstart ziehen; Clip-Ende bleibt fest':'Überblendungsende ziehen; Clip-Länge wird angepasst';
    }
    point.onpointerdown=e=>pointDrag(e,cue,name,i,svg,point,line,g,curve);
    svg.append(point);
  });
  svg.ondblclick=async event=>{
    if(event.target.closest('circle') || busy) return;
    const rect=svg.getBoundingClientRect();
    let time=clamp((event.clientX-rect.left)/g.width*g.duration,0,g.duration);
    if(isTransition) time=clamp(snap(time*cue.transition_duration)/cue.transition_duration,.0001,.9999);else time=clamp(snap(time),0,cue.duration);
    let value=g.min+(g.bottom-(event.clientY-rect.top))/g.span*(g.max-g.min);
    value=clamp(value,g.min,g.max);
    const copy=clone(curve);copy.points=copy.points.filter(p=>Math.abs(p[0]-time)>1e-6);copy.points.push([time,value]);copy.points.sort((a,b)=>a[0]-b[0]);
    selected={cue:cue.id,name,point:copy.points.findIndex(p=>p[0]===time)};
    await setCurve(cue,name,copy);
  };
  grid.append(svg);container.append(grid);addRowResize(container,cue,name);return container;
}
function gesture(event,onMove,onEnd) {
  event.preventDefault();dragging=true;
  const move=e=>onMove(e), end=e=>{window.removeEventListener('pointermove',move);window.removeEventListener('pointerup',end);window.removeEventListener('pointercancel',cancel);dragging=false;onEnd(e);};
  const cancel=()=>{window.removeEventListener('pointermove',move);window.removeEventListener('pointerup',end);window.removeEventListener('pointercancel',cancel);dragging=false;render();};
  window.addEventListener('pointermove',move);window.addEventListener('pointerup',end,{once:true});window.addEventListener('pointercancel',cancel,{once:true});
}
function clipDrag(event,cue,clip,resize) {
  if(event.button!==0 || busy) return;
  const start=event.clientX, scrollStart=$('scroll').scrollLeft, row=rowFor(cue.id);
  let delta=0;
  selected={cue:cue.id,name:null,point:null};inspector();
  gesture(event,e=>{
    delta=(e.clientX-start+$('scroll').scrollLeft-scrollStart)/zoom;
    if(resize) clip.style.width=Math.max(.1,snap(cue.duration+delta))*zoom+'px';
    else clip.style.left=Math.max(0,snap(row.start+delta))*zoom+'px';
    message(resize?`Dauer: ${Math.max(.1,snap(cue.duration+delta)).toFixed(2)} s`:`Einfügeposition: ${format(Math.max(0,row.start+delta))}`);
  },async()=>{
    if(Math.abs(delta*zoom)>3) await command(resize?{action:'resize',cue:cue.id,duration:Math.max(.1,snap(cue.duration+delta))}:{action:'move',cue:cue.id,time:Math.max(0,snap(row.start+delta))});
    render();
  });
}
function pointDrag(event,cue,name,index,svg,point,line,g,curve) {
  if(event.button!==0 || busy) return;
  event.stopPropagation();
  selected={cue:cue.id,name,point:index};inspector();
  if(name==='@transition' && (index===0 || index===curve.points.length-1)) {
    return fadeEdgeDrag(event,cue,index===0?'start':'end',svg,line,curve);
  }
  const rect=svg.getBoundingClientRect(), copy=clone(curve), original=copy.points[index].slice();
  gesture(event,e=>{
    let time=(e.clientX-rect.left)/g.width*g.duration;
    time=name==='@transition'?snap(time*cue.transition_duration)/cue.transition_duration:snap(time);
    const lower=index>0?copy.points[index-1][0]+1e-5:0;
    const upper=index+1<copy.points.length?copy.points[index+1][0]-1e-5:g.duration;
    time=clamp(time,lower,Math.min(g.duration,upper));
    let value=clamp(g.min+(g.bottom-(e.clientY-rect.top))/g.span*(g.max-g.min),g.min,g.max);
    if(name==='@transition') value=clamp(value,copy.points[index-1][1],copy.points[index+1][1]);
    copy.points[index]=[time,value];
    point.setAttribute('cx',g.x(time));point.setAttribute('cy',g.y(value));line.setAttribute('d',pathFor(copy.points,copy.mode,g));
    $('pointTime').value=(name==='@transition'?time*cue.transition_duration:time).toFixed(3);$('pointValue').value=value.toFixed(4);
  },async()=>{if(JSON.stringify(original)!==JSON.stringify(copy.points[index])) await setCurve(cue,name,copy);render();});
}
function fadeEdgeDrag(event,cue,edge,svg,line,curve) {
  const startX=event.clientX, scrollStart=$('scroll').scrollLeft, row=rowFor(cue.id);
  const fadeStart=cue.duration-cue.transition_duration;
  const initial=edge==='start'?fadeStart:cue.duration;
  let moment=initial, distance=0;
  gesture(event,e=>{
    distance=e.clientX-startX+$('scroll').scrollLeft-scrollStart;
    moment=snap(initial+distance/zoom);
    moment=edge==='start'?clamp(moment,0,cue.duration-.1):Math.max(fadeStart+.1,moment);
    const start=edge==='start'?moment:fadeStart, end=edge==='end'?moment:cue.duration;
    const preview={...cue,duration:end,transition_duration:end-start}, shape=geometry(preview,'@transition',curve);
    svg.style.left=(row.start+start)*zoom+'px';svg.setAttribute('width',shape.width);
    line.setAttribute('d',pathFor(curve.points,curve.mode,shape));
    svg.querySelector('.baseline').setAttribute('d',`M0,${shape.bottom} H${shape.width}`);
    svg.querySelectorAll('circle').forEach((circle,i)=>circle.setAttribute('cx',shape.x(curve.points[i][0])));
    const clip=svg.closest('.track').querySelector('.clip');
    clip.style.width=Math.max(8,end*zoom)+'px';
    clip.querySelector('.fade-region').style.width=(end-start)*zoom+'px';
    $('fadeDuration').value=(end-start).toFixed(3);$('duration').value=end.toFixed(3);
    message(`Überblendung: ${(end-start).toFixed(2)} s · Clip: ${end.toFixed(2)} s`);
  },async()=>{
    if(Math.abs(distance)>3 && Math.abs(moment-initial)>1e-7) {
      await command({action:'transition',cue:cue.id,edge,time:moment});
    }
    render();
  });
}
async function setCurve(cue,name,curve) {
  return command(name==='@transition'?{action:'transition',cue:cue.id,curve}:{action:'lane',cue:cue.id,parameter:name,curve});
}
function inspector() {
  const cue=selected && cueFor(selected.cue);
  $('clipForm').hidden=!cue;$('pointForm').hidden=!cue || !selected.name;
  $('selectionTitle').textContent=cue?.name||'Clip auswählen';
  $('selectionHint').textContent=cue ? `${format(rowFor(cue.id).start)} – ${format(rowFor(cue.id).end)}` : 'Eine Spur öffnen, um aufgezeichnete Parameter und Übergänge zu bearbeiten.';
  if(!cue) return;
  $('duration').value=cue.duration;
  $('transitionKind').replaceChildren(...state.transitions.map(item=>node('option',{value:item.value},item.label)));
  $('transitionKind').value=cue.transition;$('fadeDuration').value=cue.transition_duration;
  if(!selected.name) return;
  const curve=curveFor(cue,selected.name), point=curve.points[selected.point], transition=selected.name==='@transition';
  $('interpolation').value=curve.mode;$('override').checked=curve.enabled;
  $('pointFields').hidden=!point;
  if(point) {$('pointTime').value=transition?point[0]*cue.transition_duration:point[0];$('pointValue').value=point[1];}
  const endpoint=transition && (selected.point===0 || selected.point===curve.points.length-1);
  $('pointTime').disabled=endpoint;$('pointValue').disabled=endpoint;
  $('deletePoint').disabled=endpoint || curve.points.length<=1;
  $('pointForm').querySelector('button[type=submit]').disabled=endpoint;
}
async function deletePoint() {
  if(!selected?.name || selected.point===null) return;
  const cue=cueFor(selected.cue), curve=curveFor(cue,selected.name);
  if(curve.points.length<=1 || (selected.name==='@transition' && [0,curve.points.length-1].includes(selected.point))) return;
  curve.points.splice(selected.point,1);selected.point=null;await setCurve(cue,selected.name,curve);
}
for(const action of ['play','pause','stop','save','undo','redo']) $(action).onclick=()=>command({action});
$('zoom').oninput=()=>{const old=zoom;zoom=Number($('zoom').value);$('scroll').scrollLeft*=zoom/old;render();};
$('fit').onclick=()=>{zoom=clamp(($('scroll').clientWidth-labelWidth()-30)/(state?.rows.at(-1)?.end||60),.25,120);$('zoom').value=zoom;$('scroll').scrollLeft=0;render();};
$('ticks').onclick=e=>command({action:'seek',time:Math.max(0,snap((e.clientX-$('ticks').getBoundingClientRect().left)/zoom))});
$('clipForm').onsubmit=e=>{e.preventDefault();command({action:'resize',cue:selected.cue,duration:Number($('duration').value)});};
$('applyFade').onclick=()=>command({action:'transition',cue:selected.cue,kind:$('transitionKind').value,duration:Number($('fadeDuration').value)});
$('pointForm').onsubmit=async e=>{
  e.preventDefault(); const cue=cueFor(selected.cue), curve=curveFor(cue,selected.name), transition=selected.name==='@transition';
  let time=Number($('pointTime').value)/(transition?cue.transition_duration:1), value=Number($('pointValue').value);
  if(time<0 || time>(transition?1:cue.duration)) return message('Punktzeit muss innerhalb des Clips liegen.',true);
  if(curve.points.some((p,i)=>i!==selected.point&&Math.abs(p[0]-time)<1e-7)) return message('An dieser Zeit existiert bereits ein Punkt.',true);
  curve.points[selected.point]=[time,value];curve.points.sort((a,b)=>a[0]-b[0]);selected.point=curve.points.findIndex(p=>p[0]===time);await setCurve(cue,selected.name,curve);
};
for(const id of ['interpolation','override']) $(id).onchange=()=>{const cue=cueFor(selected.cue), curve=curveFor(cue,selected.name);curve.mode=$('interpolation').value;curve.enabled=$('override').checked;setCurve(cue,selected.name,curve);};
$('deletePoint').onclick=deletePoint;
$('resetLane').onclick=()=>{selected.point=null;if(selected.name==='@transition') setCurve(cueFor(selected.cue),selected.name,{points:[[0,0],[1,1]],mode:'linear',enabled:true});else command({action:'reset_lane',cue:selected.cue,parameter:selected.name});};
window.onkeydown=e=>{
  if($('midiDialog').open || $('padsDialog').open) return;
  if(e.target.matches('input,select,textarea')) return;
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='z') {e.preventDefault();command({action:e.shiftKey?'redo':'undo'});}
  if(e.code==='Space') {e.preventDefault();command({action:state?.transport.state==='playing'?'pause':'play'});}
  if(e.key==='Delete'||e.key==='Backspace'){e.preventDefault();deletePoint();}
};
window.addEventListener('resize',()=>{if(!dragging)render();});

function addRowResize(row,cue,name) {
  const handle=node('div',{class:'row-resize',title:'Spurhöhe ziehen (bis zur halben Höhe)',role:'separator','aria-label':`${cue.name} ${name||'Spur'} Höhe ändern`});
  handle.onpointerdown=e=>{
    if(e.button!==0)return;e.stopPropagation();
    const y=e.clientY,initial=heightFor(cue,name),key=cue.id+':'+(name||'head');
    gesture(e,move=>{sizes[key]=clamp(initial+move.clientY-y,name?53:28,320);render();},()=>{saveSizes();render();});
  };row.append(handle);
}
$('labelResize').onpointerdown=e=>{
  if(e.button!==0)return;const x=e.clientX,initial=labelWidth();
  gesture(e,move=>{sizes.label=clamp(initial+move.clientX-x,100,420);document.documentElement.style.setProperty('--label',sizes.label+'px');render();},()=>{saveSizes();render();});
};
function wheelZoom(e) {
  if(!state || dragging)return;e.preventDefault();
  const scroll=$('scroll'),offset=e.clientX-scroll.getBoundingClientRect().left-labelWidth();
  const anchor=(scroll.scrollLeft+offset)/zoom;
  zoom=clamp(zoom*Math.exp(-e.deltaY*(e.deltaMode===1?.035:.002)),.25,120);
  $('zoom').value=zoom;render();scroll.scrollLeft=Math.max(0,anchor*zoom-offset);
}
$('ticks').addEventListener('wheel',wheelZoom,{passive:false});
$('loopGrid').addEventListener('wheel',wheelZoom,{passive:false});
$('zoom').step=.05;$('zoom').min=.25;$('zoom').value=zoom;
function loopRegion(){return clone(state.automation.loop_region||{start:0,end:state.rows.at(-1)?.end||1,enabled:false});}
function drawLoop(region){
  const total=state.rows.at(-1)?.end||1;
  const start=clamp(region.start,0,total),end=clamp(region.end,start,total);
  $('loopRange').style.left=start*zoom+'px';$('loopRange').style.width=(end-start)*zoom+'px';
  $('loopRange').classList.toggle('enabled',region.enabled);
  $('loopCaption').textContent=`${format(start)} – ${format(end)}`;
}
function renderLoop(){
  const region=loopRegion();drawLoop(region);
  if(!['loopStart','loopEnd','loopEnabled'].includes(document.activeElement?.id)){
    $('loopStart').value=Number(region.start.toFixed(3));$('loopEnd').value=Number(Math.min(region.end,state.rows.at(-1)?.end||1).toFixed(3));$('loopEnabled').checked=region.enabled;
  }
}
const commitLoop=region=>command({action:'loop',...region});
$('applyLoop').onclick=()=>commitLoop({start:Number($('loopStart').value),end:Number($('loopEnd').value),enabled:$('loopEnabled').checked});
$('loopEnabled').onchange=()=>commitLoop({...loopRegion(),end:Math.min(loopRegion().end,state.rows.at(-1)?.end||1),enabled:$('loopEnabled').checked});
$('loopAll').onclick=()=>commitLoop({start:0,end:state.rows.at(-1)?.end||1,enabled:$('loopEnabled').checked});
$('loopGrid').onpointerdown=e=>{
  if(e.button!==0 || busy || !state?.show.cues.length)return;
  const initial=loopRegion(),total=state.rows.at(-1).end;
  initial.end=Math.min(initial.end,total);initial.start=Math.min(initial.start,initial.end-.01);
  const x=e.clientX,rect=$('loopGrid').getBoundingClientRect(),start=clamp(snap((x-rect.left)/zoom),0,total);
  const kind=e.target.id==='loopLeft'?'start':e.target.id==='loopRight'?'end':e.target.closest('#loopRange')?'move':'new';
  let region=clone(initial),moved=false;
  gesture(e,move=>{
    moved=true;const delta=snap((move.clientX-x)/zoom);
    if(kind==='start')region.start=clamp(initial.start+delta,0,initial.end-.01);
    if(kind==='end')region.end=clamp(initial.end+delta,initial.start+.01,total);
    if(kind==='move'){const length=initial.end-initial.start;region.start=clamp(initial.start+delta,0,total-length);region.end=region.start+length;}
    if(kind==='new'){const end=clamp(snap((move.clientX-rect.left)/zoom),0,total);region.start=Math.min(start,end);region.end=Math.max(start,end);}
    drawLoop(region);$('loopStart').value=region.start.toFixed(2);$('loopEnd').value=region.end.toFixed(2);
  },async()=>{if(moved&&region.end>region.start)await commitLoop(region);renderLoop();});
};
let midiRevision=null,midiDevices='';
const actionLabels={'@play':'▶ Play','@pause':'Ⅱ Pause','@stop':'■ Stopp','@previous':'Vorheriger Clip','@next':'Nächster Clip','@record':'Aufnahme an/aus','@loop':'Loop an/aus','@release':'Live-Werte freigeben'};
function midiStatus(){
  const midi=state?.midi;if(!$('midiDialog').open)return;
  if(!midi){$('midiStatus').textContent='MIDI ist in dieser Vorschau nicht verfügbar.';return;}
  const devices=JSON.stringify(midi.devices);
  if(devices!==midiDevices){midiDevices=devices;const current=$('midiDevice').value||midi.config.device;$('midiDevice').replaceChildren(node('option',{value:''},'MIDI-Eingang wählen'),...midi.devices.map(n=>node('option',{value:n},n)));if(current&&!midi.devices.includes(current))$('midiDevice').append(node('option',{value:current},current+' (getrennt)'));$('midiDevice').value=current;}
  if(midiRevision!==midi.revision){midiRevision=midi.revision;renderMidi(midi.config);}
  $('midiStatus').textContent=midi.error|| (midi.learning!==null?`${midi.config.bindings[midi.learning].label}: Regler bewegen oder Pad drücken …`:midi.devices.length?(midi.last||'Bereit zum Lernen.'):'Kein MIDI-Eingang erkannt. Controller anschließen und MIDI-Modus aktivieren.');
}
function renderMidi(config){
  $('midiEnabled').checked=config.enabled;$('midiDevice').value=config.device;
  const parameters=[...new Set(Object.values(state.parameters).flatMap(p=>Object.keys(p)))];
  $('midiBindings').replaceChildren(...config.bindings.map((binding,index)=>{
    const row=node('tr'),target=node('select',{'aria-label':binding.label+' Ziel'});
    const choices=[...new Set([binding.target,...parameters,...Object.keys(actionLabels)])];
    target.append(...choices.map(x=>node('option',{value:x},actionLabels[x]||x)));target.value=binding.target;
    const min=node('input',{type:'number',step:'any',value:binding.minimum,'aria-label':binding.label+' Minimum'}),max=node('input',{type:'number',step:'any',value:binding.maximum,'aria-label':binding.label+' Maximum'});
    const mode=node('select',{'aria-label':binding.label+' Modus'});mode.append(...[['absolute','Absolut 0–127'],['relative_twos','Relativ ± (1/127)'],['relative_offset','Relativ um 64']].map(([v,t])=>node('option',{value:v},t)));mode.value=binding.mode;
    const learn=node('button',{},'Lernen');learn.onclick=async()=>{if(await saveMidi())await command({action:'midi_learn',index});};
    const source=binding.source;
    for(const content of [binding.label,target,min,max,mode,source?`${source.kind.toUpperCase()} ${source.number} · Ch ${source.channel}`:'Nicht gelernt',learn]){const cell=node('td');cell.append(typeof content==='string'?document.createTextNode(content):content);row.append(cell);}
    return row;
  }));
}
async function saveMidi(){
  if(!state.midi)return false;
  const config=clone(state.midi.config);config.device=$('midiDevice').value;config.enabled=$('midiEnabled').checked;
  [...$('midiBindings').children].forEach((row,i)=>{const selects=row.querySelectorAll('select'),inputs=row.querySelectorAll('input');Object.assign(config.bindings[i],{target:selects[0].value,minimum:Number(inputs[0].value),maximum:Number(inputs[1].value),mode:selects[1].value});});
  return command({action:'midi_config',config,midi_revision:state.midi.revision});
}
$('midiOpen').onclick=()=>{midiRevision=null;midiDevices='';$('midiDialog').showModal();midiStatus();};
$('midiClose').onclick=()=>{$('midiDialog').close();command({action:'midi_learn',index:null});};
$('midiDialog').addEventListener('cancel',()=>command({action:'midi_learn',index:null}));
$('midiSave').onclick=saveMidi;
$('midiRelease').onclick=()=>command({action:'midi_release'});
$('midiCancel').onclick=()=>command({action:'midi_learn',index:null});
poll();setInterval(poll,200);
