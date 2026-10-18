import assert from 'node:assert/strict';
const median=v=>{const s=[...v].sort((a,b)=>a-b);return s[Math.floor(s.length/2)];};
const extent=(points,a)=>Math.max(...points.map(p=>p[a]))-Math.min(...points.map(p=>p[a]));

// Installation convention verified from the active scene: X=height;
// rear panels lie in XZ, side panels lie in XY. Unfold both around their hinge.
export function surfaceMap(bundle) {
  const groups=bundle.objects.map(o=>({object:o,points:bundle.world.filter(w=>w.object_id===o.id)}));
  const rear=[],side=[];
  for(const g of groups){
    const p=g.points.map(w=>w.point),span=[0,1,2].map(a=>extent(p,a));
    if(span[1]<Math.min(span[0],span[2])*.12)rear.push(g);
    else if(span[2]<Math.min(span[0],span[1])*.2)side.push(g);
    else throw Error(`Flächenausrichtung unklar: ${g.object.name}`);
  }
  assert(rear.length&&side.length,'Rückwand und Seitenfläche erforderlich');
  const hingeY=median(rear.flatMap(g=>g.points.map(w=>w.point[1])));
  const hingeZ=median(side.flatMap(g=>g.points.map(w=>w.point[2])));
  const raw=new Map();
  for(const g of rear)for(const w of g.points)raw.set(w.index,[w.point[2]-hingeZ,w.point[0]]);
  for(const g of side)for(const w of g.points)raw.set(w.index,[w.point[1]-hingeY,w.point[0]]);
  const values=[...raw.values()],mins=[0,1].map(a=>Math.min(...values.map(p=>p[a])));
  const spans=[0,1].map(a=>extent(values,a));assert(spans.every(v=>v>0),'Entartete Fläche');
  // Fill the pattern domain; no source index is compacted or reordered.
  const uv=p=>p.map((v,a)=>(v-mins[a])/spans[a]);
  const anchor=uv(values[0]);
  const points=bundle.coordinates.map((_,i)=>raw.has(i)?uv(raw.get(i)):[...anchor]);
  const panels=groups.map(g=>{const p=g.points.map(w=>points[w.index]);const spans=[0,1].map(a=>extent(p,a));
    assert(spans.every(v=>v>.02),`Fläche kollabiert: ${g.object.name}`);
    return {name:g.object.name,count:p.length,span:spans};});
  return {points,report:{projection:'surface-fill',hingeY,hingeZ,physicalExtent:spans,rearPanels:rear.length,sidePanels:side.length,panels,
    note:'Zusammenhängende abgewickelte Fläche. U läuft von der Seite über die Faltkante zur Rückwand; V ist die Höhe. Fill bildet die gesamte Fläche auf 0..1 ab.'}};
}

export function diagnosticPattern(bundle){
  const routed=new Set();for(const r of bundle.config.routes.filter(r=>r.enabled))for(let i=r.pixel_start;i<r.pixel_start+r.pixel_count;i++)if(bundle.mask[i])routed.add(i);
  const spans=[];for(let i=0;i<bundle.mask.length;i++)if(routed.has(i)){const start=i;while(routed.has(i+1))i++;spans.push([start,i]);}
  const enabled=spans.map(([a,b])=>a===b?`index == ${a}`:`(index >= ${a} && index <= ${b})`).join(' || ');
  return `// Continuous 2D trail on the unfolded cabinet surface. Inactive/unrouted slots stay black.\nvar clock = 0\nexport function beforeRender(delta) { clock += delta / 1000 }\nexport function render2D(index, x, y) {\n  if (!(${enabled})) { rgb(0,0,0); return }\n  var glow = 0\n  for (var j=0; j<24; j++) {\n    var t = clock * 0.7 - j * 0.045\n    var dx = x - (0.5 + 0.34*sin(t))\n    var dy = y - (0.5 + 0.34*sin(t*1.31+0.7))\n    var v = exp(-(dx*dx+dy*dy)/0.0018) * (1-j/24)\n    glow = max(glow,v)\n  }\n  hsv(0.16,0.95,glow*0.45)\n}\n`;
}
