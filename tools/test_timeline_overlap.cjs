/* Permanent browser acceptance against isolated real Python Bridge+timeline.
 * Browser plugin not available: bundled Playwright; no live TouchDesigner edits.
 * Flow: legacy timeline -> explicit overlap migration -> independent fade grips
 * and inspector -> actual shifted clips, undo/save/reload, desktop+small viewport.
 */
const {chromium}=require('playwright');
const {spawn}=require('node:child_process');
const {createInterface}=require('node:readline');
const path=require('node:path'),fs=require('node:fs'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
const evidence=path.resolve(process.argv[3]||require('node:os').tmpdir()+'/timeline-overlap');
fs.mkdirSync(evidence,{recursive:true});
(async()=>{
  const host=spawn(process.argv[2]||'python',['tests/fixtures/timeline_browser_host.py'],{cwd:root,stdio:['ignore','pipe','inherit']});
  let browser;
  try {
    const url=await new Promise((resolve,reject)=>{
      const timer=setTimeout(()=>reject(Error('Fixture startup timeout')),15000);
      createInterface({input:host.stdout}).once('line',line=>{clearTimeout(timer);resolve(JSON.parse(line).url);});
      host.once('error',reject);
    });
    browser=await chromium.launch({headless:true,channel:process.env.TIMELINE_BROWSER_CHANNEL||'msedge'});
    const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];
    page.on('pageerror',error=>errors.push(error.message));
    page.on('console',m=>{if(m.type()==='error' && !m.location().url.endsWith('/favicon.ico'))errors.push(m.text());});
    await page.goto(url);
    await page.getByRole('button',{name:'Aurora Spur 1 aufklappen'}).click();
    assert.equal(page.url(),url);assert.match(await page.title(),/Show Timeline/);
    const current=async()=>await(await page.request.get(url+'api/state')).json();
    async function mutate(action){
      const response=page.waitForResponse(r=>r.url()===url+'api/command'&&r.request().method()==='POST');
      await action();assert.equal((await response).status(),200);
      await page.waitForFunction(()=>!busy);return current();
    }
    // Existing transition automation remains stored and editable in legacy.
    await mutate(()=>page.evaluate(()=>command({action:'transition',cue:state.show.cues[0].id,
      curve:{points:[[0,0],[.5,.3],[1,1]],mode:'smooth',enabled:true}})));
    assert.equal(await page.getByRole('img',{name:'Aurora: Übergang Automationskurve'}).locator('circle').count(),3);
    const before=await current();
    page.once('dialog',dialog=>dialog.dismiss());
    await page.locator('#enableOverlap').click();
    assert.equal((await current()).revision,before.revision);
    page.once('dialog',dialog=>dialog.accept());
    let state=await mutate(()=>page.locator('#enableOverlap').click());
    assert.equal(state.show.timing_mode,'overlap');assert.deepEqual(state.rows.map(r=>r.start),[0,9,18]);
    assert.deepEqual(state.automation.tracks,before.automation.tracks);
    assert.equal(await page.locator('.clip').nth(1).evaluate(el=>el.style.left),'90px');
    assert.equal(await page.locator('#clipFades').isVisible(),true);
    const durationLane=page.getByRole('img',{name:'Aurora: Überlappungsdauer, zwei Zeitgriffe'});
    assert.equal(await durationLane.locator('circle').count(),2);
    await page.getByText('Überlappungsdauer',{exact:true}).click();
    assert.equal(await page.locator('#pointForm').isVisible(),false);
    let span=await durationLane.boundingBox();
    const durationRevision=(await current()).revision;
    await page.mouse.dblclick(span.x+span.width/2,span.y+span.height/2);
    assert.equal((await current()).revision,durationRevision);
    // Duration endpoints remain functional despite hiding meaningless curves.
    let edge=await durationLane.locator('[data-fade-edge="start"]').boundingBox();
    state=await mutate(async()=>{await page.mouse.move(edge.x+edge.width/2,edge.y+edge.height/2);
      await page.mouse.down();await page.mouse.move(edge.x+edge.width/2-10,edge.y+edge.height/2);await page.mouse.up();});
    assert.equal(state.show.cues[0].transition_duration,4);
    await mutate(()=>page.locator('#undo').click());
    // Spatial transition curves still expose all points and interpolation.
    await page.locator('#transitionKind').selectOption('wipe');
    state=await mutate(()=>page.locator('#applyFade').click());
    const spatial=page.getByRole('img',{name:'Aurora: Übergang Automationskurve'});
    assert.equal(await spatial.locator('circle').count(),3);
    await page.getByText('Übergang · wipe',{exact:true}).click();
    assert.equal(await page.locator('#pointForm').isVisible(),true);
    await mutate(()=>page.locator('#undo').click());
    assert.equal(await page.locator('#pointForm').isVisible(),false);
    assert.deepEqual((await current()).automation.transitions,before.automation.transitions);
    async function drag(kind,dx){
      const grip=page.getByRole('slider',{name:`Aurora: ${kind==='in'?'Einblendung':'Ausblendung'} ändern`});
      await grip.scrollIntoViewIfNeeded();
      const box=await grip.boundingBox(),x=box.x+box.width/2,y=box.y+box.height/2;
      return mutate(async()=>{await page.mouse.move(x,y);await page.mouse.down();
        await page.mouse.move(x+dx,y,{steps:8});await page.mouse.up();});
    }
    state=await drag('in',20);assert.equal(state.show.cues[0].fade_in,2);
    state=await drag('out',-20);assert.equal(state.show.cues[0].fade_out,5);
    assert.equal(state.show.cues[0].transition_duration,3);assert.equal(state.rows[1].start,9);
    assert.equal(state.show.cues[0].duration,12);
    await page.locator('#clipFadeInCurve').selectOption('ease_in');
    await page.locator('#clipFadeOutCurve').selectOption('smooth');
    state=await mutate(()=>page.locator('#applyClipFades').click());
    assert.equal(state.show.cues[0].fade_in_curve,'ease_in');
    assert.equal(state.show.cues[0].fade_out_curve,'smooth');
    await page.screenshot({path:path.join(evidence,'overlap-independent-fades-desktop.png')});
    // Requested overlap is separate from envelopes and actual clamped geometry.
    await page.locator('#fadeDuration').fill('12');
    state=await mutate(()=>page.locator('#applyFade').click());
    assert.equal(state.show.cues[0].transition_duration,12);
    assert.ok(state.rows[0].overlap_out<12);assert.equal(state.show.cues[0].fade_out,5);
    await mutate(()=>page.locator('#undo').click());
    // A pointer cancel never writes an envelope or history entry.
    const revision=(await current()).revision;
    const grip=page.getByRole('slider',{name:'Aurora: Einblendung ändern'});
    let box=await grip.boundingBox();
    await page.mouse.move(box.x+4,box.y+5);await page.mouse.down();
    await page.mouse.move(box.x+30,box.y+5);
    await page.evaluate(()=>window.dispatchEvent(new PointerEvent('pointercancel')));await page.mouse.up();
    assert.equal((await current()).revision,revision);
    // Keyboard handle movement and responsive layout use the same edit action.
    await page.setViewportSize({width:900,height:850});
    await page.locator('#zoom').fill('30');await page.locator('#zoom').dispatchEvent('input');
    await page.locator('#scroll').evaluate(el=>el.scrollLeft=25);
    state=await mutate(()=>page.getByRole('slider',{name:'Aurora: Einblendung ändern'}).press('ArrowRight'));
    assert.equal(state.show.cues[0].fade_in,2.1);
    await page.screenshot({path:path.join(evidence,'overlap-independent-fades-small.png')});
    await mutate(()=>page.locator('#save').click());
    await page.reload();await page.waitForFunction(()=>!!state);
    state=await current();assert.equal(state.show.cues[0].fade_in,2.1);
    assert.equal(state.show.cues[0].fade_out,5);
    assert.deepEqual(state.automation.tracks,before.automation.tracks);
    assert.deepEqual(errors,[]);
    console.log(JSON.stringify({passed:true,url,errors,evidence,
      cases:['explicit-migration-cancel-confirm','duration-only-crossfade','duration-handles','spatial-and-legacy-curves','actual-offsets','fade-in-drag','fade-out-drag','independent-curves',
        'clamped-overlap','undo','pointer-cancel','keyboard','responsive','save-reload']}));
  }finally{if(browser)await browser.close();host.kill();}
})().catch(error=>{console.error(error);process.exitCode=1;});
