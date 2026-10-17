// Complete real-client rendering of helper states plus a same-fixture render sample.
const fs=require('node:fs'),path=require('node:path'),{chromium}=require('playwright');
const out=path.join(__dirname,'../art/visual-quality-v3/review'),fixtures=JSON.parse(fs.readFileSync(path.join(out,'fixtures.json'))).states;
const base=process.env.GAUNTLET_QA_URL||'http://127.0.0.1:8016';
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.GAUNTLET_ART_BROWSER_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe'}),page=await browser.newPage({viewport:{width:1366,height:768}}),errors=[];
 page.on('pageerror',e=>errors.push(e.stack));page.on('response',r=>{if(r.status()>=400)errors.push(r.status()+' '+r.url());});
 try{
  await page.goto(base);await page.waitForTimeout(600);await page.addStyleTag({content:'@media(min-width:901px){body.is-playing .arena-controls{display:none!important}}'});
  await page.evaluate(()=>{document.querySelector('#entry').classList.add('hidden');document.querySelector('#lobby').classList.remove('hidden');});
  for(const name of Object.keys(fixtures)){
   await page.evaluate(r=>{document.querySelectorAll('dialog[open]').forEach(d=>d.close());renderRoom(r);},fixtures[name]);await page.waitForTimeout(900);
   if(name==='shop')await page.evaluate(()=>document.querySelector('#townPanel').classList.remove('hidden'));
   await page.evaluate(r=>{GauntletCombatVisuals.reset();GauntletAbilityAnimations.observe({...r,players:[],effects:[]});renderRoom(r);},fixtures[name]);
   await page.screenshot({path:path.join(out,'scene-'+name+'.png')});
  }
  await page.evaluate(r=>renderRoom(r),fixtures.dunmere);await page.locator('#heroSkillsButton').click();await page.getByRole('button',{name:'Ascension',exact:true}).click();await page.screenshot({path:path.join(out,'ascension-desktop.png')});await page.locator('[data-close="heroSkillsDialog"]').click();
  await page.locator('#togglePouch').click();await page.screenshot({path:path.join(out,'inventory-desktop.png')});await page.locator('#togglePouch').click();
  await page.evaluate(()=>document.querySelector('#audioDialog').showModal());await page.screenshot({path:path.join(out,'settings-desktop.png')});await page.evaluate(()=>document.querySelector('#audioDialog').close());
  await page.evaluate(r=>renderRoom(r),fixtures.cellar);await page.locator('#adventureMapButton').click();await page.screenshot({path:path.join(out,'cellar-map-desktop.png')});await page.setViewportSize({width:844,height:390});await page.screenshot({path:path.join(out,'cellar-map-landscape.png')});await page.locator('[data-close="adventureMapDialog"]').click();
  for(const name of ['shop','object-inspection','signatures-release','zones']){await page.evaluate(r=>{document.querySelectorAll('dialog[open]').forEach(d=>d.close());renderRoom(r);},fixtures[name]);await page.waitForTimeout(300);if(name==='shop')await page.evaluate(()=>document.querySelector('#townPanel').classList.remove('hidden'));await page.screenshot({path:path.join(out,'scene-'+name+'-landscape.png')});}
  await page.setViewportSize({width:1366,height:768});
  const perf=await page.evaluate(async r=>{
   document.querySelectorAll('dialog[open]').forEach(d=>d.close());r.effects=[];for(const p of r.players){p.abilityAnimation=null;p.moving=false;}renderRoom(r);
   for(const p of r.players)importedSprite(p.class);await new Promise(resolve=>setTimeout(resolve,500));
   const api=GauntletAscendedSprites,fx=GauntletCombatVisuals,rows=[];
   for(let round=0;round<4;round++)for(const enabled of round%2?[true,false]:[false,true]){
    window.GauntletAscendedSprites=enabled?api:null;window.GauntletCombatVisuals=enabled?fx:null;for(let i=0;i<20;i++)drawWorld(r);const values=[];
    for(let i=0;i<120;i++){const start=performance.now();drawWorld(r);values.push(performance.now()-start);}values.sort((a,b)=>a-b);rows.push({round,enabled,mean:values.reduce((a,b)=>a+b)/values.length,p50:values[60],p95:values[114],max:values.at(-1)});
   }window.GauntletAscendedSprites=api;window.GauntletCombatVisuals=fx;
   const resources=performance.getEntriesByType('resource').filter(r=>new URL(r.name).origin===location.origin&&new URL(r.name).pathname.startsWith('/sprites/')).map(r=>({path:new URL(r.name).pathname,bytes:r.encodedBodySize}));
   return{label:'Same four-hero mill fixture, 4 alternating paired rounds, 20 warmup +120 synchronous drawWorld calls each. Enabled forms versus existing base-art fallback in this build, not a historical FPS benchmark. Excludes network and frame scheduling.',rows,resources,jsHeap:performance.memory?{used:performance.memory.usedJSHeapSize,total:performance.memory.totalJSHeapSize}:null};
  },fixtures['signatures-release']);
  fs.writeFileSync(path.join(out,'scene-review.json'),JSON.stringify({scope:'Helper-prepared real server states rendered by the actual client. Not earned progression, ordinary combat or human multiplayer evidence.',errors,performance:perf},null,2));console.log(JSON.stringify({errors,renderRounds:perf.rows}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
