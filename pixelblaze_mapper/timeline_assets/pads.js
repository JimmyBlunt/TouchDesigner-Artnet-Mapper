'use strict';
let padCatalog=[],padViewKey='',padFrameKey='',padEditIndex=-1,padEditVersion=-1;
const padOrder=[12,13,14,15,8,9,10,11,4,5,6,7,0,1,2,3];
function padPreviewImage(imageId){
  const source='/api/pad_image?id='+encodeURIComponent(imageId);
  const image=node('img',{src:source,alt:'',loading:'lazy'});
  let retried=false;
  image.onload=()=>{image.onload=null;image.onerror=null;};
  image.onerror=()=>{
    if(!retried){retried=true;image.src=source+'&retry=1';return;}
    image.onload=null;image.onerror=null;
    image.replaceWith(node('span',{class:'padPlaceholder',role:'img','aria-label':'Kein Vorschaubild verfügbar'},'Kein Bild'));
  };
  return image;
}
function padTargets(){
  const kind=$('padKind').value,search=$('padSearch').value.toLocaleLowerCase();
  const current=state.pads.config.pads[state.pads.selected];
  const choices=padCatalog.filter(c=>c.kind===kind && (!search || c.label.toLocaleLowerCase().includes(search)));
  const select=$('padTarget');
  select.replaceChildren(node('option',{value:''},'— Pad leeren —'),...choices.map(c=>node('option',{value:c.id},c.label)));
  if(current.kind===kind && choices.some(c=>c.id===current.target)) select.value=current.target;
  else if(search && choices.length) select.value=choices[0].id;
}
function padsStatus(){
  if(!$('padsDialog').open) return;
  const pads=state?.pads;
  if(!pads){$('padsStatus').textContent='Material-Pads werden initialisiert …';return;}
  $('padsStatus').textContent=pads.status;
  $('padHardware').checked=pads.config.hardware;
  const banks=pads.groups||[{name:'A',count:0}];
  if($('padBank').options.length!==banks.length) $('padBank').replaceChildren(...banks.map((g,i)=>node('option',{value:i},g.name)));
  [...$('padBank').options].forEach((o,i)=>{o.textContent=banks[i].name+' · '+banks[i].count+' / 16';});
  $('padBank').value=pads.bank||0;
  $('controllerMode').textContent=pads.controller ? (pads.controller.mode==='show'?'STEP an · Show Mode':'STEP aus · Material Mode') : '';
  const screens={home:'Aktives Material',browse:'Material-Browser',pad_grid:'Pad-Übersicht',pad_menu:'Pad-Menü',pad_edit:'Preset bearbeiten',confirm_edit:'Preset speichern?',confirm_assign:'Zuordnung bestätigen',confirm_delete:'Zuordnung löschen?'};
  $('controllerScreen').textContent=pads.controller ? (screens[pads.controller.screen]||pads.controller.screen)+' · v'+pads.release : '';
  $('padTrigger').disabled=!pads.cards[pads.selected].available || state.transport.recording;
  $('padsNotice').textContent=pads.error || pads.last || '';
  const key=JSON.stringify([pads.cards,pads.selected,pads.bank]);
  if(key!==padViewKey){
    padViewKey=key;
    $('padGrid').replaceChildren(...padOrder.map(index=>{
      const card=pads.cards[index],button=node('button',{class:'materialPad'+(index===pads.selected?' chosen':''),'aria-label':`Pad ${index+1}: ${card.label}`,'aria-pressed':String(index===pads.selected)});
      button.append(node('span',{class:'padBadge'},String(index+1).padStart(2,'0')));
      if(card.image) button.append(padPreviewImage(card.image));
      else button.append(node('span',{class:'padPlaceholder'},card.target?'?':'+'));
      button.append(node('span',{class:'padLabel'},card.label));
      button.onclick=()=>command({action:'pad_select',index});
      return button;
    }));
    $('padNumber').textContent='PAD '+String(pads.selected+1).padStart(2,'0');
    $('padName').textContent=pads.cards[pads.selected].label;
    $('padTrigger').textContent=pads.cards[pads.selected].kind==='cue'?'Show-Clip starten':'Material laden';
    $('padTrigger').disabled=!pads.cards[pads.selected].available || state.transport.recording;
  }
  if(padEditIndex!==pads.selected || padEditVersion!==pads.version){
    padEditIndex=pads.selected;padEditVersion=pads.version;
    $('padKind').value=pads.config.pads[pads.selected].kind;$('padSearch').value='';padTargets();
  }
  const frameKey=pads.frame_version+':'+pads.config.hardware;
  $('padDisplays').hidden=!pads.config.hardware || !pads.frame_version;
  if(frameKey!==padFrameKey && pads.frame_version){
    padFrameKey=frameKey;
    $('padDisplayLeft').src='/api/pad_display?side=0&v='+pads.frame_version;
    $('padDisplayRight').src='/api/pad_display?side=1&v='+pads.frame_version;
  }
}
$('padsOpen').onclick=async()=>{
  $('padsDialog').showModal();padViewKey='';padEditIndex=-1;padFrameKey='';
  try{const response=await fetch('/api/pad_catalog',{signal:AbortSignal.timeout(4000)});if(!response.ok)throw Error('Materialliste nicht erreichbar');padCatalog=(await response.json()).items;padEditIndex=-1;padsStatus();}
  catch(error){$('padsNotice').textContent=error.message;}
};
$('padsClose').onclick=()=>$('padsDialog').close();
$('padKind').onchange=padTargets;
$('padSearch').oninput=padTargets;
$('padAssign').onclick=async()=>{
  const pads=state.pads,config=clone(pads.config);
  config.pads[pads.selected]={kind:$('padKind').value,target:$('padTarget').value};
  if(await command({action:'pads_config',config,pads_version:pads.version})) $('padsNotice').textContent='Pad-Zuweisung gespeichert.';
};
$('padHardware').onchange=async()=>{
  const pads=state.pads,config={...clone(pads.config),hardware:$('padHardware').checked};
  await command({action:'pads_config',config,pads_version:pads.version});padsStatus();
};
$('padTrigger').onclick=()=>command({action:'pad_trigger',index:state.pads.selected,pads_version:state.pads.version});

$('padBank').onchange=()=>command({action:'pads_bank',bank:Number($('padBank').value),pads_version:state.pads.version});
