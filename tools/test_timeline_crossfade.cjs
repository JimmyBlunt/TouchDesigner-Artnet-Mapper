/* Permanent pointer-drag acceptance against an isolated real Python backend.
 * NODE_PATH must include playwright; pass Python executable and evidence folder.
 * Browser plugin not available: use bundled Playwright, without live-show edits.
 */
const {chromium} = require('playwright');
const {spawn} = require('node:child_process');
const {createInterface} = require('node:readline');
const path = require('node:path');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const evidence = path.resolve(process.argv[3] || require('node:os').tmpdir()+'/timeline-crossfade');
fs.mkdirSync(evidence,{recursive:true});
(async()=>{
  const host = spawn(process.argv[2] || 'python',['tests/fixtures/timeline_browser_host.py'],{cwd:root,stdio:['ignore','pipe','inherit']});
  let browser;
  try {
    const url = await new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>reject(Error('Fixture startup timeout')),15000);
      createInterface({input:host.stdout}).once('line',line=>{clearTimeout(timer);resolve(JSON.parse(line).url);});
      host.once('error',reject);
    });
    browser=await chromium.launch({headless:true,channel:process.env.TIMELINE_BROWSER_CHANNEL||'msedge'});
    const page=await browser.newPage({viewport:{width:1440,height:1000}}), errors=[], warnings=[];
    page.on('pageerror',e=>errors.push(e.message));
    page.on('console',m=>{if(m.type()==='error') {
      // This app does not serve a favicon; Chromium's automatic request is
      // unrelated to timeline assets or API failures and is reported separately.
      if(m.location().url===url+'favicon.ico' && m.text().includes('404')) warnings.push('favicon.ico: 404');
      else errors.push(m.text());
    }});
    await page.goto(url);
    await page.getByRole('button',{name:'Aurora Spur 1 aufklappen'}).click();
    assert.equal(page.url(),url);
    assert.match(await page.title(),/Show Timeline/);
    await page.waitForFunction(()=>document.querySelector('[data-fade-edge="start"]'));
    const current=async()=>await (await page.request.get(url+'api/state')).json();
    let before=await current();
    async function drag(edge,dx) {
      const point=page.locator(`[data-fade-edge="${edge}"]`).first();
      await point.scrollIntoViewIfNeeded();
      const box=await point.boundingBox(), x=box.x+box.width/2,y=box.y+box.height/2;
      const response=page.waitForResponse(r=>r.url()===url+'api/command'&&r.request().method()==='POST');
      await page.mouse.move(x,y);await page.mouse.down();
      await page.mouse.move(x+dx,y,{steps:8});await page.mouse.up();
      const result=await response;assert.equal(result.status(),200);
      await page.waitForFunction(()=>!busy);
      return current();
    }
    // Lower endpoint moves earlier: 3 -> 7 seconds, clip remains 12 seconds.
    let next=await drag('start',-40);
    assert.equal(next.show.cues[0].duration,12);
    assert.equal(next.show.cues[0].transition_duration,7);
    assert.deepEqual(next.automation,before.automation);
    await page.screenshot({path:path.join(evidence,'start-extended.png')});
    // Upper endpoint moves later, keeping fade start at 5 seconds.
    next=await drag('end',30);
    assert.equal(next.show.cues[0].duration,15);
    assert.equal(next.show.cues[0].transition_duration,10);
    assert.equal(next.rows[1].start,15);
    await page.getByRole('button',{name:'Zurück',exact:false}).click();
    await page.waitForFunction(()=>!busy);
    assert.equal((await current()).show.cues[0].duration,12);
    // Cancel and click-only do not write or create extra history entries.
    const revision=(await current()).revision;
    let box=await page.locator('[data-fade-edge="start"]').first().boundingBox();
    await page.mouse.move(box.x+box.width/2,box.y+box.height/2);await page.mouse.down();
    await page.mouse.move(box.x-30,box.y+box.height/2,{steps:3});
    await page.evaluate(()=>window.dispatchEvent(new PointerEvent('pointercancel')));
    await page.mouse.up();
    await page.locator('[data-fade-edge="start"]').first().click();
    assert.equal((await current()).revision,revision);
    // Clamp start before clip zero, then recover from near-zero fade width.
    next=await drag('start',-100);
    assert.equal(next.show.cues[0].transition_duration,12);
    next=await drag('start',200);
    assert.ok(Math.abs(next.show.cues[0].transition_duration-.1)<1e-7);
    next=await drag('start',-40);
    assert.equal(next.show.cues[0].transition_duration,4);
    // Small viewport plus horizontal scrolling and changed zoom.
    await page.setViewportSize({width:900,height:850});
    await page.locator('#zoom').fill('30');await page.locator('#zoom').dispatchEvent('input');
    await page.locator('#scroll').evaluate(el=>el.scrollLeft=100);
    next=await drag('start',-30);
    assert.equal(next.show.cues[0].transition_duration,5);
    await page.screenshot({path:path.join(evidence,'scrolled-zoomed.png')});
    await page.reload();
    assert.equal((await current()).show.cues[0].transition_duration,5);
    assert.deepEqual(errors,[]);
    console.log(JSON.stringify({passed:true,url,viewports:['1440x1000','900x850'],consoleErrors:errors,warnings,
      cases:['start','end','undo','cancel','click-only','bounds','minimum-width','zoom-scroll','reload'],evidence}));
  } finally {if(browser)await browser.close();host.kill();}
})().catch(error=>{console.error(error);process.exitCode=1;});
