/* Read-only live timeline acceptance. Browser plugin absent; bundled Playwright + Chrome. */
const {chromium}=require('playwright');
const fs=require('fs');
const path=require('path');
(async()=>{
 const root=path.resolve(__dirname,'../docs/release-v1.0.0');
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const report={browser:'Playwright Chrome (Browser plugin not available)',checks:[],errors:[]};
 page.on('pageerror',e=>report.errors.push(String(e)));
 page.on('response',r=>{if(r.status()>=400)report.errors.push(r.status()+' '+r.url());});
 page.on('console',m=>{if(m.type()==='error'||m.type()==='warning')report.errors.push(m.text()+' '+m.location().url);});
 try {
  await page.goto('http://127.0.0.1:9991/',{waitUntil:'domcontentloaded'});
  await page.locator('#showName').filter({hasText:'Test1'}).waitFor();
  report.title=await page.title();report.url=page.url();
  report.checks.push('live Test1 show rendered');
  await page.getByRole('button',{name:'Hilfe: Sequencer & Timeline'}).click();
  await page.locator('dialog.release-help-popover[open]').waitFor();
  report.checks.push('timeline contextual info opens');
  await page.locator('dialog.release-help-popover[open]').getByRole('button',{name:'Schließen'}).click();
  await page.locator('#snap').selectOption('1');
  await page.locator('#fit').click();
  report.checks.push('snap and fit controls respond');
  await page.screenshot({path:path.join(root,'screenshots/sequencer.png'),fullPage:true});
  for(const [key,button,dialog] of [['mk2','#padsOpen','#padsDialog'],['midi','#midiOpen','#midiDialog']]){
   await page.locator(button).click();await page.locator(dialog+'[open]').waitFor();
   await page.screenshot({path:path.join(root,'screenshots/'+key+'.png'),fullPage:true});
   await page.locator(dialog+' .release-help-trigger').click();
   await page.locator('dialog.release-help-popover[open]').waitFor();
   await page.locator('dialog.release-help-popover[open]').getByRole('button',{name:'Schließen'}).click();
   await page.locator(dialog).getByRole('button',{name:'Schließen',exact:true}).click();
   report.checks.push(key+' dialog and contextual help open/close');
  }
  report.style=await page.locator('body').evaluate(el=>({font:getComputedStyle(el).fontFamily,background:getComputedStyle(el).backgroundColor,color:getComputedStyle(el).color}));
  await page.setViewportSize({width:900,height:700});
  await page.screenshot({path:path.join(root,'screenshots/sequencer-compact.png'),fullPage:true});
  report.checks.push('compact desktop screenshot captured');
  const response=await page.goto('http://127.0.0.1:9991/release-help/sequencer.html');
  if(response.status()!==200)throw Error('Guide not served: '+response.status());
  report.checks.push('detailed sequencer guide served');
  await page.screenshot({path:path.join(root,'screenshots/guide-sequencer.png'),fullPage:true});
  if(process.argv.includes('--manager')){
   await page.setViewportSize({width:1440,height:1000});
   await page.goto('http://127.0.0.1:9990/',{waitUntil:'domcontentloaded'});
   await page.getByRole('button',{name:'i  Info / How-to',exact:true}).click();
   await page.locator('dialog.release-help[open]').waitFor();
   await page.locator('dialog.release-help').getByRole('button',{name:'Schließen'}).click();
   await page.screenshot({path:path.join(root,'screenshots/pxlblz_manager.png'),fullPage:true});
   const managerState=await page.request.get('http://127.0.0.1:9990/api/state').then(r=>r.json());
   if(managerState.output)throw Error('Manager output unexpectedly active');
   report.manager={output:false,lastError:managerState.lastError};
   report.checks.push('PXLBLZ Manager information opens/closes; output off');
  }
 } catch(e){ report.failure=String(e);throw e; }
 finally {fs.writeFileSync(path.join(root,'qa/browser-qa.json'),JSON.stringify(report,null,2));await browser.close();}
 console.log(JSON.stringify(report,null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
