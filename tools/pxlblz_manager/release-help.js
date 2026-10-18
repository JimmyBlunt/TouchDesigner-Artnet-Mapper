/* Read-only contextual help; never invokes manager actions. */
fetch('/release-help/catalog.json').then(r=>r.json()).then(catalog=>{
 const screen=catalog.screens.find(s=>s.key==='pxlblz_manager');if(!screen)return;
 const button=document.createElement('button');button.textContent='i  Info / How-to';button.title=screen.summary;button.type='button';
 const dialog=document.createElement('dialog');dialog.className='release-help';
 const add=(tag,value)=>{const n=document.createElement(tag);n.textContent=value;return n;};
 const close=add('button','Schließen');close.onclick=()=>dialog.close();dialog.append(close,add('h2',screen.title),add('p',screen.summary));
 const list=document.createElement('ol');for(const step of screen.steps||[])list.append(add('li',step));dialog.append(list);
 const link=add('a','Ausführliches How-to mit Beispiel öffnen');link.href='/release-help/'+screen.howto;link.target='_blank';link.rel='noopener';dialog.append(link);
 document.body.append(dialog);document.querySelector('header').append(button);button.onclick=()=>dialog.showModal();
 for(const [id,field]of Object.entries(screen.fields||{})){const input=document.getElementById(id);if(input)input.title=field.description+' Beispiel: '+field.example;}
}).catch(error=>console.warn('Hilfe konnte nicht geladen werden:',error.message));
