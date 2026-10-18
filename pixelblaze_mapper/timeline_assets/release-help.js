/* Read-only contextual help. No transport, MIDI or network-output commands. */
(() => {
  'use strict';
  function text(tag, value) { const node=document.createElement(tag);node.textContent=value;return node; }
  const targets=[['sequencer','header .save'],['mk2','#padsDialog .dialogHead'],['midi','#midiDialog .dialogHead']];
  fetch('/release-help/catalog.json').then(response=>{if(!response.ok)throw Error('Help catalog unavailable');return response.json();}).then(catalog=>{
    for(const [key,selector] of targets){
      const screen=catalog.screens.find(item=>item.key===key);
      const parent=document.querySelector(selector);
      if(!screen||!parent)continue;
      const button=text('button','i  Info / How-to');
      button.type='button';button.className='release-help-trigger';button.title=screen.summary;button.setAttribute('aria-label','Hilfe: '+screen.title);
      const dialog=document.createElement('dialog');dialog.className='release-help-popover';
      const close=text('button','Schließen');close.type='button';close.className='release-help-close';close.onclick=()=>dialog.close();
      dialog.append(close,text('h2',screen.title),text('p',screen.summary));
      const list=document.createElement('ol');for(const step of screen.steps||[])list.append(text('li',step));dialog.append(list);
      const link=text('a','Ausführliches How-to mit Beispiel öffnen →');link.href='/release-help/'+screen.howto;link.target='_blank';link.rel='noopener';dialog.append(link);
      document.body.append(dialog);parent.append(button);button.onclick=()=>dialog.showModal();
      for(const [id,field] of Object.entries(screen.fields||{})){
        const input=document.getElementById(id);if(input)input.title=field.description+' Beispiel: '+field.example;
      }
    }
  }).catch(error=>console.warn('Release help:',error.message));
})();
