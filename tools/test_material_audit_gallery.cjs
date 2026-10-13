/* Run with Node and playwright on NODE_PATH; screenshots stay beside the report. */
const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const assert = require('node:assert/strict');
(async () => {
  const report = path.resolve(process.argv[2] || 'docs/material-audit-20261013/results.json');
  const folder = path.dirname(report), data = JSON.parse(fs.readFileSync(report,'utf8'));
  const browser = await chromium.launch({headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000}});
    const errors = [];
    page.on('pageerror', e => errors.push(String(e)));
    page.on('console', m => {if(m.type()==='error') errors.push(m.text());});
    const url = pathToFileURL(path.join(folder,'galerie.html')).href;
    await page.goto(url);
    assert.equal(page.url(),url);
    assert.match(await page.title(),/Materialbibliothek/);
    assert.equal(await page.locator('article:visible').count(),data.results.length);
    assert.equal(await page.locator('img').evaluateAll(images=>images.filter(i=>!i.complete||!i.naturalWidth).length),0);
    await page.getByRole('searchbox').fill('Ripple Noise');
    assert.equal(await page.locator('article:visible').count(),data.results.filter(r=>r.name.toLowerCase().includes('ripple noise')).length);
    await page.screenshot({path:path.join(folder,'gallery-search.png')});
    await page.getByRole('searchbox').fill('');
    await page.getByLabel('Prüfstatus').selectOption('review');
    assert.equal(await page.locator('article:visible').count(),data.results.filter(r=>r.status==='review').length);
    await page.getByLabel('Prüfstatus').selectOption('');
    await page.screenshot({path:path.join(folder,'gallery-desktop.png')});
    await page.setViewportSize({width:390,height:844});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    await page.screenshot({path:path.join(folder,'gallery-mobile.png')});
    assert.deepEqual(errors,[]);
    const evidence = {passed:true,materials:data.results.length,viewports:['1440x1000','390x844'],
      checks:['page identity','content','all images loaded','name search','status filter','no horizontal overflow','no console errors'],
      browser:'Playwright Chromium; Browser plugin not available'};
    fs.writeFileSync(path.join(folder,'gallery-qa.json'),JSON.stringify(evidence,null,2));
    console.log(JSON.stringify(evidence));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
